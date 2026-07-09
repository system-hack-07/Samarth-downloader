# 🎬 Samarth YouTube Downloader

A powerful YouTube video and audio downloader built with Flask and yt-dlp.

## ✨ Features

- 🎥 Download YouTube videos in multiple formats (MP4, WEBM)
- 🎵 Extract audio in MP3, M4A formats
- 📱 Mobile-optimized responsive design
- 🌓 Dark/Light theme switching
- 📋 Download history with view counter
- 🎬 Video preview with metadata
- 🔊 Click sound effects
- 🇮🇳 Made by Samarth

## 🚀 Live Demo

[Deployed on Vercel](https://your-vercel-url.vercel.app)

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/system-hack-07/Samarth-downloader.git

# Navigate to project directory
cd Samarth-downloader

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

🌐 Deploy to Vercel

1. Push code to GitHub
2. Go to vercel.com
3. Import your repository
4. Click Deploy

### Docker (recommended for production)

This repository includes a Dockerfile that installs ffmpeg and the Python dependencies and exposes port 8080.

Build and run with Docker:

```bash
docker build -t samarth-downloader .
docker run -p 8080:8080 -v $(pwd)/downloads:/app/downloads --restart unless-stopped samarth-downloader
```

Or using docker-compose:

```bash
docker-compose up -d --build
```

Notes:
- The Docker image installs ffmpeg so audio extraction (MP3) works out of the box.
- Configure MIN_FREE_BYTES and CLEANUP_OLDER_THAN_HOURS via environment variables if needed (see docker-compose.yml).
