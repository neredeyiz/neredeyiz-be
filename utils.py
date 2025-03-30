import datetime

from constants import turkey_tz


def _is_within_two_hours_from_now(gathering_time):
    current_datetime = datetime.datetime.now(tz=turkey_tz)
    gathering_time = turkey_tz.localize(gathering_time)
    time_difference = gathering_time - current_datetime
    return time_difference.total_seconds() <= 2 * 60 * 60