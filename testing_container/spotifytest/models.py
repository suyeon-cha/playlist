from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    Extended User model for storing Spotify-related information
    """
    spotify_token = models.CharField(max_length=255, blank=True, null=True)
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)
    liked_playlists = models.ManyToManyField('Playlist', related_name='liked_by', blank=True)
    
    # Fix the clash by adding custom related_name parameters
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='spotifytest_user_set',  # Custom related_name
        related_query_name='user',
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='spotifytest_user_set',  # Custom related_name
        related_query_name='user',
    )

    def __str__(self):
        return self.username


class Song(models.Model):
    """
    Model to store song information
    """
    spotify_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    album = models.CharField(max_length=255, blank=True, null=True)
    duration_ms = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.title} - {self.artist}"


class Playlist(models.Model):
    """
    Model for completed playlists
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_playlists')
    collaborators = models.ManyToManyField(User, related_name='collaborated_playlists', blank=True)
    songs = models.ManyToManyField(Song, related_name='playlists', blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_public = models.BooleanField(default=True)
    
    # Likes are tracked via the ManyToManyField in User (liked_playlists)
    
    def __str__(self):
        return self.name
    
    @property
    def likes_count(self):
        return self.liked_by.count()


class PlaylistDraft(models.Model):
    """
    Model for playlists under creation (before voting)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='draft_playlists')
    collaborators = models.ManyToManyField(User, related_name='collaborated_drafts', blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_voting_complete = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Draft: {self.name}"
    
    def finalize_playlist(self):
        """
        Creates a final Playlist from this draft after voting is complete
        """
        if not self.is_voting_complete:
            return None
        
        # Get top voted songs
        top_songs = [vote.song for vote in self.votes.order_by('-vote_count')]
        
        # Create the final playlist
        playlist = Playlist.objects.create(
            name=self.name,
            owner=self.owner
        )
        
        # Add collaborators
        playlist.collaborators.set(self.collaborators.all())
        
        # Add songs
        playlist.songs.set(top_songs)
        
        return playlist


class SongSuggestion(models.Model):
    """
    Model for songs suggested by collaborators for a draft playlist
    """
    playlist_draft = models.ForeignKey(PlaylistDraft, on_delete=models.CASCADE, related_name='suggestions')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    suggested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    suggested_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('playlist_draft', 'song')
    
    def __str__(self):
        return f"{self.song.title} suggested by {self.suggested_by.username}"


class SongVote(models.Model):
    """
    Model to track voting on songs in a draft playlist
    """
    playlist_draft = models.ForeignKey(PlaylistDraft, on_delete=models.CASCADE, related_name='votes')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    vote_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('playlist_draft', 'song')
    
    def __str__(self):
        return f"{self.song.title}: {self.vote_count} votes"


class Vote(models.Model):
    """
    Model to track individual votes
    """
    song_vote = models.ForeignKey(SongVote, on_delete=models.CASCADE, related_name='voters')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('song_vote', 'user')
    
    def __str__(self):
        return f"{self.user.username} voted for {self.song_vote.song.title}"