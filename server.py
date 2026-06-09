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

    # ✅ إعدادات yt-dlp لجلب جميع الجودات المتاحة
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # ✅ جلب كل الجودات
        "format": "all",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = []
            seen_qualities = set()

            for f in info.get("formats", []):
                # ✅ نتأكد إنه فيديو (vcodec موجود) وليس صوت فقط
                if f.get("vcodec") and f.get("vcodec") != "none":
                    height = f.get("height", 0)

                    # ✅ نتأكد إن الدقة موجودة
                    if height and height not in seen_qualities:
                        seen_qualities.add(height)

                        # ✅ نحدد اسم الجودة
                        if height >= 1080:
                            quality = "1080p"
                        elif height >= 720:
                            quality = "720p"
                        elif height >= 480:
                            quality = "480p"
                        elif height >= 360:
                            quality = "360p"
                        elif height >= 240:
                            quality = "240p"
                        else:
                            quality = f"{height}p"

                        # ✅ تحديد نوع الملف
                        ext = f.get("ext", "mp4")
                        if ext not in ["mp4", "webm", "mkv"]:
                            ext = "mp4"

                        formats.append({
                            "quality": quality,
                            "height": height,
                            "ext": ext,
                            "filesize": f.get("filesize") or f.get("filesize_approx") or 0,
                            "url": f.get("url"),
                            "format_id": f.get("format_id"),
                            "vcodec": f.get("vcodec")
                        })

            # ✅ نرتب الجودات من الأعلى إلى الأقل
            formats.sort(key=lambda x: x["height"], reverse=True)

            # ✅ البحث عن أفضل رابط MP4
            best_video = None
            for f in formats:
                if f["ext"] == "mp4" and f["height"] >= 360:
                    best_video = f["url"]
                    break

            if best_video is None and formats:
                best_video = formats[0]["url"]

            return jsonify({
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "best_url": best_video,
                "formats": formats,
                "status": "success"
            })

    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)