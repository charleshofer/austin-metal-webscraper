from datetime import datetime
import requests as rq

from common import Show


def scrape_lost_well():
    """

    Example response from the API:
    {'endHour': 23,
      'allday': False,
      'end': '1677369600000',
      'links': {'0': {'url': 'https://www.eventbrite.com/e/unsane-glassing-bridge-farmers-tickets-460866894287',
                      'newtab': True,
                      'text': 'https://www.eventbrite.com/e/unsane-glassing-bridge-farmers-tickets-460866894287'}},
      'title': 'Unsane, Glassing, Bridge Farmers',
      'image': {'source': 'wix',
                'url': 'https://static.wixstatic.com/media/28c0f7_d208ff313b81473b8efb811511eac005~mv2.jpg/v1/fill/w_518,h_800,q_85,usm_0.66_1.00_0.01/28c0f7_d208ff313b81473b8efb811511eac005~mv2.jpg',
                'original_url': '28c0f7_d208ff313b81473b8efb811511eac005~mv2.jpg',
                'height': 800,
                'width': 517.6470588235294,
                'token': 'b0bce7daf353e00b8e52bed085bc0976'},
      'endMinutes': 0,
      'start': '1677369600000',
      'startMinutes': 0,
      'location_to_gmaps': True,
      'id': 'event_1n1SIWAjl7b3dt7ElQ23K',
      'startHour': 19}

    :return:
    """
    response = rq.get(
        "https://inffuse.eventscalendar.co/js/v0.1/calendar/data"
        "?pageId=c1dmp"
        "&compId=comp-k7ala10g"
        "&viewerCompId=comp-k7ala10g"
        "&siteRevision=497"
        "&viewMode=site"
        "&deviceType=desktop"
        "&locale=en"
        "&regionalLanguage=en"
        "&width=462"
        "&height=893"
        "&instance=KILHR4Akij1YBuqKTx2dqYyOvPptIL0QV6HKI8F4wJE.eyJpbnN0YW5jZUlkIjoiOGUwODA1MDEtNmQwMy00YjVlLTkzYmYtNGZmNDU5MDI4NjI5IiwiYXBwRGVmSWQiOiIxMzNiYjExZS1iM2RiLTdlM2ItNDliYy04YWExNmFmNzJjYWMiLCJzaWduRGF0ZSI6IjIwMjItMTItMDFUMTc6MDE6MTYuMzkxWiIsInZlbmRvclByb2R1Y3RJZCI6InByZW1pdW0iLCJkZW1vTW9kZSI6ZmFsc2UsImFpZCI6IjkxNTUwMjU4LTNiYzgtNGQzNC1iNjgzLWE2YjRhNTk0ZmIzNyIsInNpdGVPd25lcklkIjoiMjhjMGY3NjYtMTMyOS00MzFmLWFiMDEtYWJmYWNkY2JlNTUzIn0"
        "&commonConfig=%7B%22brand%22:%22wix%22,%22bsi%22:%22bde8d293-5ef6-467c-9b0b-8374179dbc1a%7C1%22,%22BSI%22:%22bde8d293-5ef6-467c-9b0b-8374179dbc1a%7C1%22%7D"
        "&vsi=c09ed433-6e4e-49d8-871c-eef8d71c48e0"
    )

    response_data = response.json()
    events_list = response_data.get("project").get("data").get("events")

    shows = []
    for event in events_list:
        shows.append(
            Show(
                title=event.get("title"),
                show_date=datetime.fromtimestamp(int(event.get("start")) / 1000),
                show_time=None,
                door_time=None,
                venue="The Lost Well",
                bands=[b.strip() for b in event.get("title").split(",")],
            )
        )

    return shows
