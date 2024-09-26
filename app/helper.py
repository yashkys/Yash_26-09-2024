from typing import List
from datetime import time
from .models import BusinessHour
from datetime import datetime, timezone, timedelta
import pytz

# Constants (Python's strftime is used for date formatting)
DATE_FORMAT = "%Y-%m-%d"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DAY_END_TIME = "23:59:59"
DAY_START_TIME = "00:00:00"
MIDNIGHT = time(0, 0, 0)

def get_current_utc_date_time():
    # Get the current UTC time
    current_utc_time = datetime.utcnow()

    # Format the time as yyyy-MM-dd HH:mm:ss
    formatted_utc_time = current_utc_time.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_utc_time

def convert_to_time_array(business_hours_list: List[BusinessHour]) -> List[List[time]]:
    # Array to hold start and end time for each day of the week (7 days: 0 = Sunday, 6 = Saturday)
    hours_array = [[time(0, 0), time(23, 59, 59)] for _ in range(7)]

    # Populate the array based on the day of the week
    for bh in business_hours_list:
        day_of_week = bh.day_of_week  # Assuming 0 is Sunday, 6 is Saturday
        hours_array[day_of_week][0] = bh.start_time_local  # Start time
        hours_array[day_of_week][1] = bh.end_time_local    # End time

    return hours_array


def get_current_epoch_timestamp() -> int:
    unix_time = int(datetime.now(tz=timezone.utc).timestamp() * 1000)  # UTC timestamp in milliseconds
    return unix_time


# Function to get the current zonal time based on the timezone
def get_zonal_datetime(timezone: str) -> datetime:
    tz = pytz.timezone(timezone)
    zonal_datetime = datetime.now(tz)
    return zonal_datetime

# Function to convert a zonal datetime to UTC
def convert_zonal_datetime_to_utc(timezone: str, date: str, time: str) -> datetime:
    # Combine the date and time strings into a single datetime object
    local_datetime = datetime.strptime(f"{date}T{time}", "%Y-%m-%dT%H:%M:%S")
    
    # Create a timezone-aware datetime object
    tz = pytz.timezone(timezone)
    zoned_datetime = tz.localize(local_datetime)

    # Convert to UTC
    utc_datetime = zoned_datetime.astimezone(pytz.utc)

    return utc_datetime


# Function to get the last 7 dates in descending order
def get_last_7_dates(zoned_datetime: datetime) -> List[str]:
    dates_list = []
    today_date = zoned_datetime.date()  # Get just the date part

    # Add the last 7 days in descending order
    for i in range(1, 8):
        past_date = today_date - timedelta(days=i)
        dates_list.append(past_date.strftime(DATE_FORMAT))

    return dates_list


# Function to get the day of the week (0=Monday, 6=Sunday)
def get_day_of_week(date: datetime) -> int:
    # Python's weekday() returns 0=Monday, 6=Sunday
    return date.weekday()

# Function to convert a timestamp to a ZonedDateTime in a specific timezone
def convert_timestamp_to_zoneddatetime(timestamp: datetime, timezone: str) -> datetime:
    zone = pytz.timezone(timezone)
    return timestamp.astimezone(zone)

# Function to convert a timestamp to UTC ZonedDateTime
def convert_timestamp_to_utc(timestamp: datetime) -> datetime:
    return timestamp.astimezone(pytz.utc)
