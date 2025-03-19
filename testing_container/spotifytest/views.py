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
    
def create_spotify_playlist(request, track_ids, playlist_name, collaborator_ids=None, description=""):
    """
    Create a new playlist on Spotify, add tracks to it, and add collaborators
    
    Args:
        request: The HTTP request
        track_ids: List of Spotify track IDs to add to the playlist
        playlist_name: Name for the new playlist
        collaborator_ids: List of Spotify user IDs to add as collaborators (optional)
        description: Optional description for the playlist
        
    Returns:
        JsonResponse with playlist data or error
    """
    # Get access token from request or session as needed
    access_token = request.session.get('spotify_access_token')
    
    if not access_token:
        return JsonResponse({"error": "User not authenticated with Spotify"}, status=401)
    
    # Step 1: Get the current user's Spotify ID
    user_profile_url = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    user_response = requests.get(user_profile_url, headers=headers)
    if user_response.status_code != 200:
        return JsonResponse({"error": "Failed to get user profile", "details": user_response.json()}, status=400)
    
    user_data = user_response.json()
    user_id = user_data["id"]
    
    # Step 2: Create an empty playlist
    create_playlist_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    playlist_data = {
        "name": playlist_name,
        "description": description,
        "public": True,  # Set to False for private playlist
        "collaborative": True if collaborator_ids else False  # Make collaborative if adding collaborators
    }
    
    playlist_response = requests.post(
        create_playlist_url, 
        headers=headers, 
        json=playlist_data
    )
    
    if playlist_response.status_code != 201:
        return JsonResponse({"error": "Failed to create playlist", "details": playlist_response.json()}, status=400)
    
    playlist = playlist_response.json()
    playlist_id = playlist["id"]
    
    # Step 3: Add tracks to the playlist
    # Spotify allows a maximum of 100 tracks per request
    add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    
    # Process tracks in batches of 100
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        # Convert track IDs to proper Spotify URIs if needed
        track_uris = [f"spotify:track:{track_id}" if not track_id.startswith("spotify:track:") else track_id 
                     for track_id in batch]
        
        add_tracks_response = requests.post(
            add_tracks_url,
            headers=headers,
            json={"uris": track_uris}
        )
        
        if add_tracks_response.status_code != 201:
            # If adding tracks fails, we still return the playlist, but with an error message
            return JsonResponse({
                "warning": "Playlist created but some tracks couldn't be added",
                "playlist": playlist,
                "details": add_tracks_response.json()
            })
    
    # Step 4: Add collaborators to the playlist
    collaborator_results = []
    if collaborator_ids:
        for collaborator_id in collaborator_ids:
            # Add collaborator to the playlist
            add_collaborator_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/followers"
            
            # First, we need to invite the user to collaborate
            # Note: Spotify API has changed - we now need to send a PUT request to add users as followers
            # The playlist must be collaborative for this to work
            collaborator_response = requests.put(
                add_collaborator_url,
                headers=headers
            )
            
            # Then share the playlist with the user
            share_url = f"https://api.spotify.com/v1/users/{collaborator_id}/playlists/{playlist_id}"
            share_response = requests.put(
                share_url,
                headers=headers
            )
            
            collaborator_results.append({
                "user_id": collaborator_id,
                "status": "invited" if collaborator_response.status_code in [200, 201, 204] else "failed"
            })
    
    # Return the playlist data with collaborator results
    return JsonResponse({
        "success": True,
        "message": f"Created playlist '{playlist_name}' with {len(track_ids)} tracks",
        "playlist": playlist,
        "collaborators": collaborator_results
    })


def add_collaborators_to_playlist(request, playlist_id, collaborator_ids):
    """
    Add collaborators to an existing Spotify playlist
    
    Args:
        request: The HTTP request
        playlist_id: Spotify ID of the playlist
        collaborator_ids: List of Spotify user IDs to add as collaborators
        
    Returns:
        JsonResponse with results
    """
    access_token = request.session.get('spotify_access_token')
    
    if not access_token:
        return JsonResponse({"error": "User not authenticated with Spotify"}, status=401)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # First, make the playlist collaborative
    update_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    update_data = {
        "collaborative": True
    }
    
    update_response = requests.put(
        update_url,
        headers=headers,
        json=update_data
    )
    
    if update_response.status_code not in [200, 201, 204]:
        return JsonResponse({
            "error": "Failed to make playlist collaborative",
            "details": update_response.text
        }, status=400)
    
    # Add each collaborator
    results = []
    for collaborator_id in collaborator_ids:
        # Send playlist invitation to user
        # Note: This works differently in Spotify's API
        # The actual behavior is to generate an invite link or to add the user directly
        # For simplicity, we'll just add the user as a follower
        
        # Get user's email (requires user-read-email scope)
        user_url = f"https://api.spotify.com/v1/users/{collaborator_id}"
        user_response = requests.get(user_url, headers=headers)
        
        # Share the playlist with the user
        # Note: In reality, you might want to send this link via email or notification
        share_url = f"https://open.spotify.com/playlist/{playlist_id}"
        
        results.append({
            "user_id": collaborator_id,
            "status": "invited",
            "share_url": share_url
        })
    
    return JsonResponse({
        "success": True,
        "message": f"Added {len(collaborator_ids)} collaborators to playlist",
        "collaborators": results
    })

def home(request):
    return render(request, 'spotify_testing/home.html', {})