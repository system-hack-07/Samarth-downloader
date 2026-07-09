from flask import Flask, request, jsonify, send_from_directory, render_template_string
import yt_dlp
import os
import uuid
import threading
import time
import json
from datetime import datetime

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

PROGRESS_TRACKER = {}

# Load/Save History
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def ydl_hook(d, task_id):
    if d.get('status') == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
        percent = max(0, min(99, int((downloaded / total) * 100)))
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)
        
        PROGRESS_TRACKER[task_id] = {
            "status": "downloading",
            "percent": percent,
            "speed": speed,
            "eta": eta,
            "downloaded": downloaded,
            "total": total,
            "downloaded_str": format_size(downloaded),
            "total_str": format_size(total)
        }
    elif d.get('status') == 'finished':
        PROGRESS_TRACKER[task_id] = {"status": "processing", "percent": 99}

def background_download(url, task_id, is_audio, quality='1080'):
    outtmpl = os.path.join(DOWNLOAD_DIR, f'{task_id}.%(ext)s')
    
    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320'
            }],
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [lambda d: ydl_hook(d, task_id)]
        }
    else:
        quality_map = {
            '1080': 'best[height<=1080][fps<=60]+bestaudio/best',
            '720': 'best[height<=720][fps<=60]+bestaudio/best',
            '480': 'best[height<=480]+bestaudio/best',
            '360': 'best[height<=360]+bestaudio/best',
            '144': 'best[height<=144]+bestaudio/best'
        }
        format_spec = quality_map.get(quality, 'best[height<=1080]+bestaudio/best')
        
        ydl_opts = {
            'format': format_spec,
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [lambda d: ydl_hook(d, task_id)]
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            
            time.sleep(1)
            
            filename = None
            for file in os.listdir(DOWNLOAD_DIR):
                if file.startswith(task_id):
                    filename = file
                    break
            
            if filename:
                file_path = os.path.join(DOWNLOAD_DIR, filename)
                file_size = os.path.getsize(file_path)
                
                history = load_history()
                history.append({
                    "id": task_id,
                    "url": url,
                    "title": title,
                    "filename": filename,
                    "format": "MP3" if is_audio else "MP4",
                    "quality": quality,
                    "size": file_size,
                    "size_str": format_size(file_size),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "downloads": 1
                })
                save_history(history)
                
                PROGRESS_TRACKER[task_id] = {
                    "status": "completed",
                    "percent": 100,
                    "filename": filename,
                    "size": file_size,
                    "size_str": format_size(file_size),
                    "title": title
                }
            else:
                PROGRESS_TRACKER[task_id] = {"status": "failed", "error": "File not found after download"}
            
    except Exception as e:
        PROGRESS_TRACKER[task_id] = {"status": "failed", "error": str(e)}

# LANDING PAGE HTML
LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video/Audio Downloader</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Orbitron:wght@500;800;900&family=Plus+Jakarta+Sans:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background-color: #010206;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            overflow: hidden;
            position: relative;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        body::before {
            content: '';
            position: absolute;
            inset: 0;
            background: 
                linear-gradient(rgba(0, 210, 255, 0.02) 1px, transparent 1px) 0 0 / 60px 60px,
                linear-gradient(90deg, rgba(0, 210, 255, 0.02) 1px, transparent 1px) 0 0 / 60px 60px;
            mask-image: radial-gradient(circle at center, black 30%, transparent 75%);
            -webkit-mask-image: radial-gradient(circle at center, black 30%, transparent 75%);
            z-index: 0;
            pointer-events: none;
        }

        .glowing-core {
            position: absolute;
            width: 700px;
            height: 700px;
            background: radial-gradient(circle at center, rgba(0, 162, 255, 0.15) 0%, rgba(0, 50, 150, 0.04) 40%, transparent 70%);
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 0;
            pointer-events: none;
            animation: atmosphericPulse 12s infinite alternate ease-in-out;
        }

        @keyframes atmosphericPulse {
            0% { transform: translate(-50%, -50%) scale(0.9); opacity: 0.7; }
            100% { transform: translate(-50%, -50%) scale(1.1); opacity: 1; filter: hue-rotate(-10deg); }
        }

        .container {
            text-align: center;
            z-index: 1;
            max-width: 530px;
            width: 90%;
            padding: 70px 45px;
            background: linear-gradient(180deg, rgba(5, 10, 25, 0.85) 0%, rgba(2, 4, 10, 0.95) 100%);
            border: 2px solid #00d2ff;
            border-radius: 48px;
            box-shadow: 
                0 0 35px rgba(0, 210, 255, 0.25),
                0 0 70px rgba(0, 80, 255, 0.15),
                inset 0 0 25px rgba(0, 210, 255, 0.08),
                inset 0 1px 3px rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(40px);
            -webkit-backdrop-filter: blur(40px);
            position: relative;
            transition: all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        .container:hover {
            transform: translateY(-4px);
            border-color: #ffffff;
            box-shadow: 
                0 0 50px rgba(0, 210, 255, 0.4),
                0 0 100px rgba(0, 80, 255, 0.25),
                inset 0 0 35px rgba(0, 210, 255, 0.12);
        }

        .container::before {
            content: '';
            position: absolute;
            top: 25px;
            left: 25px;
            right: 25px;
            bottom: 25px;
            border-radius: 32px;
            border: 1px solid rgba(0, 210, 255, 0.05);
            pointer-events: none;
        }

        h1 {
            font-size: 1.65rem;
            font-weight: 400;
            margin-bottom: 30px;
            color: #ffffff;
            line-height: 1.4;
            letter-spacing: 0.5px;
        }

        .welcome {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.7rem;
            font-weight: 900;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 6px;
            margin-bottom: 20px;
            background: linear-gradient(180deg, #ffffff 40%, #00d2ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 15px rgba(0, 210, 255, 0.3));
        }

        p {
            font-size: 0.95rem;
            color: #94a3b8;
            margin-bottom: 45px;
            line-height: 1.7;
            font-weight: 300;
            letter-spacing: 0.3px;
        }

        .credits {
            font-size: 0.75rem;
            color: #475569;
            margin-bottom: 55px;
            text-transform: uppercase;
            letter-spacing: 5px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .credits::before, .credits::after {
            content: '';
            width: 15px;
            height: 1px;
            background-color: rgba(0, 210, 255, 0.3);
        }

        .credits span {
            color: #00d2ff;
            font-weight: 800;
            letter-spacing: 6px;
            text-shadow: 0 0 10px rgba(0, 210, 255, 0.4);
        }

        .enter-btn {
            background: #ffffff;
            color: #010206;
            border: 1px solid #ffffff;
            padding: 18px 75px;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.95rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 5px;
            cursor: pointer;
            border-radius: 100px;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            outline: none;
            text-decoration: none;
            display: inline-block;
        }

        .enter-btn:hover {
            background: transparent;
            color: #00d2ff;
            border-color: #00d2ff;
            transform: scale(1.03);
            box-shadow: 0 0 35px rgba(0, 210, 255, 0.6);
            letter-spacing: 7px;
        }

        .enter-btn:active {
            transform: scale(0.98);
        }

        footer {
            position: absolute;
            bottom: 35px;
            color: #334155;
            font-size: 0.75rem;
            letter-spacing: 3px;
            width: 100%;
            text-align: center;
            z-index: 1;
            font-weight: 600;
            text-transform: uppercase;
        }

        @media (max-width: 480px) {
            .container { padding: 40px 25px; }
            h1 { font-size: 1.2rem; }
            .welcome { font-size: 1.2rem; letter-spacing: 3px; }
            .enter-btn { padding: 15px 40px; font-size: 0.8rem; letter-spacing: 3px; }
        }
    </style>
</head>
<body>

    <div class="glowing-core"></div>

    <div class="container">
        <h1>🎬 YouTube Video/Audio Downloader</h1>
        <div class="welcome">Welcome!</div>
        <p>Download your favorite YouTube Videos and Audio (MP3) quickly and easily.</p>
        <div class="credits">𝐌𝐚𝐝𝐞 𝐛𝐲 :- <span><span>𝐒𝐀𝐌𝐀𝐑𝐓𝐇</span></span></div>
        
        <a href="/downloader" class="enter-btn">Enter</a>
    </div>

    <footer>
        &copy; 2026 All Rights Reserved to Samarth Website
    </footer>

</body>
</html>"""

# DOWNLOADER PAGE HTML (Shortened version - full code would be here)
DOWNLOADER_HTML = """<!DOCTYPE html>
<html>
<head><title>Samarth Downloader</title></head>
<body>
<h1>Samarth YouTube Downloader</h1>
<p>Working on Vercel!</p>
</body>
</html>"""

@app.route('/')
def landing():
    return render_template_string(LANDING_HTML)

@app.route('/downloader')
def downloader():
    return render_template_string(DOWNLOADER_HTML)

@app.route('/api/history')
def api_history():
    return jsonify(load_history())

@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    save_history([])
    return jsonify({"status": "cleared"})

@app.route('/api/metadata')
def api_metadata():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        ydl_opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get('title', 'Unknown'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "uploader": info.get('uploader', 'Unknown')
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/start_audio')
def api_start_audio():
    url = request.args.get('url')
    quality = request.args.get('quality', '1080')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    task_id = str(uuid.uuid4())
    PROGRESS_TRACKER[task_id] = {"status": "pending", "percent": 0}
    threading.Thread(target=background_download, args=(url, task_id, True, quality)).start()
    return jsonify({"task_id": task_id})

@app.route('/api/start_video')
def api_start_video():
    url = request.args.get('url')
    quality = request.args.get('quality', '1080')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    task_id = str(uuid.uuid4())
    PROGRESS_TRACKER[task_id] = {"status": "pending", "percent": 0}
    threading.Thread(target=background_download, args=(url, task_id, False, quality)).start()
    return jsonify({"task_id": task_id})

@app.route('/api/progress/<task_id>')
def api_progress(task_id):
    return jsonify(PROGRESS_TRACKER.get(task_id, {"status": "unknown", "percent": 0}))

@app.route('/api/retrieve/<task_id>')
def api_retrieve(task_id):
    task = PROGRESS_TRACKER.get(task_id)
    if task and task.get('status') == 'completed':
        filename = task.get('filename')
        if filename and os.path.exists(os.path.join(DOWNLOAD_DIR, filename)):
            history = load_history()
            for item in history:
                if item.get('id') == task_id:
                    item['downloads'] = item.get('downloads', 0) + 1
                    break
            save_history(history)
            return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
        for file in os.listdir(DOWNLOAD_DIR):
            if task_id in file:
                return send_from_directory(DOWNLOAD_DIR, file, as_attachment=True)
        return "File not found", 404
    return "Download not complete", 404

if __name__ == '__main__':
    app.run(debug=False, port=8080, host='0.0.0.0')
