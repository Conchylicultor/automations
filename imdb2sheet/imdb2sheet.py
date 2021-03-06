"""Fetch IMDB and update google sheet values."""

from __future__ import annotations

import csv
import dataclasses
import datetime
import enum
import json
import os
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


@dataclasses.dataclass(frozen=True)
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

    # Extra metadata
    plot: str = None
    writers: list[str] = None
    actors: list[str] = None
    languages: list[str] = None
    countries: list[str] = None
    pg_rating: str = None
    poster: str = None
    awards: str = None
    box_office: int = None
    rotten_rating: int = None
    metacritic_rating: int = None

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
                type=MovieType(_camel2snake(row["Title Type"])),
                genres=_list_str(row["Genres"]),
                directors=_list_str(row["Directors"]),
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

    def replace_with_metadata(self) -> Movie:
        """Update with additional metadata.

        Example:

        ```
        {
            "Title":"Guardians of the Galaxy Vol. 2",
            "Year":"2017",
            "Rated":"PG-13",
            "Released":"05 May 2017",
            "Runtime":"136 min",
            "Genre":"Action, Adventure, Comedy",
            "Director":"James Gunn",
            "Writer":"James Gunn, Dan Abnett, Andy Lanning",
            "Actors":"Chris Pratt, Zoe Saldana, Dave Bautista",
            "Plot":"The Guardians struggle to keep together as a team while dealing with their personal family issues, notably Star-Lord's encounter with his father the ambitious celestial being Ego.",
            "Language":"English",
            "Country":"United States",
            "Awards":"Nominated for 1 Oscar. 15 wins & 58 nominations total","
            Poster":"https://m.media-amazon.com/images/M/MV5BNjM0NTc0NzItM2FlYS00YzEwLWE0YmUtNTA2ZWIzODc2OTgxXkEyXkFqcGdeQXVyNTgwNzIyNzg@._V1_SX300.jpg",
            "Ratings":[
                {"Source":"Internet Movie Database","Value":"7.6/10"},
                {"Source":"Rotten Tomatoes","Value":"85%"},
                {"Source":"Metacritic","Value":"67/100"},
            ],
            "Metascore":"67",
            "imdbRating":"7.6",
            "imdbVotes":"622,462",
            "imdbID":"tt3896198",
            "Type":"movie",
            "DVD":"22 Aug 2017",
            "BoxOffice":"$389,813,101",
            "Production":"N/A",
            "Website":"N/A",
            "Response":"True",
        }
        ```

        Note: Series have slightly different fields

        """
        if self.plot is not None:
            print(f"Reusing {self.title}")
            return self
        print(f"Fetching {self.title}")

        omdb_api = OmdbAPI()
        out = omdb_api.query(self.id)

        with epy.maybe_reraise(f"{out=}\n"):
            ratings = out["Ratings"]
            rotten_ratings = [
                r["Value"] for r in ratings if r["Source"] == "Rotten Tomatoes"
            ]
            if rotten_ratings:
                (rotten_rating,) = rotten_ratings
                rotten_rating = int(rotten_rating.rstrip("%"))
            else:
                rotten_rating = -1

            if (metascore := out["Metascore"]) != "N/A":
                metacritic_rating = int(metascore)
            else:
                metacritic_rating = -1

            if (box_office := out.get("BoxOffice", "N/A")) != "N/A":
                box_office = int(box_office.lstrip("$").replace(",", ""))
            else:
                box_office = 0

            return dataclasses.replace(
                self,
                plot=out["Plot"],
                writers=_list_str(out["Writer"]),
                actors=_list_str(out["Actors"]),
                languages=_list_str(out["Language"]),
                countries=_list_str(out["Country"]),
                pg_rating=out["Rated"],
                poster=out["Poster"],
                awards=out["Awards"],
                box_office=box_office,
                rotten_rating=rotten_rating,
                metacritic_rating=metacritic_rating,
            )

    def to_json(self) -> str:
        value = dataclasses.asdict(self)
        value = json.dumps(value, default=serialize_json)
        return value

    @classmethod
    def from_json(cls, json_value: str) -> Movie:
        init_kwargs = json.loads(json_value, object_hook=deserialize_json)
        init_kwargs["type"] = MovieType(init_kwargs["type"])
        return cls(**init_kwargs)


def serialize_json(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.date):
        name = "date"
        val = obj.isoformat()
    elif isinstance(obj, datetime.timedelta):
        name = "timedelta"
        val = obj.total_seconds()
    else:
        raise TypeError(f"Type {type(obj)} not serializable")
    return f"{name}://{val}"


def deserialize_json(json_dict):
    for k, v in json_dict.items():
        if isinstance(v, str):
            if v.startswith("date://"):
                json_dict[k] = datetime.date.fromisoformat(v[len("date://") :])
            elif v.startswith("timedelta://"):
                json_dict[k] = datetime.timedelta(
                    seconds=float(v[len("timedelta://") :])
                )
    return json_dict


def _add_arguments(url, **arguments):
    arguments = "&".join(f"{k}={v}" for k, v in arguments.items())
    if arguments:
        url = f"{url}?{arguments}"
    return url


class OmdbAPI:
    """OMDB API."""

    def query(self, imdb_id):
        if not (api_key := os.environ.get("OMDB_KEY")):
            raise ValueError("Missing OMDB_KEY")
        url = f"http://www.omdbapi.com/"
        url = _add_arguments(
            url,
            i=imdb_id,
            apikey=api_key,
        )

        # Fetch and parse result
        resp = requests.get(url)
        out = json.loads(resp.text)
        if out["Response"] != "True":
            status_message = out["Error"]
            raise ValueError(f"Invalid request: {url}.\n{status_message=}")
        return out


def load_movies() -> list[Movie]:
    # 1) Fetch IMDB ratings
    # TODO(epot): Ideally, should fetch the public list
    # url = "https://www.imdb.com/user/ur42567646/ratings/export"
    # resp = requests.get(url, allow_redirects=True)
    # resp.text
    p = pathlib.Path(__file__).parent / "ratings.csv"
    with p.open(encoding="windows-1252") as f:
        movies = [Movie.from_ratings(row) for row in csv.DictReader(f)]

    return movies


def load_movies_extra() -> list[Movie]:
    out_path = pathlib.Path(__file__).parent / "cache.jsonl"
    movies = [Movie.from_json(v) for v in out_path.read_text().splitlines() if v]
    return movies


def main():
    """Main script."""
    # Load movies and pre-computed movies
    movies = load_movies()
    movies_extra = {m.id: m for m in load_movies_extra()}

    # Use pre-computed version when available
    movies = [movies_extra.get(m.id, m) for m in movies]

    # Fetch extra movies
    extra_movies = [m.replace_with_metadata().to_json() for m in movies]

    # Save output
    out_path = pathlib.Path(__file__).parent / "cache.jsonl"
    out_path.write_text("\n".join(extra_movies))


def _camel2snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _list_str(names: str) -> list[str]:
    return [d for d in names.split(", ")]


if __name__ == "__main__":
    main()
