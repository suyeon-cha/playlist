from django.urls import path
from spotifytest import views

urlpatterns = [
    path('', views.spotify_login, name='spotify-login'),
    path('callback/', views.spotify_callback, name='spotify-callback'),
]
