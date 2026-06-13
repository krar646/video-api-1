from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def home():
    return "Pro Video API is running"

@app.route("/extract", methods=["POST"])
def extract():
    data = request.get_json(silent=True)

    if not data or "url" not in data:
        return jsonify({"error": "No URL provided"}), 400

    url = data["url"]

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "all",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            video_formats = []
            audio_formats = []

            for f in info.get("formats", []):
                has_video = f.get("vcodec") and f.get("vcodec") != "none"
                has_audio = f.get("acodec") and f.get("acodec") != "none"

                if has_video and not has_audio:
                    height = f.get("height", 0)
                    if height > 0:
                        video_formats.append({
                            "quality": f"{height}p" if height >= 360 else f"{height}p",
                            "height": height,
                            "ext": f.get("ext", "mp4"),
                            "url": f.get("url"),
                            "filesize": f.get("filesize") or 0,
                        })

                if not has_video and has_audio:
                    audio_formats.append({
                        "quality": "audio",
                        "ext": f.get("ext", "m4a"),
                        "url": f.get("url"),
                        "filesize": f.get("filesize") or 0,
                    })

            video_formats.sort(key=lambda x: x["height"], reverse=True)

            formats = []
            for v in video_formats:
                best_audio = audio_formats[0] if audio_formats else None
                formats.append({
                    "quality": v["quality"],
                    "height": v["height"],
                    "video_url": v["url"],
                    "audio_url": best_audio["url"] if best_audio else None,
                    "filesize": v["filesize"] + (best_audio["filesize"] if best_audio else 0),
                })

            return jsonify({
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "formats": formats,
                "status": "success"
            })

    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
