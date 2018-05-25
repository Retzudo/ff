import flask
import requests
from datetime import datetime
from flask import Flask, render_template
from bs4 import BeautifulSoup
from typing import List

app = Flask(__name__)

URL = 'http://www.ff-ried.at/site/?cID=86&mID=33'
TIME_FORMAT = '%d.%m. %H:%M'


class Brigade:
    def __init__(self, location: str, start: datetime, end: datetime=None):
        self.location = location
        self.start = start
        self.end = end

    @classmethod
    def from_row(cls, row):
        tds = row.find_all('td')
        dates = tds[1]
        location = tds[2].string
        start, end = dates.string.split('-', maxsplit=2)

        start = start.strip()
        end = end.strip()
        now = datetime.now()

        if start:
            start = datetime.strptime(start, TIME_FORMAT)
            start = start.replace(year=now.year)

        if end:
            end = datetime.strptime(end, TIME_FORMAT)
            end = end.replace(year=now.year)

        return cls(
            location=location,
            start=start,
            end=end,
        )


class Event:
    def __init__(self, title: str, type: str, brigades: List[Brigade]=None):
        self.title = title
        self.type = type
        self.brigades = brigades or []

    @staticmethod
    def get_event_type(string):
        if 'bullet_red' in string:
            return 'fire'
        if 'bullet_blue' in string:
            return 'technical'
        if 'bullet_yellow' in string:
            return 'persons'
        if 'bullet_green' in string:
            return 'environmental'

        return 'unknown'

    @classmethod
    def from_row(cls, row):
        title = row.find('b').string.strip()
        type = cls.get_event_type(row.find('img')['src'])

        return cls(title=title, type=type)


def parse_content(html: str) -> List[Event]:
    print('asdf', 'Überflutung' in html)
    soup = BeautifulSoup(html, 'html.parser')
    events = []

    table = soup.find(id='BWSTEinsatz').find('table')
    rows = table.find_all('tr')

    for row in rows:
        if len(row.find_all('td')) == 2:  # Event row
            event = Event.from_row(row)
            events.append(event)
        else:
            events[-1].brigades.append(
                Brigade.from_row(row)
            )

    return events


@app.route('/')
def index():
    response = requests.get(URL)

    if response.status_code == 200:
        response.encoding = 'utf-8'
        flask.g.last_response = response.text

    if not flask.g.get('last_response'):
        events = []
    else:
        events = parse_content(flask.g.get('last_response'))

    return render_template('index.html', events=events)
