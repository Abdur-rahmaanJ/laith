"""
Example: File Download and Upload with Progress

Download and upload files with optional progress callbacks.

Usage:
    # Download a file
    path = http.download("https://example.com/file.zip", "/local/file.zip")

    # Upload a file
    resp = http.upload("https://example.com/upload", "/local/file.txt")

    # With progress callback
    def on_progress(pct):
        print(f"Progress: {pct}%")

    http.download("https://example.com/video.mp4", "/local/video.mp4",
                  on_progress=on_progress)

    http.upload("https://example.com/upload", "/local/photo.jpg",
                on_progress=on_progress)
"""

def on_progress(pct):
    print(f"Progress: {pct}%")

def main_ui():
    path = http.download("https://example.com/video.mp4", "/sdcard/video.mp4",
                         on_progress=on_progress)
    Text(f"Downloaded to {path}")
