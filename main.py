import streamlit as st
import os
from dotenv import load_dotenv
from transcription import transcribe_audio
from video_generator import create_subtitled_video
from audio_utils import convert_to_wav

# Load environment variables
load_dotenv()

st.title("Audio to Subtitled Video Generator")

# File uploader
uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "ogg"])

if uploaded_file is not None:
    st.audio(uploaded_file)
    
    if st.button("Generate Subtitled Video"):
        with st.spinner("Processing..."):
            # Save the uploaded file temporarily
            temp_audio_path = f"temp_audio.{uploaded_file.name.split('.')[-1]}"
            with open(temp_audio_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Convert to WAV if necessary
            wav_path = convert_to_wav(temp_audio_path)
            
            # Transcribe audio
            transcription = transcribe_audio(wav_path)
            
            # Generate video with subtitles
            output_video_path = "output_video.mp4"
            create_subtitled_video(wav_path, transcription, output_video_path)
            
            # Clean up temporary files
            os.remove(temp_audio_path)
            if wav_path != temp_audio_path:
                os.remove(wav_path)
            
            # Provide download link
            with open(output_video_path, "rb") as file:
                st.download_button(
                    label="Download Subtitled Video",
                    data=file,
                    file_name="subtitled_video.mp4",
                    mime="video/mp4"
                )
            
            # Clean up output video
            os.remove(output_video_path)

st.markdown("""
### Instructions:
1. Upload an audio file (MP3, WAV, M4A, or OGG format).
2. Click the "Generate Subtitled Video" button.
3. Wait for the processing to complete.
4. Download the generated video with subtitles.
""")
