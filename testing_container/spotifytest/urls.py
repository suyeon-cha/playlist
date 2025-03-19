from django.urls import path
from spotifytest import views

urlpatterns = [
    path('spotify-login', views.spotify_login, name='spotify-login'),
    path('', views.home, name='home'),
    path('callback/', views.spotify_callback, name='spotify-callback'),
]
