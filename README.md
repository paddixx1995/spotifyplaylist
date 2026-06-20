# VISIO XXL Playlist Builder

Python-Anwendung, die sich per OAuth mit der Spotify API verbindet, eine
Playlist namens **"VISIO XXL"** erstellt (falls noch nicht vorhanden) und sie
automatisch mit Songs aus den Genres **Hardtekk, Techno, Rap und Rock**
befüllt — pro Durchgang werden bis zu 100 neue, noch nicht enthaltene Songs
hinzugefügt. Das Programm läuft so lange, bis die Playlist mindestens
**10.000 Songs** enthält, und merkt sich bereits hinzugefügte Titel in
`added_tracks.json`, damit bei einem erneuten Start keine Duplikate entstehen.

## 1. Spotify App erstellen

1. Gehe zu https://developer.spotify.com/dashboard und logge dich ein.
2. Klicke auf **"Create app"**.
3. Vergib einen Namen (z. B. "VISIO XXL Builder") und eine Beschreibung.
4. Trage als **Redirect URI** ein: `http://127.0.0.1:8888/callback`
   (muss exakt mit der URI in der `.env`-Datei übereinstimmen).
5. Wähle als API **"Web API"** aus und speichere die App.
6. Öffne **"Settings"** der App — dort findest du **Client ID** und
   **Client Secret** (Secret über "View client secret" anzeigen).

## 2. Projekt einrichten

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Zugangsdaten eintragen

Kopiere `.env.example` zu `.env`:

```bash
cp .env.example .env
```

Öffne `.env` und trage deine Werte ein:

```
SPOTIPY_CLIENT_ID=deine_client_id_hier
SPOTIPY_CLIENT_SECRET=dein_client_secret_hier
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

## 4. Anwendung starten

```bash
python playlist_builder.py
```

Beim ersten Start öffnet sich ein Browserfenster zum Spotify-Login (OAuth).
Nach der Anmeldung wird das Access-Token in `.cache` gespeichert, sodass du
dich bei weiteren Läufen nicht erneut anmelden musst.

## Funktionsweise

- `get_or_create_playlist`: Sucht nach einer vorhandenen Playlist
  "VISIO XXL" im eigenen Account oder erstellt sie neu.
- `collect_new_tracks`: Durchsucht Spotify reihum nach den vier Genres und
  filtert bereits bekannte Track-IDs heraus.
- `added_tracks.json`: Persistiert alle bereits hinzugefügten Track-IDs,
  damit auch nach einem Neustart keine Duplikate entstehen.
- Die Hauptschleife fügt pro Durchgang bis zu 100 neue Songs hinzu, bis die
  Playlist 10.000 Songs erreicht hat oder keine neuen Songs mehr gefunden
  werden.

## Wichtiger Hinweis zur Song-Anzahl

Die Spotify-Such-API begrenzt die Ergebnisse pro Suchanfrage auf einen
maximalen Offset von 1000 Treffern pro Suchbegriff. Bei vier Genres können
über die reine Genre-Suche realistisch nur einige tausend eindeutige Songs
gefunden werden, nicht garantiert 10.000. Das Skript bricht automatisch ab
und gibt eine Meldung aus, falls keine weiteren neuen Songs mehr gefunden
werden, bevor das Ziel erreicht ist. Falls du mehr Songs benötigst, kannst
du die Liste `GENRES` in `playlist_builder.py` um weitere Genres oder
Suchbegriffe (z. B. Subgenres, Künstler, Jahreszahlen) erweitern.
