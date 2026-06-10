from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
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

    # ✅ إعدادات yt-dlp الصحيحة لجلب فيديو مع صوت
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = []
            seen_qualities = set()

            for f in info.get("formats", []):
                has_video = f.get("vcodec") and f.get("vcodec") != "none"
                has_audio = f.get("acodec") and f.get("acodec") != "none"
                
                if has_video and has_audio:
                    height = f.get("height", 0)
                    if height and height not in seen_qualities:
                        seen_qualities.add(height)
                        
                        if height >= 1080:
                            quality = "1080p"
                        elif height >= 720:
                            quality = "720p"
                        elif height >= 480:
                            quality = "480p"
                        elif height >= 360:
                            quality = "360p"
                        else:
                            quality = f"{height}p"
                        
                        formats.append({
                            "quality": quality,
                            "height": height,
                            "ext": f.get("ext", "mp4"),
                            "filesize": f.get("filesize") or f.get("filesize_approx") or 0,
                            "url": f.get("url"),
                            "format_id": f.get("format_id"),
                            "vcodec": f.get("vcodec"),
                            "acodec": f.get("acodec")
                        })

            formats.sort(key=lambda x: x["height"], reverse=True)

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
