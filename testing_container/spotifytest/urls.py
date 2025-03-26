from django.urls import path
from spotifytest import views

urlpatterns = [
    path('', views.spotify_login, name='spotify-login'),
    path('user-profile/', views.user_profile, name='user-profile'),
    path('playlist-complete/', views.playlist_complete, name='playlist-complete'),
    # path('', views.track_list, name='track-list'),
    path('home/', views.home, name='home'),
    path('callback/', views.spotify_callback, name='spotify-callback'),
    path("create_spotify_playlist/", views.create_spotify_playlist, name="create_spotify_playlist"),
]
