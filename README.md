<img src="https://git.tuxworld.nl/yixboost/games-v2/raw/branch/main/static/images/readme_banner.png">

# Yixboost Games V2
Open-source rewrite of Yixboost Games, it's still in early alpha. Some features are not implemented yet, they are marked with "N/I". You can view the project's kanban board [here](https://git.tuxworld.nl/yixboost/games-v2/projects/2).

## Public testing instance
There is a public instance available for testing at https://version2.yixboost.eu. If you find any bugs, please report them [here](https://version2.yixboost.eu/report). You can login using Hack Club Auth. This games-v2 instance is hosted on [Hack Club Nest](https://nest.hackclub.com).

## The goal
The goal of this project is to make a completely better version of the closed-source V1 version of Yixboost Games that feels and works the same as V1, but better, with plugin support, better database connections, and good caching. The way of logging in is made much better and safer with OpenID.

## Built-in plugins
- ``game_loader``: Gets games from the database and displays them on all pages, manages all the game content.
- ``search``: Simple search plugin for searching games with a search page and search bar in the navbar.
- ``issues``: Bug report form with autofill features and a game action button for reporting a game on the game's page.

## Tech Stack
- FastAPI
- Jinja2
- SQLite
- Redis

This project is submitted to Hack Club's [Stardance](https://stardance.hackclub.com) event. (You can view devlogs here too)
https://stardance.hackclub.com/projects/17189