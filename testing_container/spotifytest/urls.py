from django.urls import path
from spotifytest import views

urlpatterns = [
    path('', views.spotify_login, name='spotify-login'),
    path('user-profile/', views.user_profile, name='user-profile'),
    path('playlist-complete/', views.playlist_complete, name='playlist-complete'),
    path('create_playlist/', views.create_playlist, name='create_playlist'),
    # path('', views.track_list, name='track-list'),
    path('song-selection/', views.song_selection, name='song-selection'),
    path('home/', views.home, name='home'),
    path('vote/', views.vote, name='vote'),
    path('callback/', views.spotify_callback, name='spotify-callback'),
    path("create_spotify_playlist/", views.create_spotify_playlist, name="create_spotify_playlist"),
]
