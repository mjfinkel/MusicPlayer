import yt_dlp
import os
import requests
import sqlite3
import musicbrainzngs
import re


DB_FOLDER = "site/static/resources/sql"
DB_PATH = os.path.join(DB_FOLDER, "songdata.db")


def create_db():
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_FOLDER)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id TEXT primary key,
                title TEXT,
                artist TEXT,
                album TEXT,
                release_year TEXT,
                genre TEXT
            )
            """
        )
        conn.commit()


def store_metadata(song_info):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for song in song_info:
            cursor.execute("SELECT id FROM songs WHERE id = ?", (song["yt_id"],))
            existing_entry = cursor.fetchone()
            if not existing_entry:
                cursor.execute(
                    "INSERT INTO songs (id, title, artist, album, release_year, genre) VALUES (?, ?, ?, ?, ?, ?)", (
                        song["yt_id"],
                        song["title"],
                        song["artist"],
                        song["album"],
                        song["release_year"],
                        song["genre"]
                    )
                )
                conn.commit()


def save_albumcover(album, artist):
    try:
        if not os.path.exists("site/static/resources/images"):
            os.makedirs("site/static/resources/images")
        # safe_filename = "".join(c if c.isalnum() or c in " _-" else "_" for c in album) + ".jpg"
        safe_filename = album + ".jpg"
        file_path = os.path.join("static/resources/images", safe_filename)
        if not os.path.exists(file_path):
            result = musicbrainzngs.search_releases(artist=artist, release=album, limit=1)
            if "release-list" in result and result["release-list"]:
                release = result["release-list"][0]
                mbid = release["id"]
                cover_url = f"https://coverartarchive.org/release/{mbid}/front"
                response = requests.get(cover_url, stream=True)
                if response.status_code == 200:
                    file_path = os.path.join("site/resources/images", f"{safe_filename}")
                    with open(file_path, "wb") as file:
                        for chunk in response.iter_content(1024):
                            file.write(chunk)
                    print(f"MusicBrainz: Album cover downloaded: {file_path}")
                    return file_path
                else:
                    print("MusicBrainz: Album cover not found.")
            else:
                print("MusicBrainz: No album found.")
    except Exception as e:
        print(f"MusicBrainz: Error: {e}")


def get_metadata(title, yt_id):
    url = f"https://itunes.apple.com/search?term={title}&limit=1"
    response = requests.get(url).json()

    if response["resultCount"] > 0:
        track = response["results"][0]
        song_info = {
            "yt_id": yt_id,
            "title": track["trackName"],
            "artist": track["artistName"],
            "album": track["collectionName"],
            "release_year": track["releaseDate"][:4],
            "genre": track["primaryGenreName"],
        }
        # print(song_info['album'])
        save_albumcover(song_info['album'], song_info['artist'])
        return song_info

    return {
        "yt_id": yt_id,
        "title": title,
        "artist": "Unknown",
        "album": "Unknown",
        "release_year": "Unknown",
        "genre": "Unknown",
    }


def download_yt(urls):
    user_audio_dir = 'site/static/resources/audio'
    if not os.path.exists(user_audio_dir):
        os.makedirs(user_audio_dir)

    options = {
        'format': 'bestaudio/best',
        'outtmpl': f'{user_audio_dir}/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        data = []
        for url in urls:
            info = ydl.extract_info(url, download=False)
            original_ext = "mp3"
            sanitized_title = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', info['title'])
            if os.path.exists(os.path.join(user_audio_dir, f"{sanitized_title}.mp3")):
                print(f"Song already downloaded: {info['title']}")
                continue
            info = ydl.extract_info(url, download=True)
            yt_id = url.split("watch?v=")[1].split("&")[0]
            item = get_metadata(info['title'], yt_id)
            data.append(item)
            original_title = info.get("id", "unknown")
            original_filename = os.path.join(user_audio_dir, f"{original_title}.{original_ext}")
            sanitized_title = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', info['title'])
            sanitized_filename = os.path.join(user_audio_dir, f"{sanitized_title}.{original_ext}")
            data[-1]['filename'] = sanitized_filename
            os.rename(original_filename, sanitized_filename)
        store_metadata(data)
        return data


def get_ytlink(query):
    search_url = f"ytsearch:{query}"
    options = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": True
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(search_url, download=False)
        
        if "entries" in info and len(info["entries"]) > 0:
            return info["entries"][0]["url"]
        else:
            return None


def main():
    musicbrainzngs.set_useragent("MusicPlayer", "1.0", "matthewf9236@gmail.com")
    create_db()
    songs = [
        get_ytlink('Hey Jude (Live at Sullivan Stadium, Foxboro, MA 7/2/89)'),
        get_ytlink('Busta Rhymes x Janet Jackson - What Its Gonna Be? (Kaytranada Edition)'),
        get_ytlink('Janet Jackson - If (Kaytranada Remix)'),
        get_ytlink('Hypnotize Biggie Smalls')
    ]
    download_yt(songs)

def add_new(song):
    return download_yt([get_ytlink(song)])[0]['filename'].split('/')[-1]


if __name__ == "__main__":
    main()