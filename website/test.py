import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

scope = "playlist-modify-public"
username = "bilge;"

SPOTIFY_CLIENT_ID = "e8428daa81a645c79bd69599c62ca09b"
SPOTIFY_CLIENT_SECRET = "ad668440ec204f93bb23c2a92896c988"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8081/"

ACCESS_TOKEN = SpotifyOAuth(scope=scope, username=username, client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=SPOTIFY_REDIRECT_URI)

spotifyObject = spotipy.Spotify(auth_manager=ACCESS_TOKEN)



sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="e8428daa81a645c79bd69599c62ca09b",
                                               client_secret="ad668440ec204f93bb23c2a92896c988",
                                               redirect_uri="http://127.0.0.1:8081/",
                                               scope="user-library-read playlist-modify-public"))

results = sp.current_user_saved_tracks()
for idx, item in enumerate(results['items']):
    track = item['track']
    print(idx, track['artists'][0]['name'], " – ", track['name'])




results = sp.search(q='Karsu', limit=20)
for idx, track in enumerate(results['tracks']['items']):
    print(idx, track['name'])

music_search_input=input("Hello:")
results = sp.search(q=music_search_input, limit=20)
for idx, track in enumerate(results['tracks']['items']):
    print(track['name'])