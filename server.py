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
        return jsonify({"status": "error", "error": "No URL provided"}), 400

    url = data["url"]

    # ✅ منع يوتيوب
    if 'youtube.com' in url or 'youtu.be' in url:
        return jsonify({
            "status": "error",
            "error": "YouTube downloads are not supported"
        }), 403

    try:
        # ✅ الخطوة 1: نجيب كل التنسيقات عشان نشوف الوضع
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": "all",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # ✅ نشوف إذا فيه فيديو كامل (صوت مدمج)
            has_complete_format = False
            for f in info.get("formats", []):
                if (f.get("vcodec") and f.get("vcodec") != "none" and
                    f.get("acodec") and f.get("acodec") != "none"):
                    has_complete_format = True
                    break

        # ✅ الخطوة 2: نختار الإعدادات المناسبة
        if has_complete_format:
            # ✅ فيه فيديو كامل (صوت مدمج) → نجيبه مباشرة
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "format": "best[ext=mp4]/best",
            }
        else:
            # ✅ مافيه فيديو كامل → ندمج الفيديو مع الصوت
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            }

        # ✅ الخطوة 3: نستخرج المعلومات ونبني الـ formats
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = []
            seen_qualities = set()

            for f in info.get("formats", []):
                if f.get("vcodec") and f.get("vcodec") != "none":
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
                            "ext": "mp4",
                            "url": f.get("url"),
                            "filesize": f.get("filesize") or 0,
                        })

            formats.sort(key=lambda x: x["height"], reverse=True)

            return jsonify({
                "status": "success",
                "title": info.get("title", ""),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "formats": formats,
                "merged": not has_complete_format,  # ✅ نقول للتطبيق إذا كان تم الدمج
            })

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
