from datetime import datetime
from src import database

## Clock in


def test_clock_in():
    database.clock_in()
    date_time = datetime(2022, 1, 1, 9, 0, 0)
    database.clock_in(date_time)
