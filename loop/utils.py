import datetime
import pytz
from django import utils as django_utils


OUTPUT_DATE_TIME_FORMAT = "%H:%M:%S"
default_timezone = "America/Chicago"


def convert_timezone(
        time_str,
        time_zone=default_timezone,
        input_time_format=OUTPUT_DATE_TIME_FORMAT
):
    """
    Convert in desired date time format
    """
    time = datetime.datetime.strptime(time_str, input_time_format)
    dt_object = timezone_aware(time, time_zone)
    return dt_object


def change_timezone(dt_object, desired_timezone=default_timezone):
    """
    Convert date time object from one timezone to another
    """
    expected_timezone_time = dt_object.astimezone(
        pytz.timezone(desired_timezone)
    )
    return expected_timezone_time

def timezone_aware(time, time_zone):
    dt_object = django_utils.timezone.make_aware(
        time,
        timezone=pytz.timezone(time_zone)
    )
    return dt_object

