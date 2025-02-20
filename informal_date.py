'''Parse informal date strings into datetime objects'''
from datetime import datetime, timedelta
import re

import text2int

def parse(date_str):
    '''Parse the given date string into a datetime object'''
    today = datetime.now()
    date_str = date_str.lower().strip()

    # Handle: HH:MM and assume today's date
    try:
        tm = datetime.strptime(date_str, '%H:%M')
        return datetime.combine(today.date(), tm.time())
    except ValueError:
        pass

    # Handle today, yesterday, tomorrow, last day
    if date_str == 'today':
        return today.replace(hour=0, minute=0, second=0, microsecond=0)
    if date_str in ['yesterday', 'last day']:
        return (today - timedelta(days=1)).replace(hour=0, minute=0,
                                                   second=0, microsecond=0)
    if date_str == 'tomorrow':
        return (today + timedelta(days=1)).replace(hour=0, minute=0,
                                                   second=0, microsecond=0)

    # Handle:
    #   <n> days
    #   <n> days ago
    #   last <n> days
    match = re.match(r'(last\s+)?(\d+)\s+days?(\s+ago)?', date_str)
    if match:
        days_ago = int(match.group(2))
        return (today - timedelta(days=days_ago)).replace(hour=0, minute=0,
                                                          second=0, microsecond=0)

    # Handle:
    #   one day, two days...nine days
    #   one day ago, two days ago...nine days ago
    #   last one day, last two days...last nine days
    match = re.match(r'(last\s+)?(\w+)\s+days?(\s+ago)?', date_str)
    if not match:
        # As above but with two words for the days like "thirty seven days ago"
        match = re.match(r'(last\s+)?(\w+\s+\w+)\s+days?(\s+ago)?', date_str)
    if match:
        days = text2int.parse(match.group(2))
        return (today - timedelta(days=days)).replace(hour=0, minute=0,
                                                      second=0, microsecond=0)

    # Handle:
    #   <n> hours
    #   <n> hours ago
    #   last <n> hours
    match = re.match(r'(last\s+)?(\d+)\s+hours?(\s+ago)?', date_str)
    if match:
        hours_ago = int(match.group(2))
        return (today - timedelta(hours=hours_ago)).replace(second=0, microsecond=0)

    # Handle "last hour"
    if date_str == "last hour":
        return (today - timedelta(hours=1)).replace(second=0, microsecond=0)

    # Handle times like:
    #   two hours, five hours...nine hours
    #   last two hours, last five hours...last nine hours
    #   two hours ago, five hours ago...nine hours ago
    match = re.match(r'(last\s+)?(\w+)\s+hours?(\s+ago)?', date_str)
    if not match:
        # As above but with two words for hours like "fourty one hours ago"
        match = re.match(r'(last\s+)?(\w+\s+\w+)\s+hours?(\s+ago)?', date_str)
    if match:
        hours_ago = text2int.parse(match.group(2))
        return (today - timedelta(hours=hours_ago)).replace(second=0, microsecond=0)

    # Handle:
    #   <n> minutes
    #   last <n> minutes
    #   <n> minutes ago
    match = re.match(r'(last\s+)?(\d+)\s+minutes?(\s+ago)?', date_str)
    if match:
        minutes_ago = int(match.group(2))
        return (today - timedelta(minutes=minutes_ago)).replace(second=0,
                                                                microsecond=0)

    # Handle "last minute"
    if date_str == "last minute":
        return (today - timedelta(minutes=1)).replace(second=0, microsecond=0)

    # Handle:
    #   one minute, two minutes...nine minutes
    #   last one minute, last two minutes, last nine minutes
    #   one minute ago, two minutes ago...nine minutes ago
    match = re.match(r'(last\s+)?(\w+)\s+minutes?(\s+ago)?', date_str)
    if not match:
        # As above but with two words for the minutes like "fifty seven minutes ago"
        match = re.match(r'(last\s+)?(\w+\s+\w+)\s+minutes?', date_str)
    if match:
        minutes_ago = text2int.parse(match.group(2))
        return (today - timedelta(minutes=minutes_ago)).replace(second=0,
                                                                microsecond=0)

    raise ValueError("Unsupported informal date format")


def test():
    '''Test parse()'''
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

    # Convert informal dates to datetime objects
    for informal_date in informal_dates:
        try:
            parse(informal_date)
        except ValueError as e:
            print(e)

    date_today = parse("today")
    date_yesterday = parse("yesterday")
    date_tomorrow = parse("tomorrow")

    # Comparison tests
    if date_today <= date_yesterday:
        raise ValueError(
                f"FAIL: today {date_today} is <= yesterday {date_yesterday}")
    if date_tomorrow <= date_yesterday:
        raise ValueError(
                f"FAIL: tomorrow {date_tomorrow} is <= yesterday {date_yesterday}")
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

if __name__ == '__main__':
    try:
        test()
    except ValueError as ex:
        print(ex)
