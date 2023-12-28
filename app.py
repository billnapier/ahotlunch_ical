"""Main app."""
import os
from datetime import datetime, timedelta
import pytz

import icalendar
from flask import Flask, Response

from ahotlunch import create_login_session, get_calendar

app = Flask(__name__)

ahotlunch_username = os.environ.get("ahotlunch_username")

if not ahotlunch_username:
    raise ValueError("No ahotlunch_username set for Flask application")

ahotlunch_password = os.environ.get("ahotlunch_password")

if not ahotlunch_password:
    raise ValueError("No ahotlunch_password set for Flask application")

session = create_login_session(
    instance="mygreenlunch",
    username=ahotlunch_username,
    password=ahotlunch_password,
)


def _create_calendar():
    cal = icalendar.Calendar()
    cal.add("prodid", "-//github.com/billnapier/ahotlunch_ical//")
    cal.add("version", "2.0")
    return cal


_DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@app.route("/")
def root():
    cal = _create_calendar()

    now = datetime.now()
    start_date = now - timedelta(weeks=26)
    end_date = now - timedelta(week=26)
    data = get_calendar(
        session, instance="mygreenlunch", start_date=start_date, end_date=end_date
    )
    for item in data.values():
        item = item[0]

        event = icalendar.Event()
        event['uid'] = item.get('id')

        created_date = datetime.strptime(item.get("createdDate"), _DATE_TIME_FORMAT)
        order_date = datetime.strptime(item.get("orderDate"), _DATE_TIME_FORMAT)
        start_date = datetime(
            year=order_date.year,
            month=order_date.month,
            day=order_date.day,
            hour=12,
            tzinfo=pytz.timezone("America/Los_Angeles"),
        )
        end_date = datetime(
            year=order_date.year,
            month=order_date.month,
            day=order_date.day,
            hour=13,
            tzinfo=pytz.timezone("America/Los_Angeles"),
        )

        event.add("summary", item.get("name"))
        event.add("dtstart", start_date)
        event.add("dtend", end_date)
        event.add("dtstamp", created_date)

        cal.add_component(event)
    return  Response(cal.to_ical(), mimetype='text/calendar')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
