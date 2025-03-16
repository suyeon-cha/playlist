import os
import requests
import random
import string
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import urlencode

def generate_random_string(length=16):
    """Generate a random string for state parameter"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def spotify_login(request):
    """Redirect user to Spotify authorization page"""
    state = generate_random_string(16)
    scope = "user-read-private user-read-email user-library-read"

    query_params = {
        "response_type": "code",
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "scope": scope,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "state": state,
    }

    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(query_params)
    return redirect(auth_url)

def spotify_callback(request):
    print("callback")
    """Handle Spotify's callback and get an access token"""
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not code or not state:
        return JsonResponse({"error": "Authorization failed"}, status=400)

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=payload, headers=headers)
    token_data = response.json()
    print(token_data)

    if "access_token" in token_data:
        return get_saved_tracks(request,token_data)
    else:
        return JsonResponse({"error": "Failed to fetch access token"}, status=400)


def get_saved_tracks(request,token_data):
    """Fetch the user's saved tracks from Spotify"""
    access_token = token_data.get('access_token')  # Retrieve token from session

    if not access_token:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    url = "https://api.spotify.com/v1/me/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if "items" in data:
        print(data)
        return render(request, 'spotify_testing/track_list.html', data)
    else:
        return JsonResponse({"error": "Failed to fetch access token"}, status=400)

    