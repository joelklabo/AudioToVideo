import streamlit as st
import os
from video_generator import create_subtitled_video
from transcription import transcribe_audio
from audio_utils import process_audio
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    st.title("Audio to Subtitled Video Generator")

    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "ogg"])

    if uploaded_file is not None:
        st.write("File uploaded successfully!")
        
        # Save the uploaded file temporarily
        temp_audio_path = "temp_audio" + os.path.splitext(uploaded_file.name)[1]
        with open(temp_audio_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("Generate Subtitled Video"):
            status_placeholder = st.empty()
            try:
                status_placeholder.text("Processing...")
                
                # Process the audio file
                status_placeholder.text("Processing audio...")
                mp3_path = process_audio(temp_audio_path)
                
                # Transcribe the audio
                status_placeholder.text("Transcribing audio...")
                transcription = transcribe_audio(mp3_path)
                
                # Generate the video
                status_placeholder.text("Generating video...")
                output_video_path = "output_video.mp4"
                create_subtitled_video(mp3_path, transcription, output_video_path)
                
                # Display the video
                st.video(output_video_path)
                
                # Provide download link
                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="Download Video",
                        data=file,
                        file_name="subtitled_video.mp4",
                        mime="video/mp4"
                    )
                status_placeholder.text("Processing complete!")
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                st.error(error_msg)
                logger.error(error_msg)
            finally:
                # Clean up temporary files
                for path in [temp_audio_path, mp3_path, output_video_path]:
                    if path and os.path.exists(path):
                        try:
                            os.remove(path)
                            logger.info(f"Removed temporary file: {path}")
                        except Exception as e:
                            logger.error(f"Error removing temporary file {path}: {str(e)}")

if __name__ == "__main__":
    main()
