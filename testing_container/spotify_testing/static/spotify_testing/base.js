document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("open-playlist-button");
    if (!btn) return;
  
    btn.addEventListener("click", async () => {
      console.log("button press");
  
      // 🔍 Collect track URIs from the DOM
      const songElements = document.querySelectorAll(".song-information");
      const uris = Array.from(songElements).map(el => el.dataset.uri);
  
      try {
        const response = await fetch("/create_spotify_playlist/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({ uris })
        });
  
        const data = await response.json();
        if (data.playlist_url) {
          window.location.href = data.playlist_url;
        } else {
          alert("Failed to create playlist.");
        }
      } catch (err) {
        console.error(err);
        alert("Something went wrong.");
      }
    });
  
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === name + "=") {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  });
  