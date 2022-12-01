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

    # Get Lost Well shows
    lost_well_shows = scraper.scrape_lost_well()
    print("Total Lost Well Shows", len(lost_well_shows))

    # Filter out shows that have already happened
    lost_well_shows = list(filter(_filter_by_show_date, lost_well_shows))
    print("Filtered by Date", len(lost_well_shows))

    # Filter out shows that aren't in the DM list
    lost_well_shows = list(filter(partial(_filter_by_band, bands=bands), lost_well_shows))
    print("Filter by Bands", len(lost_well_shows))

    # Add shows to the database
    database.upsert_shows(lost_well_shows)

    # Get the shows back out
    lost_well_shows = database.get_shows()

    pprint.pp(lost_well_shows)
