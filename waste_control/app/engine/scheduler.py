import datetime
from typing import Dict, Any, Optional
from ..config import StreamConfig

DAYS_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}

# Standard fixed US holidays
US_FIXED_HOLIDAYS = [
    (1, 1),   # New Year's Day
    (7, 4),   # Independence Day
    (11, 11), # Veterans Day
    (12, 25)  # Christmas
]

def is_holiday(date: datetime.date) -> bool:
    """Check if date is an observed holiday that causes a municipal delay."""
    if (date.month, date.day) in US_FIXED_HOLIDAYS:
        return True
    
    # Thanksgiving: 4th Thursday in November
    if date.month == 11 and date.weekday() == 3:
        if 22 <= date.day <= 28:
            return True
            
    # Memorial Day: Last Monday in May
    if date.month == 5 and date.weekday() == 0:
        if date.day >= 25:
            return True

    # Labor Day: 1st Monday in September
    if date.month == 9 and date.weekday() == 0:
        if date.day <= 7:
            return True

    return False

def calculate_next_pickup(stream: StreamConfig, from_date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """Calculate the next collection date and remaining days for a stream."""
    if from_date is None:
        from_date = datetime.date.today()

    target_weekday = DAYS_MAP.get(stream.pickup_day.lower(), 1)
    
    # Check within the next 45 days
    for offset in range(0, 46):
        candidate = from_date + datetime.timedelta(days=offset)
        
        # Must match designated weekday
        if candidate.weekday() != target_weekday:
            continue

        # Evaluate cadence
        week_num = candidate.isocalendar()[1]
        if stream.schedule_type == "biweekly_even" and (week_num % 2 != 0):
            continue
        if stream.schedule_type == "biweekly_odd" and (week_num % 2 == 0):
            continue
        if stream.schedule_type == "monthly" and candidate.day > 7:
            continue

        # Apply holiday delay if applicable
        pickup_date = candidate
        if stream.holiday_delay:
            week_start = candidate - datetime.timedelta(days=candidate.weekday())
            cur = week_start
            holiday_shifted = False
            while cur <= candidate:
                if is_holiday(cur):
                    holiday_shifted = True
                    break
                cur += datetime.timedelta(days=1)
            
            if holiday_shifted:
                pickup_date = candidate + datetime.timedelta(days=1)

        days_remaining = (pickup_date - from_date).days
        if days_remaining < 0:
            continue

        return {
            "stream_id": stream.id,
            "stream_name": stream.name,
            "next_date": pickup_date.isoformat(),
            "days_remaining": days_remaining,
            "is_today": days_remaining == 0,
            "is_tomorrow": days_remaining == 1,
            "color": stream.color
        }

    return {
        "stream_id": stream.id,
        "stream_name": stream.name,
        "next_date": None,
        "days_remaining": -1,
        "is_today": False,
        "is_tomorrow": False,
        "color": stream.color
    }
