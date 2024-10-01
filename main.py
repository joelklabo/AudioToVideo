import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from transcription import transcribe_audio
from video_generator import create_subtitled_video
from audio_utils import process_audio

# Load environment variables
load_dotenv()

st.title("Audio to Subtitled Video Generator")

# File uploader
uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "ogg"])

if uploaded_file is not None:
    try:
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_audio_path = temp_file.name

        st.audio(temp_audio_path)
        
        if st.button("Generate Subtitled Video"):
            status_placeholder = st.empty()
            progress_bar = st.progress(0)

            try:
                status_placeholder.text("Processing audio...")
                progress_bar.progress(10)
                mp3_path = process_audio(temp_audio_path)
                
                status_placeholder.text("Transcribing audio...")
                progress_bar.progress(40)
                transcription = transcribe_audio(mp3_path)
                
                status_placeholder.text("Generating video with subtitles...")
                progress_bar.progress(70)
                output_video_path = tempfile.mktemp(suffix=".mp4")
                create_subtitled_video(mp3_path, transcription, output_video_path)
                
                status_placeholder.text("Processing complete!")
                progress_bar.progress(100)

                # Provide download link
                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="Download Subtitled Video",
                        data=file,
                        file_name="subtitled_video.mp4",
                        mime="video/mp4"
                    )
            except Exception as e:
                status_placeholder.text("An error occurred during processing.")
                st.error(f"Error details: {str(e)}")
            finally:
                # Clean up temporary files
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                if os.path.exists(output_video_path):
                    os.remove(output_video_path)
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")

st.markdown("""
### Instructions:
1. Upload an audio file (MP3, WAV, M4A, or OGG format).
2. Click the "Generate Subtitled Video" button.
3. Wait for the processing to complete.
4. Download the generated video with subtitles.
""")
