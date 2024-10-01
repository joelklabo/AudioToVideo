from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import re

def create_subtitled_video(audio_path, transcription, output_path):
    # Load audio
    audio = AudioFileClip(audio_path)
    
    # Create a black background video
    video = VideoFileClip('color:black').set_duration(audio.duration).set_audio(audio)
    
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
    
    # Write output video file
    final_video.write_videofile(output_path, fps=24, codec="libx264")

def parse_srt(srt_content):
    pattern = r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)\n((?:(?!\n\n).|\n)*)'
    matches = re.findall(pattern, srt_content, re.DOTALL)
    
    def time_to_seconds(time_str):
        h, m, s = time_str.replace(',', '.').split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    
    return [(time_to_seconds(start), time_to_seconds(end), text.strip()) for start, end, text in matches]
