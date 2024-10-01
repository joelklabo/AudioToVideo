from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
import re
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_subtitled_video(audio_path, transcription, output_path):
    try:
        logger.info(f"Starting video generation with audio: {audio_path}")
        
        # Load audio
        audio = AudioFileClip(audio_path)
        
        # Create a black background video
        video = ColorClip(size=(640, 480), color=(0,0,0)).set_duration(audio.duration).set_audio(audio)
        
        # Parse SRT content
        subtitles = parse_srt(transcription)
        logger.info(f"Parsed {len(subtitles)} subtitles")
        
        # Log detailed subtitle timings
        for i, (start, end, text) in enumerate(subtitles):
            logger.info(f"Subtitle {i+1}: {start:.2f} - {end:.2f}: {text}")
        
        subtitle_clips = []
        for start, end, text in subtitles:
            logger.info(f"Creating subtitle: {start} - {end}: {text}")
            text_clip = (TextClip(text, fontsize=24, color='white', font='Arial', method='caption', size=video.size)
                         .set_position(('center', 'bottom'))
                         .set_duration(end - start)
                         .set_start(start))
            subtitle_clips.append(text_clip)
        
        final_video = CompositeVideoClip([video] + subtitle_clips)
        
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
    pattern = r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)\n((?:(?!\n\n).|\n)*)'
    matches = re.findall(pattern, srt_content, re.DOTALL)
    
    def time_to_seconds(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    
    subtitles = [(time_to_seconds(start), time_to_seconds(end), text.strip()) for start, end, text in matches]
    return subtitles
