#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Eren-is
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import re
import base64
import requests
import argparse
from datetime import datetime, timedelta
from urllib.parse import quote
from dotenv import dotenv_values

spotify_url_pattern = r"https:\/\/open\.spotify\.com\/track\/[\w?=\-&]+"

class SpTrackGetter:
    _api_auth_url = "https://accounts.spotify.com/api/token"
    _api_tracks_url = "https://api.spotify.com/v1/tracks/"
    _api_audio_features_url = "https://soundstat.info/api/v1/track/"
    _search_url = "https://www.youtube.com/results?search_query={}"

    def __init__(self, url: str, client_id: str, client_secret: str, soundstat_key: str=""):
        self.url = url
        self.id = self.get_id_from_url(self.url)
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__access_token = ""
        self.__token_valid_until = datetime.now()
        self.__soundstat_key = soundstat_key
        self.title = ""
        self.artists = []
        self.album = {}
        self.duration_s = 0
        self.release_date = ""
        self.cover_arts = {}
        self.popularity = 0
        self.youtube_search_url = ""
        # Soundstat related data:
        self.audio_features_in_progress = False
        self.genre = ""
        self.acousticness = 0
        self.danceability = 0
        self.energy = 0
        self.instrumentalness = 0
        self.valence = 0
        self.tempo = 0
        self.load_info()

    def get_id_from_url(self, url: str) -> str:
        return url.split('/')[-1].split('&')[0].split('?')[0]

    def get_track_search_url(self, artist: str, title: str) -> str:
        encoded_text = quote(f"{artist} {title}")
        return self._search_url.format(encoded_text)

    def load_info(self, audio_features_only: bool=False):
        if audio_features_only is False:
            # Make sure we have a Spotify API token
            self.__auth()
            # Get track data
            data = self._get_track_json(self.id)
            self.title = data["name"]
            self.artists = data["artists"]
            self.album = data["album"]
            self.duration_s = data["duration_ms"] / 1000
            self.release_date = data["album"]["release_date"]
            self.cover_arts = data["album"]["images"]
            self.popularity = data["popularity"]
            self.youtube_search_url = self.get_track_search_url(self.artists[0].name, self.title)

        if self.__soundstat_key != "":
            # Get audio features
            data = self._get_audio_features_json(self.id)
            if len(data) > 0:
                self.audio_features_in_progress = False
                self.genre = data["genre"]
                self.acousticness = data["features"]["acousticness"]
                self.danceability = data["features"]["danceability"]
                self.energy = data["features"]["energy"]
                self.instrumentalness = data["features"]["instrumentalness"]
                self.valence = data["features"]["valence"]
                self.tempo = data["features"]["tempo"]
            else:
                self.audio_features_in_progress = True

    def _get_track_json(self, track_id: str) -> dict:
        header = {"Authorization": f"Bearer {self.__access_token}"}
        url = f"{self._api_tracks_url}{track_id}"
        response = requests.get(url, headers=header)

        if response.status_code != 200:
            raise Exception(f"Invalid response when getting track data: {response.status_code}")

        return response.json()

    def _get_audio_features_json(self, track_id: str) -> dict:
        header = {"accept" : "application/json",
                  "x-api-key": self.__soundstat_key}
        url = f"{self._api_audio_features_url}{track_id}"
        response = requests.get(url, headers=header)

        if response.status_code == 202:
            response_json = response.json()
            if "analysis in progress" in response_json["detail"]:
                return {}
            else:
                raise Exception(f"Invalid response when getting track data: {response.status_code} - {response_json["detail"]}")

        if response.status_code != 200:
            raise Exception(f"Invalid response when getting audio features: {response.status_code}")

        return response.json()

    def __auth(self, force: bool=False):
        if (len(self.__access_token) == 0) or (datetime.now() > self.__token_valid_until) or (force is True):
            auth_data = f"{self.__client_id}:{self.__client_secret}"
            auth_data_base64 = base64.b64encode(auth_data.encode())
            header = {"Content-Type": "application/x-www-form-urlencoded",
                      "Authorization": f"Basic {auth_data_base64.decode("ascii")}",
                      "Cache-Control": "no-cache",
                      "Pragma": "no-cache"}
            data = {"grant_type" : "client_credentials"}
            response = requests.post(self._api_auth_url, headers=header, data=data)

            if response.status_code != 200:
                raise Exception(f"Failed to acquire API access token: {response.status_code}")

            response_json = response.json()
            self.__token_valid_until = datetime.now() + timedelta(seconds=response_json["expires_in"])
            self.__access_token = response_json["access_token"]

    def get_data_dict(self) -> dict:
        if self.__soundstat_key != "":
            return {"url" : self.url,
                    "id" : self.id,
                    "title" : self.title,
                    "artists" : self.artists,
                    "album" : self.album,
                    "duration_s" : self.duration_s,
                    "release_date" : self.release_date,
                    "cover_arts" : self.cover_arts,
                    "popularity" : self.popularity,
                    "youtube_search_url" : self.youtube_search_url,
                    "audio_features_in_progress" : self.audio_features_in_progress,
                    "genre" : self.genre,
                    "acousticness" : self.acousticness,
                    "danceability" : self.danceability,
                    "energy" : self.energy,
                    "instrumentalness" : self.instrumentalness,
                    "valence" : self.valence,
                    "tempo" : self.tempo}
        else:
            return {"url" : self.url,
                    "id" : self.id,
                    "title" : self.title,
                    "artists" : self.artists,
                    "album" : self.album,
                    "duration_s" : self.duration_s,
                    "release_date" : self.release_date,
                    "cover_arts" : self.cover_arts,
                    "popularity" : self.popularity,
                    "youtube_search_url" : self.youtube_search_url}

def spotify_url_find(string: str) -> str:
    result = re.search(spotify_url_pattern, string)
    if result is None:
        return ""
    else:
        return result.group()

def spotify_url_type(arg: str) -> str:
    if re.match(spotify_url_pattern, arg) is None:
        raise argparse.ArgumentTypeError(f"Invalid URL format: {arg}")
    else:
        return arg

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Spotify song info from a Spotify url")
    parser.add_argument("url", type=spotify_url_type, help="Song URL")
    args = parser.parse_args()

    config = dotenv_values(".env")

    if "SPOTIFY_CLIENT" not in config or "SPOTIFY_SECRET" not in config:
        raise Exception("Missing SPOTIFY_CLIENT or SPOTIFY_SECRET in .env file")

    if "SOUNDSTAT_KEY" in config:
        soundstat_key = config["SOUNDSTAT_KEY"]
    else:
        soundstat_key = ""

    sp_info_getter = SpTrackGetter(args.url, config["SPOTIFY_CLIENT"], config["SPOTIFY_SECRET"], soundstat_key)

    print(sp_info_getter.get_data_dict())
