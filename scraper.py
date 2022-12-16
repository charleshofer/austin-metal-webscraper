import json
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
# their event titles, like "Death File Red, Bruka, Ungrieved".
# TODO: Death metal bands don't usually include these characters in their names, but we need a way to handle exceptions
SPLIT_TOKENS = ",|:|/|&"


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
        response.raise_for_status()
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

    return shows


def _catil_band_parse(event_title):
    # Break apart the event title to get the bands.
    # TODO: Right now we just band on the fact that CATIL adds every band to the event title. But this is not the case
    #  even half the time.
    bands = [b.strip() for b in re.split(SPLIT_TOKENS, event_title)]
    # Remove any empty strings
    bands = filter(lambda s: s != "", bands)
    # Remove "and" and "&" from bands at the end of the list
    bands = filter(lambda s: s.replace("&", "").replace("and", "").strip(), bands)
    return list(bands)


def scrape_mohawk():
    return _scrape_prekindle("Mohawk", "https://www.prekindle.com/api/events/organizer/531433527670566235")


def scrape_ballroom():
    return _scrape_prekindle("The Ballroom", "https://www.prekindle.com/api/events/organizer/531433527847976172")


def scrape_metal_archives():
    # TODO: MA isn't the most well-built site. I'm getting a 403 from every MA request I get, but it still returns the
    #   start of the data. Kind of deceptive. Figure out how to not get 403s.
    headers = {
        "authority": "www.metal-archives.com",
    }
    resp = rq.get(
        "https://www.metal-archives.com/search/ajax-advanced/searching/bands/?bandName=&genre=Death+Metal&country=&yearCreationFrom=&yearCreationTo=&bandNotes=&status=&themes=&location=&bandLabelName=&sEcho=1&iColumns=3&sColumns=&iDisplayStart=500&iDisplayLength=200&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&_=1671215632964",
        headers=headers
    )
    #resp = rq.get("https://www.metal-archives.com/browse/ajax-genre/g/death/json/1?sEcho=2&iColumns=4&sColumns=&iDisplayStart=500&iDisplayLength=500&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&iSortCol_0=0&sSortDir_0=asc&iSortingCols=1&bSortable_0=true&bSortable_1=true&bSortable_2=true&bSortable_3=false")
    print(resp.ok)
    print(resp.status_code)
    print(resp.text[:1000])
    #pprint(resp.json())


def _scrape_prekindle(venue, url):
    # Send the request
    resp = rq.get(url)

    # Remove the jQuery callback from the response and load the JSON it contains
    resp_text = resp.text
    resp_text = resp_text.replace("callback(", "")
    resp_text = resp_text[:-1]
    resp_data = json.loads(resp_text)

    pprint.pp(resp_data)

    # Get turn the response data into Show objects
    shows = []
    for event in resp_data.get("events", []):
        bands = event.get("lineup")
        # Sometimes venues don't fill out the 'lineup' property. Try to compensate for this by just adding the title
        # of the event as a band. Sometimes venues will just list the headliner. It's not a big deal if we have
        # nonsense band names that are actually event names (like 'Summer Slaughter Tour'), because we filter
        # out the bands we don't care about.
        if bands is None or bands == []:
            bands += [b.strip() for b in re.split(SPLIT_TOKENS, event.get("title"))]
        if bands:
            show_date = datetime.strptime(event.get("date"), "%m/%d/%Y")
            show_time = datetime.combine(date=show_date, time=datetime.strptime(event.get("time"), "%I:%M%p").time())
            door_time = datetime.combine(date=show_date, time=datetime.strptime(event.get("doorsTime"), "%I:%M%p").time())
            shows.append(
                Show(
                    title=event.get("title"),
                    show_date=show_date,
                    show_time=show_time,
                    door_time=door_time,
                    venue=venue,
                    bands=bands,
                )
            )
    return shows


if __name__ == "__main__":
    pprint.pp(scrape_lost_well())

