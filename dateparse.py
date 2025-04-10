#!/usr/bin/env python3

'''Parse informal date strings into datetime objects'''
from datetime import datetime, timedelta
import re

import tzlocal
import dateutil

import text2int

LOCAL_TIMEZONE = tzlocal.get_localzone()


def parse(date_limit_str):
    '''Parse the given date string into a datetime object'''
    try:
        parsed_date = _parse(date_limit_str).replace(tzinfo=LOCAL_TIMEZONE)
        dt = parsed_date
    except ValueError:
        dt = dateutil.parser.parse(date_limit_str)

    if not dt:
        print(f"Error parsing date: {date_limit_str}")
        return None

    return dt.replace(tzinfo=LOCAL_TIMEZONE)


def _parse(date_str):
    '''Parse the given date string into a datetime object'''
    today = datetime.now()
    date_str = date_str.lower().strip()

    parse_fns = [_parse_today_yesterday_tomorrow,
                 _parse_weeks,
                 _parse_days,
                 _parse_hours,
                 _parse_minutes]

    for fn in parse_fns:
        try:
            return fn(today, date_str)
        except ValueError:
            pass

    raise ValueError("Unsupported informal date format")


def _parse_today_yesterday_tomorrow(today, date_str):
    '''parse the given date string: handle today, yesterday, tomorrow'''
    if date_str == 'today':
        dt = today
    elif date_str == 'yesterday':
        dt = today - timedelta(days=1)
    elif date_str == 'tomorrow':
        dt = today + timedelta(days=1)
    else:
        dt = None

    if dt:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    raise ValueError()


def _parse_weeks(today, date_str):
    '''parse the given date string for weeks'''
    # Handle "last week"
    if date_str == "last week":
        date_str = 'last 1 week'

    # <n> weeks, <n> weeks ago, last <n> weeks
    match = re.match(r'(last\s+)?(\d+)\s+weeks?(\s+ago)?', date_str)

    # one week, two weeks...nine weeks
    # one week ago, two weeks ago...nine weeks ago
    # last one week, last two weeks...last nine weeks
    if not match:
        match = re.match(r'(last\s+)?(\w+)\s+weeks?(\s+ago)?', date_str)

    # As above but with two words for the weeks like "thirty seven weeks ago"
    if not match:
        match = re.match(r'(last\s+)?(\w+\s+\w+)\s+weeks?(\s+ago)?', date_str)

    if match:
        weeks = text2int.parse(match.group(2))
        return (today - timedelta(weeks=weeks)).replace(hour=0, minute=0,
                                                        second=0, microsecond=0)

    raise ValueError()


def _parse_days(today, date_str):
    '''parse the given date string for days'''
    # Handle "last day"
    if date_str == "last day":
        date_str = 'last 1 day'

    # <n> days, <n> days ago, last <n> days
    match = re.match(r'(last\s+)?(\d+)\s+days?(\s+ago)?', date_str)

    # one day, two days...nine days
    # one day ago, two days ago...nine days ago
    # last one day, last two days...last nine days
    if not match:
        match = re.match(r'(last\s+)?(\w+)\s+days?(\s+ago)?', date_str)

    # As above but with two words for the days like "thirty seven days ago"
    if not match:
        match = re.match(r'(last\s+)?(\w+\s+\w+)\s+days?(\s+ago)?', date_str)

    if match:
        days = text2int.parse(match.group(2))
        return (today - timedelta(days=days)).replace(hour=0, minute=0,
                                                      second=0, microsecond=0)

    raise ValueError()


def _parse_hours(today, date_str):
    '''parse the given date string for hours'''
    # Handle "last hour"
    if date_str == "last hour":
        date_str = 'last 1 hour'

    # <n> hours, <n> hours ago, last <n> hours
    match = re.match(r'(last\s+)?(\d+)\s+hours?(\s+ago)?', date_str)

    # two hours, five hours...nine hours
    # last two hours, last five hours...last nine hours
    # two hours ago, five hours ago...nine hours ago
    if not match:
        match = re.match(r'(last\s+)?(\w+)\s+hours?(\s+ago)?', date_str)

    # As above but with two words for hours like "forty one hours ago"
    if not match:
        match = re.match(r'(last\s+)?(\w+\s+\w+)\s+hours?(\s+ago)?', date_str)

    if match:
        hours = text2int.parse(match.group(2))
        return (today - timedelta(hours=hours)).replace(second=0, microsecond=0)

    raise ValueError()


def _parse_minutes(today, date_str):
    '''parse the given date string for minutes'''
    # Handle last minute/last min
    if date_str in ["last minute", "last min"]:
        date_str = 'last 1 minute'

    # <n> minutes
    # last <n> minutes
    # <n> minutes ago
    match = re.match(r'(last\s+)?(\d+)\s+min(ute)?s?(\s+ago)?', date_str)

    # one minute, two minutes...nine minutes
    # last one minute, last two minutes, last nine minutes
    # one minute ago, two minutes ago...nine minutes ago
    match = re.match(r'(last\s+)?(\w+)\s+min(ute)?s?(\s+ago)?', date_str)

    # As above but with two words for the minutes like "fifty seven minutes ago"
    if not match:
        match = re.match(r'(last\s+)?(\w+\s+\w+)\s+min(ute)?s?', date_str)

    if match:
        minutes_ago = text2int.parse(match.group(2))
        return (today - timedelta(minutes=minutes_ago)).replace(second=0,
                                                                microsecond=0)

    raise ValueError("Unsupported informal date format")


def humanise_date_string(date_string):
    '''Convert the given BlueSky date string into something more readable
        for human consumption'''
    try:
        return dateutil.parser.isoparse(date_string).strftime(
                '%B %d, %Y at %I:%M %p UTC')
    except ValueError:
        # Failed to parse string, return it as a simple string
        return str(date_string)
