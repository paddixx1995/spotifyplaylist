"""Baut eine Spotify-Playlist mit mindestens 10.000 Songs aus mehreren Genres."""

import json
import os
import time
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

PLAYLIST_NAME = "VISIO XXL"
GENRES = ["hardtekk", "techno", "rap", "rock"]
TARGET_SONG_COUNT = 10_000
BATCH_SIZE = 100
SEARCH_PAGE_LIMIT = 50  # Spotify-Maximum pro Suchanfrage
TRACKED_FILE = Path("added_tracks.json")
SCOPE = "playlist-modify-public playlist-modify-private"


def get_spotify_client() -> spotipy.Spotify:
    auth_manager = SpotifyOAuth(
        client_id=os.environ["SPOTIPY_CLIENT_ID"],
        client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=os.environ.get("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
        scope=SCOPE,
        cache_path=".cache",
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def load_added_track_ids() -> set:
    if TRACKED_FILE.exists():
        with TRACKED_FILE.open("r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_added_track_ids(track_ids: set) -> None:
    with TRACKED_FILE.open("w", encoding="utf-8") as f:
        json.dump(sorted(track_ids), f, indent=2)


def get_or_create_playlist(sp: spotipy.Spotify) -> str:
    user_id = sp.current_user()["id"]

    offset = 0
    while True:
        playlists = sp.current_user_playlists(limit=50, offset=offset)
        for playlist in playlists["items"]:
            if playlist["name"] == PLAYLIST_NAME:
                return playlist["id"]
        if not playlists["next"]:
            break
        offset += 50

    playlist = sp.user_playlist_create(
        user=user_id,
        name=PLAYLIST_NAME,
        public=False,
        description="Automatisch erstellte Playlist mit Hardtekk, Techno, Rap und Rock.",
    )
    return playlist["id"]


def get_current_playlist_track_ids(sp: spotipy.Spotify, playlist_id: str) -> set:
    track_ids = set()
    offset = 0
    while True:
        results = sp.playlist_items(
            playlist_id, fields="items.track.id,next", additional_types=["track"], limit=100, offset=offset
        )
        for item in results["items"]:
            track = item.get("track")
            if track and track.get("id"):
                track_ids.add(track["id"])
        if not results["next"]:
            break
        offset += 100
    return track_ids


def search_tracks_for_genre(sp: spotipy.Spotify, genre: str, offset: int) -> list:
    results = sp.search(q=f"genre:{genre}", type="track", limit=SEARCH_PAGE_LIMIT, offset=offset)
    return results["tracks"]["items"]


def collect_new_tracks(sp: spotipy.Spotify, known_ids: set, needed: int) -> list:
    """Sucht in allen Genres reihum nach neuen, noch nicht bekannten Tracks."""
    new_track_ids = []
    genre_offsets = {genre: 0 for genre in GENRES}
    exhausted_genres = set()

    while len(new_track_ids) < needed and len(exhausted_genres) < len(GENRES):
        for genre in GENRES:
            if genre in exhausted_genres:
                continue
            if len(new_track_ids) >= needed:
                break

            tracks = search_tracks_for_genre(sp, genre, genre_offsets[genre])
            genre_offsets[genre] += SEARCH_PAGE_LIMIT

            if not tracks:
                exhausted_genres.add(genre)
                continue
            if genre_offsets[genre] >= 1000:
                # Spotify-Suche erlaubt insgesamt maximal Offset 1000.
                exhausted_genres.add(genre)

            for track in tracks:
                track_id = track.get("id")
                if not track_id or track_id in known_ids:
                    continue
                known_ids.add(track_id)
                new_track_ids.append(track_id)
                if len(new_track_ids) >= needed:
                    break

    return new_track_ids


def main() -> None:
    sp = get_spotify_client()
    playlist_id = get_or_create_playlist(sp)
    print(f"Playlist '{PLAYLIST_NAME}' bereit (ID: {playlist_id}).")

    known_ids = load_added_track_ids()
    known_ids |= get_current_playlist_track_ids(sp, playlist_id)
    save_added_track_ids(known_ids)

    print(f"Aktuell {len(known_ids)} Songs bekannt/in der Playlist.")

    while len(known_ids) < TARGET_SONG_COUNT:
        remaining = TARGET_SONG_COUNT - len(known_ids)
        batch_size = min(BATCH_SIZE, remaining)

        new_tracks = collect_new_tracks(sp, known_ids, batch_size)
        if not new_tracks:
            print("Keine weiteren neuen Songs gefunden. Suche wird beendet.")
            break

        for i in range(0, len(new_tracks), 100):
            chunk = new_tracks[i : i + 100]
            sp.playlist_add_items(playlist_id, chunk)

        save_added_track_ids(known_ids)
        print(f"{len(new_tracks)} neue Songs hinzugefügt. Gesamt: {len(known_ids)}/{TARGET_SONG_COUNT}")

        time.sleep(1)  # Schont die Spotify-API-Rate-Limits.

    print(f"Fertig. Playlist enthält {len(known_ids)} Songs.")


if __name__ == "__main__":
    main()
