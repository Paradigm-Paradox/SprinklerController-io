class LightingEngine:
    def __init__(self, zone_name: str, target_dli_mol: float = 16.0):
        self.zone_name = zone_name
        self.target_dli_mol = target_dli_mol
        self.accumulated_dli = 0.0

    def accumulate_ppfd(self, ppfd_umol: float, duration_seconds: float) -> float:
        """
        DLI accumulation formula:
        mol / m² / day = (PPFD umol/m²/s * seconds) / 1,000,000
        """
        increment = (ppfd_umol * duration_seconds) / 1_000_000.0
        self.accumulated_dli += increment
        return round(self.accumulated_dli, 2)

    def reset_daily_dli(self):
        self.accumulated_dli = 0.0
