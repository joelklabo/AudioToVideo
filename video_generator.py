import cv2
import numpy as np
import os
from moviepy.editor import VideoFileClip, AudioFileClip

def create_subtitled_video(
    audio_path,
    transcription,
    output_video_path,
    bg_color=(0, 0, 0),
    font_color=(255, 255, 255),
    title=None,
    byline=None
):
    # Video parameters
    fps = 30
    width, height = 1280, 720

    # Convert colors from RGB to BGR for OpenCV
    bg_color_bgr = (bg_color[2], bg_color[1], bg_color[0])
    font_color_bgr = (font_color[2], font_color[1], font_color[0])

    # Get audio duration
    duration = get_audio_duration(audio_path)
    total_frames = int(duration * fps)

    # Create a blank video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Prepare subtitles
    subtitles = prepare_subtitles(transcription, duration)

    # Font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    title_font_scale = 2.0
    byline_font_scale = 1.0
    subtitle_font_scale = 1.5
    font_thickness = 2

    # Generate frames
    for frame_number in range(total_frames):
        # Create background image
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:, :] = bg_color_bgr  # Set background color

        # Calculate current time
        current_time = frame_number / fps

        # Add title
        if title:
            text_size, _ = cv2.getTextSize(title, font, title_font_scale, font_thickness)
            x = int((width - text_size[0]) / 2)
            y = int(height * 0.1)
            cv2.putText(img, title, (x, y), font, title_font_scale, font_color_bgr, font_thickness, cv2.LINE_AA)

        # Add byline
        if byline:
            text_size, _ = cv2.getTextSize(byline, font, byline_font_scale, font_thickness)
            x = width - text_size[0] - 50
            y = height - 50
            cv2.putText(img, byline, (x, y), font, byline_font_scale, font_color_bgr, font_thickness, cv2.LINE_AA)

        # Add subtitle
        subtitle_text = get_current_subtitle(subtitles, current_time)
        if subtitle_text:
            text_size, _ = cv2.getTextSize(subtitle_text, font, subtitle_font_scale, font_thickness)
            x = int((width - text_size[0]) / 2)
            y = int((height + text_size[1]) / 2)
            cv2.putText(img, subtitle_text, (x, y), font, subtitle_font_scale, font_color_bgr, font_thickness, cv2.LINE_AA)

        # Write frame to video
        video_writer.write(img)

    video_writer.release()

    # Add audio to video
    add_audio_to_video(output_video_path, audio_path)

def get_audio_duration(audio_path):
    from mutagen.mp3 import MP3
    from mutagen.wave import WAVE
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis

    ext = os.path.splitext(audio_path)[1].lower()
    if ext == '.mp3':
        audio = MP3(audio_path)
    elif ext == '.wav':
        audio = WAVE(audio_path)
    elif ext == '.m4a':
        audio = MP4(audio_path)
    elif ext == '.ogg':
        audio = OggVorbis(audio_path)
    else:
        raise ValueError(f"Unsupported audio format: {ext}")
    return audio.info.length

def prepare_subtitles(transcription, duration):
    import re
    lines = transcription.strip().split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove timestamps and special characters
        cleaned_line = re.sub(r'\[.*?\]', '', line)  # Remove text in square brackets
        cleaned_line = re.sub(r'\d{2}:\d{2}:\d{2}.*', '', cleaned_line)  # Remove timestamps
        cleaned_line = cleaned_line.strip()

        # Remove standalone numbers (line numbers)
        if cleaned_line.isdigit():
            continue  # Skip lines that are just numbers

        # Remove empty lines
        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    # Split transcription into subtitles based on punctuation or length
    subtitles = split_into_subtitles(cleaned_lines, duration)

    return subtitles

def split_into_subtitles(cleaned_lines, duration):
    import math

    # Combine all cleaned lines into one text
    full_text = ' '.join(cleaned_lines)

    # Split text into sentences using punctuation
    import nltk
    nltk.download('punkt', quiet=True)
    from nltk.tokenize import sent_tokenize

    sentences = sent_tokenize(full_text)

    # Calculate time per subtitle based on the number of sentences
    total_subtitles = len(sentences)
    time_per_subtitle = duration / total_subtitles if total_subtitles > 0 else duration

    subtitles = []
    current_time = 0.0
    for sentence in sentences:
        subtitles.append({
            'start': current_time,
            'end': current_time + time_per_subtitle,
            'text': sentence.strip()
        })
        current_time += time_per_subtitle

    return subtitles

def get_current_subtitle(subtitles, current_time):
    for subtitle in subtitles:
        if subtitle['start'] <= current_time < subtitle['end']:
            return subtitle['text']
    return ''

def add_audio_to_video(video_path, audio_path):
    from moviepy.editor import VideoFileClip, AudioFileClip
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile("temp_video_with_audio.mp4", codec="libx264", audio_codec='aac')
    final_clip.close()
    video_clip.close()
    audio_clip.close()
    os.replace("temp_video_with_audio.mp4", video_path)
