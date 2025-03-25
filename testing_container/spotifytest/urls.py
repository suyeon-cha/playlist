from django.urls import path
from spotifytest import views

urlpatterns = [
    path('', views.spotify_login, name='spotify-login'),
    # path('', views.user_profile, name='user-profile'),
    # path('', views.playlist_complete, name='playlist-complete'),
    # path('', views.track_list, name='track-list'),
    # path('', views.home, name='home'),
    path('callback/', views.spotify_callback, name='spotify-callback'),
]
