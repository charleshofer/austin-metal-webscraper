from datetime import datetime
import json
import sqlite3

from common import Band, Show


def _get_connection():
    return sqlite3.connect("show_scraper.db")


def _load_bands():
    with open("bands.txt", "r") as bands_file:
        bands_json = json.loads(bands_file.read())
        return [Band(b.get("name"), b.get("genre")) for b in bands_json]


def _show_to_tuple(show):
    return (
        show.title,
        show.show_date.isoformat(),
        show.show_time.isoformat() if show.show_time is not None else None,
        show.door_time.isoformat() if show.show_time is not None else None,
        show.venue,
        json.dumps(show.bands),
    )


def init(update_schema=False):
    con = _get_connection()
    # If we need to update the scheme, drop all the existing talbes. WARNING: This will remove all current data
    if update_schema:
        with con:
            con.execute("DROP TABLE bands")
            con.execute("DROP TABLE shows")

    # Add any new tables to the database
    with con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS bands(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, genre)"
        )
        con.execute(
            "CREATE TABLE IF NOT EXISTS shows("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "title TEXT, "
            "show_date TEXT, "
            "door_time TEXT, "
            "show_time TEXT, "
            "venue TEXT, "
            "bands TEXT, "
            "CONSTRAINT unq UNIQUE (show_date, venue))"
        )

    # Add bands that we care about
    upsert_bands([Band(b.name, b.genre) for b in _load_bands()])


def upsert_bands(bands):
    formatted_bands = [(b.name, b.genre) for b in bands]
    con = _get_connection()
    with con:
        con.executemany("INSERT OR REPLACE INTO bands (name, genre) VALUES (?,?)", formatted_bands)


def get_bands():
    con = _get_connection()
    with con:
        result_set = con.execute("SELECT id, name, genre FROM bands")
        return [
            Band(name=name, genre=genre, db_id=db_id)
            for db_id, name, genre in result_set.fetchall()
        ]


def upsert_shows(shows):
    # Format the shows into the form the database wants
    formatted_shows = [_show_to_tuple(s) for s in shows]

    # Get a connection and do the insert
    con = _get_connection()
    with con:
        con.executemany(
            "INSERT OR REPLACE INTO shows (title, show_date, door_time, show_time, venue, bands) VALUES (?,?,?,?,?,?)",
            formatted_shows,
        )


def get_shows():
    con = _get_connection()
    with con:
        result_set = con.execute(
            "SELECT title, show_date, door_time, show_time, venue, bands, id FROM shows"
        )
        return [
            Show(
                title=title,
                show_date=datetime.fromisoformat(show_date),
                show_time=datetime.fromisoformat(show_time) if show_time is not None else None,
                door_time=datetime.fromisoformat(door_time) if door_time is not None else None,
                venue=venue,
                bands=json.loads(bands),
                db_id=db_id,
            )
            for title, show_date, door_time, show_time, venue, bands, db_id in result_set.fetchall()
        ]
