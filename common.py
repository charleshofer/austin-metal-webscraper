"""Module for common data structures used around the application"""

from datetime import datetime


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
        return "Show(title='{}', show_date={}, show_time={}, door_time={}, venue={}, bands={}, id={})".format(
            self.title,
            self.show_date,
            self.show_time,
            self.door_time,
            self.venue,
            self.bands,
            self.db_id,
        )

    def __repr__(self):
        return self.__str__()
