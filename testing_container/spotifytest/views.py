import os
import requests
import random
import string
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.conf import settings
from urllib.parse import urlencode
import uuid
from base64 import b64encode

##Redirect user to Spotify authorization page: https://developer.spotify.com/documentation/web-api/tutorials/code-flow
##Button clicked from home page -> Spotify Login 
def spotify_login(request):
    scope = "user-read-private user-read-email user-library-read"
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
def spotify_callback(request):
    print("callback",request.GET)
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

    if "access_token" in token_data:
        return get_saved_tracks(request,token_data)
    else:
        return JsonResponse({"error": "Failed to fetch access token"}, status=400)

##Fetch the user's saved tracks from Spotify: https://developer.spotify.com/documentation/web-api/reference/get-users-saved-tracks 
def get_saved_tracks(request,token_data):
    access_token = token_data.get('access_token')  

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

    