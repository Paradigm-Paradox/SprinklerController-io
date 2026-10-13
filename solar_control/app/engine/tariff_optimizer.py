import logging
from .models import TariffState, PowerFlowState
from ..config import AppConfig
from ..ha_client import HAClient

logger = logging.getLogger("SolarControl.TariffOptimizer")

class TariffOptimizer:
    def __init__(self, config: AppConfig, ha_client: HAClient):
        self.config = config
        self.ha = ha_client

    async def evaluate(self, pf: PowerFlowState) -> TariffState:
        tariff_state = TariffState(enabled=self.config.tariff.dynamic_pricing_enabled)
        if not self.config.tariff.dynamic_pricing_enabled:
            return tariff_state

        if self.config.tariff.price_sensor:
            tariff_state.import_price = await self.ha.get_numeric_state(self.config.tariff.price_sensor)

        if self.config.tariff.export_price_sensor:
            tariff_state.export_price = await self.ha.get_numeric_state(self.config.tariff.export_price_sensor)

        # Detect negative feed-in price
        if tariff_state.export_price < 0.0:
            tariff_state.is_negative_export = True
            if self.config.tariff.negative_price_curtailment and pf.grid_w < -100.0:
                logger.warning(
                    f"Negative feed-in tariff detected ({tariff_state.export_price}). Curtailment recommended to prevent export charges."
                )

        return tariff_state
