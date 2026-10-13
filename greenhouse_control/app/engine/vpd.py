import math
from typing import Dict

def saturation_vapor_pressure(temp_c: float) -> float:
    """
    Calculate saturation vapor pressure (VP_sat) in kPa using Tetens equation.
    Formula: 0.61078 * exp((17.27 * T) / (T + 237.3))
    """
    return 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))

def actual_vapor_pressure(temp_c: float, relative_humidity: float) -> float:
    """
    Calculate actual vapor pressure (VP_air) in kPa.
    Formula: VP_sat(temp_c) * (RH / 100)
    """
    vp_sat = saturation_vapor_pressure(temp_c)
    return vp_sat * (max(0.0, min(100.0, relative_humidity)) / 100.0)

def calculate_dew_point(temp_c: float, relative_humidity: float) -> float:
    """
    Calculate dew point temperature in Celsius via Magnus-Tetens formula.
    """
    rh = max(0.01, min(100.0, relative_humidity))
    a = 17.27
    b = 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(rh / 100.0)
    return (b * alpha) / (a - alpha)

def calculate_vpd(
    air_temp_c: float,
    relative_humidity: float,
    leaf_temp_c: float = None,
    leaf_offset_c: float = -2.0
) -> Dict[str, float]:
    """
    Compute comprehensive psychrometric & VPD metrics.
    
    Returns:
        air_vpd_kpa: VPD relative to air temperature
        leaf_vpd_kpa: VPD relative to plant canopy leaf temperature
        vp_sat_air_kpa: Air saturation vapor pressure
        vp_sat_leaf_kpa: Leaf saturation vapor pressure
        vp_air_kpa: Actual vapor pressure in air
        dew_point_c: Dew point temperature
        effective_leaf_temp_c: Effective leaf temperature used
    """
    if leaf_temp_c is None:
        effective_leaf_temp = air_temp_c + leaf_offset_c
    else:
        effective_leaf_temp = leaf_temp_c

    vp_sat_air = saturation_vapor_pressure(air_temp_c)
    vp_sat_leaf = saturation_vapor_pressure(effective_leaf_temp)
    vp_air = actual_vapor_pressure(air_temp_c, relative_humidity)

    air_vpd = max(0.0, vp_sat_air - vp_air)
    leaf_vpd = max(0.0, vp_sat_leaf - vp_air)
    dew_point = calculate_dew_point(air_temp_c, relative_humidity)

    return {
        "air_vpd_kpa": round(air_vpd, 3),
        "leaf_vpd_kpa": round(leaf_vpd, 3),
        "vp_sat_air_kpa": round(vp_sat_air, 3),
        "vp_sat_leaf_kpa": round(vp_sat_leaf, 3),
        "vp_air_kpa": round(vp_air, 3),
        "dew_point_c": round(dew_point, 2),
        "effective_leaf_temp_c": round(effective_leaf_temp, 2),
    }
