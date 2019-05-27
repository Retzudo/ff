import flask
import requests
from datetime import datetime
from flask import Flask, render_template
from bs4 import BeautifulSoup
from typing import List

app = Flask(__name__)

URL = 'https://www.ff-ried.at/einsatzkarte-bezirk-ried/'
TIME_FORMAT = '%d.%m.%Y | %H:%M'


class Brigade:
    def __init__(self, location: str, start: datetime, end: datetime = None):
        self.location = location
        self.start = start
        self.end = end


class Event:
    def __init__(self, title: str, type: str, brigades: List[Brigade] = None):
        self.title = title
        self.type = type
        self.brigades = brigades or []


def get_event_type(image_url: str) -> str:
    if 'technisches' in image_url.lower():
        return 'technical'

    if 'brand' in image_url.lower():
        return 'fire'

    if 'personenrettung' in image_url.lower():
        return 'persons'

    if 'umwelt' in image_url.lower():
        return 'environmental'

    return 'unknown'


def brigade_from_item(item) -> Brigade:
    data_lines = item.find_all(class_='EinsatzItemContent_ListView')

    location = data_lines[0].findChildren()[1].text.strip()
    start_text = data_lines[1].findChildren()[1].text.strip()
    end_text = data_lines[2].findChildren()[1].text.strip()

    start = datetime.strptime(start_text, TIME_FORMAT)
    end = datetime.strptime(end_text, TIME_FORMAT) if end_text.lower() != 'andauernd' else None

    return Brigade(
        location,
        start,
        end
    )


def event_from_item(item) -> Event:
    title_item = item.find(class_='Alarmierungen_ListView_Item_Title')
    title = title_item.getText().strip()

    brigades_container = item.find(class_='Alarmierungen_ListView_Item_Content')
    brigade_items = brigades_container.find_all('div', recursive=False)
    brigades = [brigade_from_item(item) for item in brigade_items]

    image_url = item.find(class_='Alarmierungen_ListView_Item_Title_Symbol').find('img').get('src')
    event_type = get_event_type(image_url)

    return Event(
        title,
        event_type,
        brigades,
    )


def parse_content(html: str) -> List[Event]:
    soup = BeautifulSoup(html, 'html.parser')

    container = soup.find(class_='EinsatzlisteContent')
    items = container.find_all(class_='Alarmierungen_ListView_Item')

    return [event_from_item(item) for item in items]


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
