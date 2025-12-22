import datetime
from datetime import date


def get_current_week() -> str:
    current_week = datetime.datetime.now().isocalendar()[1]
    today_number = date.today().weekday() + 1
    week_id = str(today_number) + '_week_' + str(current_week)
    return week_id
