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

def create_subtitled_video(audio_path, transcription, output_path, bg_color=(0,0,0), title=None, byline=None):
    try:
        logger.info(f"Starting video generation with audio: {audio_path}")
        
        # Load audio
        audio = AudioFileClip(audio_path)
        logger.info(f"Audio duration: {audio.duration:.2f} seconds")
        
        # Create a background video with the specified color
        video = ColorClip(size=(1280, 720), color=bg_color).set_duration(audio.duration)
        
        # Parse SRT content
        subtitles = parse_srt(transcription)
        logger.info(f"Parsed {len(subtitles)} subtitles")
        
        clips = [video]

        # Find a system font
        system_fonts = [
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
            'C:\\Windows\\Fonts\\arial.ttf'  # Windows
        ]
        font = next((f for f in system_fonts if os.path.exists(f)), None)
        
        if font is None:
            logger.warning("No system font found. Using default font.")

        # Add title if provided
        if title:
            title_fontsize = 75  # Change this value to adjust title font size
            logger.info(f"Creating title clip with font size: {title_fontsize}")
            title_clip = (TextClip(title, fontsize=title_fontsize, color='white', font=font, method='label')
                          .set_position(('center', 25))
                          .set_duration(audio.duration))
            clips.append(title_clip)

        # Add byline if provided
        if byline:
            byline_fontsize = 40  # Change this value to adjust byline font size
            logger.info(f"Creating byline clip with font size: {byline_fontsize}")
            byline_clip = (TextClip(byline, fontsize=byline_fontsize, color='white', font=font, method='label')
                           .set_position(('right', 'bottom'))
                           .margin(right=10, bottom=10, opacity=0)
                           .set_duration(audio.duration))
            clips.append(byline_clip)
        
        subtitle_clips = []
        subtitle_fontsize = 50  # Change this value to adjust subtitle font size
        logger.info(f"Creating subtitle clips with font size: {subtitle_fontsize}")
        for i, (start, end, text) in enumerate(subtitles):
            logger.info(f"Creating subtitle {i+1}: {start:.2f} - {end:.2f}: {text}")
            text_clip = (TextClip(text, fontsize=subtitle_fontsize, color='white', font=font, method='label')
                         .set_position('center')
                         .set_start(start)
                         .set_duration(end - start))
            subtitle_clips.append(text_clip)
            logger.info(f"Added subtitle clip {i+1}: start={start:.2f}, end={end:.2f}, duration={text_clip.duration:.2f}")
        
        clips.extend(subtitle_clips)
        final_video = CompositeVideoClip(clips).set_audio(audio)
        logger.info(f"Final video duration: {final_video.duration:.2f}, Number of subtitle clips: {len(subtitle_clips)}")
        
        # Write final output video file
        logger.info("Writing final video file")
        try:
            output_path = output_path.replace('.mov', '.mp4')
            temp_output_path = output_path + ".temp.mp4"
            final_video.write_videofile(
                temp_output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                bitrate='2000k',
                preset='medium',
                ffmpeg_params=[
                    '-vf', 'scale=1280:720',
                    '-pix_fmt', 'yuv420p',
                    '-profile:v', 'baseline',
                    '-level', '3.0',
                    '-movflags', '+faststart',
                    '-ar', '44100',  # Set audio sample rate to 44.1 kHz
                    '-ac', '2'  # Ensure stereo audio
                ]
            )
            
            # Use FFmpeg to remove metadata and ensure compatibility
            os.system(f'ffmpeg -i {temp_output_path} -c copy -map_metadata -1 -movflags +faststart {output_path}')
            os.remove(temp_output_path)
            
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
