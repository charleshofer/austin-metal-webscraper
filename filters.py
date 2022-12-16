from datetime import datetime
from functools import partial
import pprint

import database
import scraper


def _filter_by_show_date(show):
    return show.show_date >= datetime.now()


def _filter_by_band(show, bands):
    band_names = [b.name for b in bands]
    for band in show.bands:
        if band in band_names:
            return True
    return False


def _filter_by_existing(new_show, existing_shows):
    for existing_show in existing_shows:
        if new_show.show_date.strftime("%Y-%m-%d") == existing_show.show_date.strftime("%Y-%m-%d"):
            return False
    return True


if __name__ == "__main__":
    # Initialize database
    database.init(update_schema=False)

    # Get the list of approved bands
    bands = database.get_bands()
    existing_shows = database.get_shows()
    all_shows = []

    # Get Lost Well shows
    lost_well_shows = scraper.scrape_lost_well()
    print("Total Lost Well Shows", len(lost_well_shows))
    all_shows += lost_well_shows

    # Get CATIL shows
    catil_shows = scraper.scrape_catil()
    print("Total CATIL Shows", len(catil_shows))
    all_shows += catil_shows

    # Get Mohawk shows
    mohawk_shows = scraper.scrape_mohawk()
    print("Total Mohawk Shows", len(mohawk_shows))
    all_shows += mohawk_shows

    # Filter out shows that have already happened
    all_shows = list(filter(_filter_by_show_date, all_shows))
    print("Filtered by Date", len(all_shows))

    # Filter out shows that aren't in the DM list
    all_shows = list(filter(partial(_filter_by_band, bands=bands), all_shows))
    print("Filter by Bands", len(all_shows))

    # Add shows to the database
    database.upsert_shows(all_shows)

    # Get the shows back out
    db_shows = database.get_shows()
    pprint.pp(db_shows)
