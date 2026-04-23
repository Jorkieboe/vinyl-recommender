import webview
import os
import shutil
from dotenv import load_dotenv
from backend.bridge import Bridge
from backend.database import Database
from backend.logger import logger

def check_ffmpeg():
    if not shutil.which('ffmpeg'):
        logger.warning("WARNING: ffmpeg not found. Librosa analysis will fail.")
        return False
    return True

def main():
    # Load environment variables from .env
    load_dotenv()

    check_ffmpeg()

    # Ensure DB is initialized before starting
    Database().init_db()

    bridge = Bridge()

    # In development, Vite runs on 5173 by default
    # Use environment variable to toggle dev/prod mode
    is_dev = os.getenv('PYWEBVIEW_DEV', 'true').lower() == 'true'

    if is_dev:
        url = 'http://localhost:5173'
    else:
        # Resolve path to the built frontend
        current_dir = os.path.dirname(os.path.abspath(__file__))
        url = os.path.join(current_dir, '..', 'frontend', 'dist', 'index.html')
        if not os.path.exists(url):
            logger.error(f"Error: Production build not found at {url}")
            # Fallback to dev for safety during early stages
            url = 'http://localhost:5173'

    window = webview.create_window(
        'Vinyl Recommender',
        url,
        js_api=bridge,
        width=1200,
        height=800,
        background_color='#111827'
    )

    webview.start(debug=is_dev)

if __name__ == '__main__':
    main()