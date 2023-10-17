import spotipy
import time 

from spotipy.oauth2 import SpotifyOAuth # Used for authorizing user
from flask import Flask, request, url_for, session, redirect    # Used to store user info and redirecting to various pages

# Create flask object
app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = "Spotify Cookie"
app.secret_key = "jf4543nj;p345_232**"
TOKEN_INFO = "token_info"

@app.route('/')
def login():
    # Redirect user to spotify login authorization
    auth_url = create_spotify_oauth().get_authorize_url()   # Generate authorization link by using create_spotify_oauth() function
    return redirect(auth_url)   # Redirect user to authorization URL

@app.route('/redirect')
def redirect_page():
    session.clear() # Clear previous user's session
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code) # Exchange authorization code for token
    session[TOKEN_INFO] = token_info # Saving the session's token info
    return redirect(url_for("save_discover_weekly", external = True)) # Redirect to app

@app.route('/saveDiscoverWeekly')
def save_discover_weekly():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect("/")

    sp = spotipy.Spotify(auth=token_info["access_token"])
    saved_weekly_playlist_id = None
    discover_weekly_playlist_id = None

    current_playlists = sp.current_user_playlists()["items"]    # Get all of user's playlists
    # Search for Discover Weekly or Saved Weekly
    for playlist in current_playlists:
        if(playlist["name"] == "Discover Weekly"):
            discover_weekly_playlist_id = playlist["id"]
        if(playlist["name"] == "Saved Weekly"):
            saved_weekly_playlist_id = playlist["id"]
        
        # If Discover Weekly not found
        if not discover_weekly_playlist_id:
            return "Discover Weekly not found"
        if not saved_weekly_playlist_id:
            new_playlist = sp.user_playlist_create(user_id, "Saved Weekly", True)
            saved_weekly_playlist_id = new_playlist["id"]
        
        discover_weekly_playlist = sp.play_items(discover_weekly_playlist_id)
        song_uris = []
        for song in discover_weekly_playlist["items"]:  # Add all songs from Discover Weekly into a list
            song_uri = song["track"]["uri"]
            song_uris.append(song_uri)
        user_id = sp.current_user()["id"]
        sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uri)

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for("login", external=False))  # If authorization fails
    
    now = int(time.time())  # Get current time
    is_expired = token_info["expires_at"] - now < 60    # Make sure token doesn't expire in the next 60 seconds
    # If token is expired or about to expire
    if (is_expired):
        # Repeat OAuth processs and refresh token from previous
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info["refresh_token"])
    return token_info

# Encode app scope request to be sent to Spotify
def create_spotify_oauth():
    return SpotifyOAuth(client_id = "11d7bef2f04d4c41a76963172a2ca580", # Set up client id
                        client_secret = "94a0a26130c1467ba471ef2c58eef5a8", # Set up client secret
                        redirect_uri = url_for('redirect_page', _external= True),    # Set the redirect url to be absolute (full domain)
                        scope = "user-library-read playlist-modify-public playlist-modify-private"  # Defining which funcitonalities we will need
                        )

app.run(debug=True)