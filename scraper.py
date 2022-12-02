from datetime import datetime
from functools import partial
import logging
import os
import pprint
import re
import requests as rq
from requests_oauthlib import OAuth2Session

from common import Show

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Regex to split up show titles and descriptions to find band names. For example: Lost Well will list the bands in
# their event titles, like "Death File Red, Bruka, Ungrieved"
SPLIT_TOKENS = ",|:|/"


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
    logger.info("Found %i total events at The Lost Well", len(events_list))

    shows = []
    for event in events_list:
        shows.append(
            Show(
                title=event.get("title"),
                show_date=datetime.fromtimestamp(int(event.get("start")) / 1000),
                show_time=None,
                door_time=None,
                venue="The Lost Well",
                bands=[b.strip() for b in re.split(SPLIT_TOKENS, event.get("title"))],
            )
        )

    return shows


def scrape_catil():
    # Get the API key from the environment
    oauth_token = os.environ.get("EVENTBRITE_TOKEN")
    pagination_token = "start"
    shows = []

    while pagination_token is not None:
        # Set up the URL, adding a continuation/pagination token if this isn't the first page
        url = "https://www.eventbriteapi.com/v3/venues/28302591/events?expand=music_properties&token={}".format(oauth_token)
        if pagination_token != "start":
            url += "&continuation={}".format(pagination_token)

        # Get the response and unpack it
        response = rq.get(url)
        response_data = response.json()
        events_list = response_data.get("events")
        page_info = response_data.get("pagination")

        logger.info(
            "Found %i events on page %i of %i for Come and Take It Live",
            len(events_list),
            page_info.get("page_number"),
            page_info.get("page_count")
        )

        # Go through every event, and create a Show object for it
        for event in events_list:
            bands = _catil_band_parse(event.get("name").get("text"))
            if bands:
                shows.append(
                    Show(
                        title=event.get("name").get("text"),
                        show_date=datetime.strptime(event.get("start").get("local"), "%Y-%m-%dT%H:%M:%S"),
                        show_time=datetime.strptime(event.get("start").get("local"), "%Y-%m-%dT%H:%M:%S"),
                        door_time=None,
                        venue="Come and Take It Live",
                        bands=bands,
                    )
                )

        # Set the new pagination token
        pagination_token = page_info.get("continuation")

    logger.info("Found %i total events at Come and Take It Live", len(shows))
    return shows


def _catil_band_parse(event_title):
    # Break apart the event title to get the bands.
    # TODO: Right now we just band on the fact that CATIL adds every band to the event title. But this is not the case
    #  even half the time.
    bands = [b.strip() for b in re.split(SPLIT_TOKENS, event_title)]
    # Remove any empty strings
    bands = filter(lambda s: s != "", bands)
    return list(bands)


if __name__ == "__main__":
    shows = scrape_catil()
    pprint.pp(shows)

