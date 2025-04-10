'''BlueSky tests'''


import datetime
from unittest.mock import patch
import pytest

import dateparse

test_isodates = [
    "2023-01-01",                   # Basic date
    "2023-12-31",                   # Basic date
    "2020-02-29",                   # Leap year date
    "2023-01-01T12:00:00",          # Date with time
    "2023-12-31T23:59:59",          # Date with time
    "2023-01-01T12:00:00+00:00",    # Date with timezone
    "2023-01-01T12:00:00-05:00",    # Date with timezone
    "2023-01-01T12:00:00Z",         # Date with UTC
    "2023-01-01T12:00:00.123456",   # Date with fractional seconds
    "2023-01-01T12:00:00+02:00",    # Date with timezone in hours and minutes
]

'''
"2023-W01-1",               # Week date
"2023-W52-7",               # Week date
"2023-001",                 # Ordinal date
"2023-365"                  # Ordinal date
'''

informal_dates = [
    "today",
    "yesterday",
    "tomorrow",

    "last day",
    "1 day",
    "2 days",
    "9 day",
    "48 days",

    "last 1 day",
    "last 2 days",
    "last 9 day",
    "last 48 days",

    "1 day ago",
    "2 days ago",
    "9 day ago",
    "88 days ago",

    "one day",
    "two day",
    "nine day",
    "fifty three days",

    "last one day",
    "last two day",
    "last nine day",
    "last fifty eight days",

    "one day ago",
    "two day ago",
    "nine day ago",
    "seventy six days ago",

    "last hour",
    "1 hour",
    "2 hours",
    "9 hour",
    "48 hours",

    "last 1 hour",
    "last 2 hours",
    "last 9 hour",
    "last 48 hours",

    "1 hour ago",
    "2 hours ago",
    "9 hour ago",
    "88 hours ago",

    "one hour",
    "two hour",
    "nine hour",
    "fifty three hours",

    "last one hour",
    "last two hour",
    "last nine hour",
    "last fifty eight hours",

    "one hour ago",
    "two hour ago",
    "nine hour ago",
    "seventy six hours ago",

    "last minute",
    "1 minute",
    "2 minutes",
    "9 minute",
    "48 minutes",

    "last 1 minute",
    "last 2 minutes",
    "last 9 minute",
    "last 48 minutes",

    "1 minute ago",
    "2 minutes ago",
    "9 minute ago",
    "88 minutes ago",

    "one minute",
    "two minute",
    "nine minute",
    "fifty three minutes",

    "last one minute",
    "last two minute",
    "last nine minute",
    "last fifty eight minutes",

    "one minute ago",
    "two minute ago",
    "nine minute ago",
    "seventy six minutes ago",
]

words_numbers = [('one day', '1 day'),
                 ('two days', '2 days'),
                 ('three days', '3 days'),
                 ('four days', '4 days'),
                 ('five days', '5 days'),
                 ('six days', '6 days'),
                 ('seven days', '7 days'),
                 ('eight days', '8 days'),
                 ('nine days', '9 days'),
                 ('ten days', '10 days'),
                 ('fifteen days', '15 days'),
                 ('twenty one days', '21 days'),
                 ('thirty seven days', '37 days'),
                 ('forty two days', '42 days'),
                 ('fifty days', '50 days'),
                 ('sixty three days', '63 days'),
                 ('seventy seven days', '77 days'),
                 ('eighty nine days', '89 days'),
                 ('ninety five days', '95 days')]


class TestDateParse:
    '''Test BlueSky rich() method'''
    @pytest.mark.parametrize('testdate', test_isodates)
    def test_parse_isodate(self, testdate):
        '''Test the parse() method with various ISO formatted dates.'''
        assert dateparse.parse(testdate)

    @pytest.mark.parametrize('testdate', informal_dates)
    def test_informal_dates(self, testdate):
        '''Test parse() method with various informal dates'''
        # Convert informal dates to datetime objects
        assert dateparse.parse(testdate)

    def test_today_yesterday_comparisons(self):
        date_today = dateparse.parse("today")
        date_yesterday = dateparse.parse("yesterday")

        assert date_today > date_yesterday
        assert date_yesterday < date_today

    def test_today_tomorrow_comparisons(self):
        date_today = dateparse.parse("today")
        date_tomorrow = dateparse.parse("tomorrow")

        assert date_today < date_tomorrow
        assert date_tomorrow > date_today

    def test_yesterday_tomorrow_comparisons(self):
        date_yesterday = dateparse.parse("yesterday")
        date_tomorrow = dateparse.parse("tomorrow")

        assert date_tomorrow > date_yesterday
        assert date_yesterday < date_tomorrow

    @pytest.mark.parametrize('word_number', words_numbers)
    def test_word_number_parsing(self, word_number):
        word, number = word_number
        date_word = dateparse.parse(word)
        date_number = dateparse.parse(number)
        assert date_word == date_number

    def test_minutes_comparisons(self):
        one_minute = dateparse.parse("one minute ago")
        five_minutes = dateparse.parse("five minute ago")
        thirty_minutes = dateparse.parse("30 mins ago")

        assert one_minute > five_minutes
        assert five_minutes > thirty_minutes

    def test_minute_now_comparisons(self):
        one_minute = dateparse.parse("one minute ago")
        five_minutes = dateparse.parse("five minute ago")
        thirty_minutes = dateparse.parse("30 mins ago")
        now = datetime.datetime.now(datetime.timezone.utc)

        assert one_minute < now
        assert five_minutes < now
        assert thirty_minutes < now

    def test_hour_comparisons(self):
        one_hour = dateparse.parse("one hour ago")
        eight_hours = dateparse.parse("eight hours ago")
        thirty_six_hours = dateparse.parse("thirty six hours ago")
        one_hundred_and_twenty_hours = dateparse.parse("120 hours ago")
        now = datetime.datetime.now(datetime.timezone.utc)

        assert one_hour > eight_hours
        assert one_hour > thirty_six_hours
        assert one_hour > one_hundred_and_twenty_hours

        assert eight_hours > thirty_six_hours
        assert eight_hours > one_hundred_and_twenty_hours

        assert one_hundred_and_twenty_hours < thirty_six_hours
        assert one_hundred_and_twenty_hours < eight_hours
        assert one_hundred_and_twenty_hours < one_hour

    def test_day_comparisons(self):
        one_day = dateparse.parse("1 day")
        two_days = dateparse.parse("two days")
        five_days = dateparse.parse("5 days")
        seven_days = dateparse.parse("seven days")
        forty_five_days = dateparse.parse("forty five days")

        assert one_day > two_days
        assert one_day > five_days
        assert one_day > seven_days
        assert one_day > forty_five_days

        assert two_days < one_day
        assert two_days > five_days
        assert two_days > seven_days
        assert two_days > forty_five_days

        assert five_days < one_day
        assert five_days < two_days
        assert five_days > seven_days
        assert five_days > forty_five_days

        assert seven_days < one_day
        assert seven_days < two_days
        assert seven_days < five_days
        assert seven_days > forty_five_days

        assert forty_five_days < one_day
        assert forty_five_days < two_days
        assert forty_five_days < five_days
        assert forty_five_days < seven_days

    def test_week_comparisons(self):
        one_week = dateparse.parse("1 week")
        two_weeks = dateparse.parse("two weeks")
        ten_weeks = dateparse.parse("10 weeks")
        fifty_weeks = dateparse.parse("fifty weeks")

        assert one_week > two_weeks
        assert one_week > ten_weeks
        assert one_week > fifty_weeks

        assert two_weeks < one_week
        assert two_weeks > ten_weeks
        assert two_weeks > fifty_weeks

        assert fifty_weeks < one_week
        assert fifty_weeks < two_weeks
        assert fifty_weeks < ten_weeks

        '''
        if date_tomorrow <= date_today:
            raise ValueError(
                    f"FAIL: tomorrow {date_tomorrow} is <= today {date_today}")

        date_last_day = parse('last day')
        if date_last_day >= date_today:
            raise ValueError(
                    f"FAIL: Last day {date_last_day} >= today {date_today}")

        date_last_two_days = parse('last two days')
        if date_last_two_days >= date_today:
            raise ValueError(
                    f"FAIL: Last two days {date_last_two_days} >= today {date_today}")

        date_last_four_days = parse('last four days')
        date_ten_minutes_ago = parse('ten minutes ago')
        if date_last_four_days >= date_ten_minutes_ago:
            raise ValueError(f"FAIL: Last four days {date_last_four_days} >= "
                            f"ten minutes ago {date_ten_minutes_ago}")

        print('PASS')
        '''
