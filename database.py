from datetime import datetime
import json
import sqlite3


def _get_connection():
    return sqlite3.connect("show_scraper.db")


def _load_bands():
    with open("bands.txt", "r") as bands_file:
        bands_json = json.loads(bands_file.read())
        return [Band(b.get("name"), b.get("genre")) for b in bands_json]


class Band:
    def __init__(self, name, genre, db_id=None):
        self.name = name
        self.genre = genre
        self.db_id = db_id


class Show:
    def __init__(self, title, show_date, show_time, door_time, venue, bands, db_id=None):
        # Don't create shows without titles, show dates, venues, or lists of bands
        if title is None:
            raise ValueError("Cannot create a show without a title.")
        if show_date is None or not isinstance(show_date, datetime):
            raise ValueError("Cannot create a show without a show_date.")
        if bands is None or bands == []:
            raise ValueError("Cannot create a show without a list of bands.")

        self.db_id = db_id
        self.title = title
        self.show_date = show_date
        self.show_time = show_time
        self.door_time = door_time
        self.venue = venue
        self.bands = bands

    def __str__(self):
        return (
            "Show(title='{}', show_date={}, show_time={}, door_time={}, venue={}, bands={}, id={})".format(
                self.title, self.show_date, self.show_time, self.door_time, self.venue, self.bands, self.db_id
            )
        )

    def __repr__(self):
        return self.__str__()


def _show_to_tuple(show):
    return (
        show.title,
        show.show_date.isoformat(),
        show.show_time.isoformat() if show.show_time is not None else None,
        show.door_time.isoformat() if show.show_time is not None else None,
        show.venue,
        json.dumps(show.bands)
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
        return [Band(name=name, genre=genre, db_id=db_id) for db_id, name, genre in result_set.fetchall()]


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
                db_id=db_id
            )
            for title, show_date, door_time, show_time, venue, bands, db_id in result_set.fetchall()
        ]
