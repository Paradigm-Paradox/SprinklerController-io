import math
import logging
from datetime import datetime, date

logger = logging.getLogger("gardencontrol.et")

class ETCalculator:
    """Calculates reference evapotranspiration (ET0) using the Hargreaves-Samani method.
    
    Formula:
    ET0 = 0.0023 * (Tmean + 17.8) * (Tmax - Tmin)^0.5 * Ra
    Where Ra is extraterrestrial radiation (mm/day equivalent).
    """

    @staticmethod
    def calculate_extraterrestrial_radiation(latitude_deg: float, day_of_year: int) -> float:
        """Compute extraterrestrial radiation Ra in mm/day equivalent for a given latitude and day."""
        phi = math.radians(latitude_deg)
        dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)
        delta = 0.409 * math.sin((2.0 * math.pi * day_of_year / 365.0) - 1.39)
        
        # Sunset hour angle
        tan_term = -math.tan(phi) * math.tan(delta)
        # Clamp to [-1, 1]
        tan_term = max(-1.0, min(1.0, tan_term))
        omega_s = math.acos(tan_term)
        
        # Solar constant Gsc = 0.0820 MJ / m^2 / min
        # Radiation in MJ / m^2 / day:
        ra_mj = (24.0 * 60.0 / math.pi) * 0.0820 * dr * (
            omega_s * math.sin(phi) * math.sin(delta) +
            math.cos(phi) * math.cos(delta) * math.sin(omega_s)
        )
        
        # Convert MJ/m^2/day to equivalent water evaporation in mm/day (divide by 2.45)
        ra_mm = ra_mj / 2.45
        return max(0.1, ra_mm)

    @classmethod
    def calculate_daily_et0(
        cls,
        t_min_c: float,
        t_max_c: float,
        latitude_deg: float = 18.2, # Default approx for Puerto Rico
        current_date: Optional[date] = None
    ) -> float:
        """Calculate daily ET0 in mm."""
        if current_date is None:
            current_date = date.today()
        doy = current_date.timetuple().tm_yday
        ra = cls.calculate_extraterrestrial_radiation(latitude_deg, doy)
        
        t_mean = (t_max_c + t_min_c) / 2.0
        delta_t = max(0.5, t_max_c - t_min_c)
        
        et0 = 0.0023 * (t_mean + 17.8) * math.sqrt(delta_t) * ra
        return round(max(0.2, et0), 2)

    @classmethod
    def calculate_crop_water_deficit(
        cls,
        et0_mm: float,
        crop_kc: float,
        rainfall_mm: float = 0.0,
        efficiency: float = 0.85
    ) -> float:
        """Calculate net depth of water needed by the crop (mm)."""
        # Effective rainfall (approx 80% if under 25mm, less if torrential)
        eff_rain = min(rainfall_mm * 0.8, rainfall_mm)
        crop_need = (et0_mm * crop_kc) - eff_rain
        if crop_need <= 0.0:
            return 0.0
        return round(crop_need / efficiency, 2)
