from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_subtitled_video(audio_path, transcription, output_path):
    try:
        logging.info(f"Starting video generation with audio: {audio_path}")
        
        # Load audio
        audio = AudioFileClip(audio_path)
        
        # Create a black background video
        video = ColorClip(size=(640, 480), color=(0,0,0)).set_duration(audio.duration).set_audio(audio)
        
        # Parse SRT content
        subtitle_clips = []
        for subtitle in parse_srt(transcription):
            start, end, text = subtitle
            text_clip = (TextClip(text, fontsize=24, color='white', font='Arial', method='caption', size=video.size)
                         .set_position(('center', 'bottom'))
                         .set_duration(end - start)
                         .set_start(start))
            subtitle_clips.append(text_clip)
        
        # Combine video and subtitles
        final_video = CompositeVideoClip([video] + subtitle_clips)
        
        # Write output video file with updated encoding settings
        logging.info("Writing video file with updated encoding settings")
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            ffmpeg_params=['-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2']
        )
        logging.info(f"Video generation completed successfully: {output_path}")
    except Exception as e:
        logging.error(f"An error occurred during video generation: {str(e)}")
        raise

def parse_srt(srt_content):
    pattern = r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)\n((?:(?!\n\n).|\n)*)'
    matches = re.findall(pattern, srt_content, re.DOTALL)
    
    def time_to_seconds(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    
    return [(time_to_seconds(start), time_to_seconds(end), text.strip()) for start, end, text in matches]
