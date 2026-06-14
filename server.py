from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "VidSnap API Running"

@app.route("/extract", methods=["POST"])
def extract():
    data = request.get_json(silent=True)

    if not data or "url" not in data:
        return jsonify({
            "status": "error",
            "error": "No URL provided"
        }), 400

    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data["url"], download=False)

            formats = []

            for f in info.get("formats", []):

                # ✅ فيديو + صوت فقط (فيديو كامل)
                if (
                    f.get("url")
                    and f.get("vcodec") != "none"
                    and f.get("acodec") != "none"
                ):

                    formats.append({
                        "quality": f"{f.get('height', 0)}p",
                        "height": f.get("height", 0),
                        "ext": f.get("ext", "mp4"),
                        "url": f.get("url"),
                        "filesize": (
                            f.get("filesize")
                            or f.get("filesize_approx")
                            or 0
                        )
                    })

            formats.sort(
                key=lambda x: x["height"],
                reverse=True
            )

            best_url = formats[0]["url"] if formats else ""

            return jsonify({
                "status": "success",
                "title": info.get("title", ""),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "best_url": best_url,
                "formats": formats
            })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
