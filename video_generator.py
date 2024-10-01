from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.config import change_settings
import re
import logging
import os
from moviepy.config import get_setting

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add this at the beginning of the file
FFMPEG_PATH = "/usr/local/bin/ffmpeg"  # Update this path according to your system
IMAGEMAGICK_BINARY = "/usr/local/bin/convert"  # Update this path according to your system

# Configure MoviePy settings
change_settings({"FFMPEG_BINARY": FFMPEG_PATH, "IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})

# Log the current settings
logger.info(f"FFMPEG_BINARY: {get_setting('FFMPEG_BINARY')}")
logger.info(f"IMAGEMAGICK_BINARY: {get_setting('IMAGEMAGICK_BINARY')}")

def create_subtitled_video(audio_path, transcription, output_path):
    try:
        logger.info(f"Starting video generation with audio: {audio_path}")
        
        # Load audio
        audio = AudioFileClip(audio_path)
        logger.info(f"Audio duration: {audio.duration:.2f} seconds")
        
        # Create a black background video
        video = ColorClip(size=(640, 480), color=(0,0,0)).set_duration(audio.duration)
        
        # Parse SRT content
        subtitles = parse_srt(transcription)
        logger.info(f"Parsed {len(subtitles)} subtitles")
        
        subtitle_clips = []
        for i, (start, end, text) in enumerate(subtitles):
            logger.info(f"Creating subtitle {i+1}: {start:.2f} - {end:.2f}: {text}")
            text_clip = (TextClip(text, fontsize=24, color='white', font='Arial', method='caption', size=video.size)
                         .set_position(('center', 'bottom'))
                         .set_start(start)
                         .set_duration(end - start))
            subtitle_clips.append(text_clip)
            logger.info(f"Added subtitle clip {i+1}: start={start:.2f}, end={end:.2f}, duration={text_clip.duration:.2f}")
        
        final_video = CompositeVideoClip([video] + subtitle_clips).set_audio(audio)
        logger.info(f"Final video duration: {final_video.duration:.2f}, Number of subtitle clips: {len(subtitle_clips)}")
        
        # Write final output video file
        logger.info("Writing final video file")
        try:
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',
                ffmpeg_params=['-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', '-movflags', '+faststart']
            )
            logger.info(f"Video successfully written to {output_path}")
        except Exception as e:
            logger.error(f"Error writing video file: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"An error occurred during video generation: {str(e)}")
        raise

def parse_srt(srt_content):
    # Split the content into individual subtitle entries
    subtitle_entries = re.split(r'\n\n+', srt_content.strip())
    
    subtitles = []
    for entry in subtitle_entries:
        # Split each entry into its components
        parts = entry.split('\n')
        if len(parts) >= 3:  # Ensure we have at least the timing and text
            # Extract timing information
            timing = parts[1]
            start_time, end_time = timing.split(' --> ')
            
            # Convert time to seconds
            start_seconds = time_to_seconds(start_time)
            end_seconds = time_to_seconds(end_time)
            
            # Join the remaining parts as the subtitle text
            text = ' '.join(parts[2:])
            
            subtitles.append((start_seconds, end_seconds, text))
    
    for i, (start, end, text) in enumerate(subtitles):
        logger.info(f"Parsed subtitle {i+1}: {start:.2f} - {end:.2f}: {text}")
    
    return subtitles

def time_to_seconds(time_str):
    hours, minutes, seconds = time_str.replace(',', '.').split(':')
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
