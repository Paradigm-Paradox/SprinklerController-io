import time
from typing import Dict, Any, Optional

class BinState:
    def __init__(
        self,
        stream_id: str,
        fill_level_percent: float = 0.0,
        distance_cm: Optional[float] = None,
        location: str = "storage",
        lid_open: bool = False,
        battery_percent: Optional[int] = 100,
        last_updated: Optional[float] = None
    ):
        self.stream_id = stream_id
        self.fill_level_percent = fill_level_percent
        self.distance_cm = distance_cm
        self.location = location  # storage, curb, transit
        self.lid_open = lid_open
        self.battery_percent = battery_percent
        self.last_updated = last_updated or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stream_id": self.stream_id,
            "fill_level_percent": self.fill_level_percent,
            "distance_cm": self.distance_cm,
            "location": self.location,
            "lid_open": self.lid_open,
            "battery_percent": self.battery_percent,
            "last_updated": self.last_updated
        }

class BinManager:
    def __init__(self):
        self.bins: Dict[str, BinState] = {}

    def get_bin(self, stream_id: str) -> BinState:
        if stream_id not in self.bins:
            self.bins[stream_id] = BinState(stream_id=stream_id)
        return self.bins[stream_id]

    def update_sensor_reading(
        self,
        stream_id: str,
        distance_cm: float,
        empty_depth_cm: float = 95.0,
        full_depth_cm: float = 15.0
    ) -> BinState:
        bin_state = self.get_bin(stream_id)
        bin_state.distance_cm = distance_cm
        
        usable_height = empty_depth_cm - full_depth_cm
        if usable_height <= 0:
            usable_height = 80.0
            
        clamped_dist = max(full_depth_cm, min(empty_depth_cm, distance_cm))
        fill_ratio = (empty_depth_cm - clamped_dist) / usable_height
        bin_state.fill_level_percent = round(fill_ratio * 100.0, 1)
        bin_state.last_updated = time.time()
        return bin_state

    def set_location(self, stream_id: str, location: str) -> BinState:
        bin_state = self.get_bin(stream_id)
        if location in ["storage", "curb", "transit"]:
            bin_state.location = location
            bin_state.last_updated = time.time()
        return bin_state

    def set_lid(self, stream_id: str, lid_open: bool) -> BinState:
        bin_state = self.get_bin(stream_id)
        bin_state.lid_open = lid_open
        bin_state.last_updated = time.time()
        return bin_state
