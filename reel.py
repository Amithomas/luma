# reel.py

import yt_dlp
import os
import cv2
import tempfile
import base64
from faster_whisper import WhisperModel

# Load Whisper once when app starts
WHISPER_MODEL = WhisperModel("base", device="cpu", compute_type="int8")


def process_reel(url):
    print("⬇️ Downloading reel...")
    video_path, temp_dir = download_reel(url)

    print("🎞️ Extracting frames...")
    frames = extract_frames(video_path)

    print("🎤 Transcribing audio...")
    transcript = transcribe_audio(video_path)

    print("🧹 Cleaning up...")
    cleanup(temp_dir)

    return {
        "transcript": transcript,
        "frames": frames
    }


def download_reel(url):
    # Create a temporary directory that auto-deletes when done
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "reel.mp4")

    ydl_opts = {
        "outtmpl": output_path,
        "format": "best[ext=mp4]/best",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path, temp_dir


def extract_frames(video_path, interval_seconds=5):
    frames = []

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / fps

    # Extract one frame every interval_seconds
    current_second = 0
    while current_second < duration:
        # Jump to the right frame
        cap.set(cv2.CAP_PROP_POS_MSEC, current_second * 1000)
        success, frame = cap.read()

        if success:
            # Convert frame to base64 string
            _, buffer = cv2.imencode(".jpg", frame)
            frame_base64 = base64.b64encode(buffer).decode("utf-8")
            frames.append(frame_base64)

        current_second += interval_seconds

    cap.release()
    return frames


def transcribe_audio(video_path):
    segments, info = WHISPER_MODEL.transcribe(
        video_path,
        beam_size=5,
        language="en"
    )

    transcript = " ".join([segment.text for segment in segments])
    return transcript.strip()

def cleanup(temp_dir):
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)