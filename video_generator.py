from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
import re
import logging
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_subtitled_video(audio_path, transcription, output_path, chunk_duration=60):
    try:
        logger.info(f"Starting video generation with audio: {audio_path}")
        
        # Load audio
        audio = AudioFileClip(audio_path)
        
        # Create a black background video
        video = ColorClip(size=(640, 480), color=(0,0,0)).set_duration(audio.duration).set_audio(audio)
        
        # Parse SRT content
        subtitles = parse_srt(transcription)
        
        # Process video in chunks
        chunk_paths = []
        for i, chunk_start in enumerate(range(0, int(audio.duration), chunk_duration)):
            chunk_end = min(chunk_start + chunk_duration, audio.duration)
            logger.info(f"Processing chunk {i+1}: {chunk_start} - {chunk_end}")
            
            chunk_video = video.subclip(chunk_start, chunk_end)
            chunk_subtitles = [s for s in subtitles if chunk_start <= s[0] < chunk_end]
            
            subtitle_clips = []
            for start, end, text in chunk_subtitles:
                text_clip = (TextClip(text, fontsize=24, color='white', font='Arial', method='caption', size=video.size)
                             .set_position(('center', 'bottom'))
                             .set_duration(end - start)
                             .set_start(start - chunk_start))
                subtitle_clips.append(text_clip)
            
            final_chunk = CompositeVideoClip([chunk_video] + subtitle_clips)
            
            chunk_path = tempfile.mktemp(suffix=f"_chunk_{i}.mp4")
            final_chunk.write_videofile(
                chunk_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                ffmpeg_params=['-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2']
            )
            chunk_paths.append(chunk_path)
        
        # Concatenate chunks
        logger.info("Concatenating video chunks")
        from moviepy.editor import concatenate_videoclips
        final_clips = [VideoFileClip(path) for path in chunk_paths]
        final_video = concatenate_videoclips(final_clips)
        
        # Write final output video file
        logger.info("Writing final video file")
        try:
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                ffmpeg_params=['-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2']
            )
            logger.info(f"Video successfully written to {output_path}")
        except Exception as e:
            logger.error(f"Error writing video file: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"An error occurred during video generation: {str(e)}")
        raise
    finally:
        # Clean up temporary chunk files
        for path in chunk_paths:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Removed temporary chunk file: {path}")

def parse_srt(srt_content):
    pattern = r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)\n((?:(?!\n\n).|\n)*)'
    matches = re.findall(pattern, srt_content, re.DOTALL)
    
    def time_to_seconds(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    
    return [(time_to_seconds(start), time_to_seconds(end), text.strip()) for start, end, text in matches]
