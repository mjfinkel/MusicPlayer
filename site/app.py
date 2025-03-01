from flask import Flask, render_template, request, redirect, url_for, jsonify
from main import add_new
import os

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = "site/static/resources/audio"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        songs = []
        return render_template("index.html", songs=songs)

    # main()
    audio_files = os.listdir(app.config["UPLOAD_FOLDER"])
    return render_template("index.html", audio_files=audio_files)


@app.route("/add_song", methods=["POST"])
def add_song():
    song_filename = request.json.get("song_filename")
    if not song_filename:
        return jsonify({"error": "Invalid filename"}), 400

    new_song = add_new(song_filename)  # Call add_new() function to add song
    return jsonify({"success": True, "song_filename": new_song})


if __name__ == "__main__":
    app.run(debug=True)
