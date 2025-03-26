import json
import os
import requests
import random
import string
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from urllib.parse import urlencode
import uuid
from base64 import b64encode
from django.contrib.auth import login

from spotifytest.models import User

##Redirect user to Spotify authorization page: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
##Button clicked from home page -> Spotify Login 
def spotify_login(request):
    scope = "user-read-private user-read-email user-library-read playlist-modify-private"
    state = uuid.uuid4()
    query_params = {
        "response_type": "code",
        "state": state,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "scope": scope,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(query_params)
    return redirect(auth_url)

##Handle Spotify's callback and get an access token: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
# @login_required

def get_or_create_user(access_token, refresh_token):
    if not access_token:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    url = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    data = response.json()

    if "id" in data:
        print("spotify id",data['id'])
        spotify_id = data['id']

        user, created = User.objects.get_or_create(
            spotify_user_id=spotify_id,
            defaults={
                'username': spotify_id,
                'auth_token': access_token,
                'refresh_token': refresh_token,
                'last_auth_time': timezone.now(),
            }
        )

        user.auth_token = access_token
        user.refresh_token = refresh_token
        user.last_auth_time = timezone.now()
        user.save()
        return user, created
    
    else:
        return None, False

# spotify will always send us here if the account has been connected on attempted login
def spotify_callback(request):
    # print("callback",request.GET)
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not code or not state:
        return JsonResponse({"error": "Authorization failed"}, status=400)

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
    }
    
    encoded = b64encode(f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded}"
    }
    response = requests.post(token_url, data=payload, headers=headers)
    token_data = response.json()

    if "access_token" in token_data and "refresh_token" in token_data:
        user, created = get_or_create_user(
            access_token = token_data.get("access_token"),
            refresh_token = token_data.get("refresh_token")
        )
        if user is None:
            return JsonResponse({"error": "Failed to get or create user"}, status=400)
        
        # if created: 
        #   DIRECT THEM TO THE CHANGE USERNAME SCREEN


        login(request, user)
        return playlist_complete(request)
    
    else:
        return JsonResponse({"error": "Failed to fetch access token"}, status=400)

@login_required
def playlist_complete(request):
    access_token = request.user.auth_token

    if not access_token:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    print(access_token)

    url = "https://api.spotify.com/v1/me/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    print(response)
    data = response.json()

    if "items" in data:
        return render(request, 'spotify_testing/playlist_complete.html', data)
    else:
        return JsonResponse({"error": "Failed to fetch access token"}, status=400)

@login_required
def song_selection(request):
    access_token = request.user.auth_token

    if not access_token:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    print(access_token)

    url = "https://api.spotify.com/v1/me/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    print(response)
    data = response.json()

    if "items" in data:
        return render(request, 'spotify_testing/song_selection.html', data)
    else:
        return JsonResponse({"error": "Failed to fetch access token"}, status=400)

def user_profile(request):
    return render(request, 'spotify_testing/user_profile.html', {})

def home(request):
    return render(request, 'spotify_testing/home.html', {})

def create_playlist(request):
    return render(request, 'spotify_testing/create_playlist.html', {})   

@login_required
def create_spotify_playlist(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    access_token = request.user.auth_token
    if not access_token:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    try:
        body = json.loads(request.body)
        track_uris = body.get("uris", [])
        print("Received track URIs:", track_uris)

        if not track_uris:
            return JsonResponse({"error": "No tracks provided"}, status=400)

    except Exception as e:
        print("JSON parse error:", e)
        return JsonResponse({"error": "Invalid JSON", "details": str(e)}, status=400)

    # Headers for Spotify API
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Get user ID
    user_profile_url = "https://api.spotify.com/v1/me"
    user_resp = requests.get(user_profile_url, headers=headers)
    user_data = user_resp.json()
    user_id = user_data.get("id")

    if not user_id:
        return JsonResponse({"error": "Failed to fetch user ID"}, status=400)

    # Create playlist
    playlist_data = {
        "name": "My Generated Playlist",
        "description": "Created via Django + Spotify API",
        "public": False
    }

    create_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    create_resp = requests.post(create_url, headers=headers, json=playlist_data)
    create_json = create_resp.json()

    playlist_id = create_json.get("id")
    playlist_url = create_json.get("external_urls", {}).get("spotify")

    if not playlist_id:
        print("Playlist creation failed:", create_json)
        return JsonResponse({"error": "Failed to create playlist"}, status=400)

    # Add tracks
    add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    add_resp = requests.post(add_tracks_url, headers=headers, json={"uris": track_uris})

    if add_resp.status_code not in range(200, 299):
        print("Failed to add tracks:", add_resp.text)
        return JsonResponse({"error": "Failed to add tracks"}, status=400)

    return JsonResponse({"playlist_url": playlist_url})