# Austin Metal Webscraper

Part of an effort to try and get all Austin death metal shows listed in
one place where you can filter by subgenre.

## Features

* Scrape venue webpages or event management APIs for show information.
  Eventually, it'd be nice to pull from all of the following:
    * [DONE] The Lost Well
    * [DONE] Come and Take It Live
    * Chess Club
    * Spiderhouse Ballroom
    * Valhalla on Red River
* Store show information in a SQL database
* [TODO] Generate various types of calendars from the show database.
  It'd be great if we could generate the following:
    * Google Calendar
    * Images for Instagram a la Austin Indie Shows
    * Publish a static HTML website with show information
* [TODO] Email or SMS notification features
    * Notifications for specific bands
    * Weekly or monthly email detailing all shows for the coming period
    
## Setup

We use `pipenv`. Run `pipenv sync` to get your Python environment setup.
If you want to run any of the scripts, `pipenv shell` and then
`python <script>.py`.
