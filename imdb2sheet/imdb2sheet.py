"""Fetch IMDB and update google sheet values."""

from __future__ import annotations

import csv
import dataclasses
import datetime
import enum
import json
import pathlib
import re
from typing import Optional

from etils import epy
import requests


class MovieType(epy.StrEnum):
    """Movie types."""

    MOVIE = enum.auto()
    TV_MOVIE = enum.auto()
    TV_SERIES = enum.auto()
    TV_MINI_SERIES = enum.auto()
    TV_SPECIAL = enum.auto()
    TV_EPISODE = enum.auto()
    VIDEO = enum.auto()
    SHORT = enum.auto()


# Genres can be:
# Action
# Adventure
# Animation
# Biography
# Comedy
# Crime
# Documentary
# Drama
# Family
# Fantasy
# Film Noir
# History
# Horror
# Music
# Musical
# Mystery
# Romance
# Sci-Fi
# Short Film
# Sport
# Superhero
# Thriller
# War
# Western
Genre = str


@dataclasses.dataclass
class Movie:
    id: str
    title: str
    type: MovieType
    genres: list[Genre]
    directors: list[str]
    year: int  # Year sometimes do not match release date
    release_date: Optional[datetime.date]
    runtime: datetime.timedelta
    num_ratings: int
    imdb_rating: float
    my_rating: int
    date_rated: datetime.date

    @property
    def url(self) -> str:
        return f"https://www.imdb.com/title/{self.id}/"

    @classmethod
    def from_ratings(cls, row):
        runtime = row["Runtime (mins)"]
        runtime = datetime.timedelta(minutes=int(runtime) if runtime else 0)

        if release_date := row["Release Date"]:
            release_date = datetime.datetime.strptime(release_date, "%Y-%m-%d").date()
        else:
            release_date = None

        with epy.maybe_reraise(f"{row=}\n"):
            return cls(
                id=row["Const"],
                title=row["Title"],
                type=MovieType(camel2snake(row["Title Type"])),
                genres=[g for g in row["Genres"].split(", ")],
                directors=[d for d in row["Directors"].split(", ")],
                year=int(row["Year"]),
                release_date=release_date,
                runtime=runtime,
                num_ratings=int(row["Num Votes"]),
                imdb_rating=float(row["IMDb Rating"]),
                my_rating=int(row["Your Rating"]),
                date_rated=datetime.datetime.strptime(
                    row["Date Rated"], "%Y-%m-%d"
                ).date(),
            )


# TODO(epot):
# {"Title":"Guardians of the Galaxy Vol. 2","Year":"2017","Rated":"PG-13","Released":"05 May 2017","Runtime":"136 min","Genre":"Action, Adventure, Comedy","Director":"James Gunn","Writer":"James Gunn, Dan Abnett, Andy Lanning","Actors":"Chris Pratt, Zoe Saldana, Dave Bautista","Plot":"The Guardians struggle to keep together as a team while dealing with their personal family issues, notably Star-Lord's encounter with his father the ambitious celestial being Ego.","Language":"English","Country":"United States","Awards":"Nominated for 1 Oscar. 15 wins & 58 nominations total","Poster":"https://m.media-amazon.com/images/M/MV5BNjM0NTc0NzItM2FlYS00YzEwLWE0YmUtNTA2ZWIzODc2OTgxXkEyXkFqcGdeQXVyNTgwNzIyNzg@._V1_SX300.jpg","Ratings":[{"Source":"Internet Movie Database","Value":"7.6/10"},{"Source":"Rotten Tomatoes","Value":"85%"},{"Source":"Metacritic","Value":"67/100"}],"Metascore":"67","imdbRating":"7.6","imdbVotes":"622,462","imdbID":"tt3896198","Type":"movie","DVD":"22 Aug 2017","BoxOffice":"$389,813,101","Production":"N/A","Website":"N/A","Response":"True"}


def _add_arguments(url, **arguments):
    arguments = "&".join(f"{k}={v}" for k, v in arguments.items())
    if arguments:
        url = f"{url}?{arguments}"
    return url


class OmdbAPI:
    """OMDB API."""

    def query(self, imdb_id):
        api_key = ""
        url = f"http://www.omdbapi.com/"
        url = _add_arguments(
            url,
            i=imdb_id,
            apikey=api_key,
        )

        # Fetch and parse result
        resp = requests.get(url)
        out = json.loads(resp.text)
        if out.get("Response", True) == "False":
            status_message = out["Error"]
            raise ValueError(f"Invalid request: {url}.\n{status_message=}")
        return out


def load_movies(fetch_extra=False) -> list[Movie]:
    # 1) Fetch IMDB ratings
    # TODO(epot): Ideally, should fetch the public list
    # url = "https://www.imdb.com/user/ur42567646/ratings/export"
    # resp = requests.get(url, allow_redirects=True)
    # resp.text
    p = pathlib.Path(__file__).parent / "ratings.csv"
    with p.open(errors="replace") as f:
        movies = [Movie.from_ratings(row) for row in csv.DictReader(f)]

    if not fetch_extra:
        return movies

    # 3) Fetch missing metadata (thumbnail, country,...)
    omdb_api = OmdbAPI()
    for movie in movies:
        out = omdb_api.query("tt0068646")
    print(out)


def main():
    """Main script."""
    movies = load_movies()


def camel2snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


if __name__ == "__main__":
    main()
