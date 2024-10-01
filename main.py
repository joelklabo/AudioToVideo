import streamlit as st
import os
import tempfile
import logging
import io
import contextlib
from dotenv import load_dotenv
from transcription import transcribe_audio
from video_generator import create_subtitled_video
from audio_utils import process_audio
import concurrent.futures
import time

# Configure logging
log_stream = io.StringIO()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=log_stream)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set timeout for long-running tasks (in seconds)
TASK_TIMEOUT = 300

def run_with_timeout(func, *args, timeout=TASK_TIMEOUT):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.error(f"Task timed out after {timeout} seconds")
            raise TimeoutError(f"Task timed out after {timeout} seconds")

def main():
    st.title("Audio to Subtitled Video Generator")

    # File uploader
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "ogg"])

    # Display logs
    log_placeholder = st.empty()

    def update_logs():
        current_time = int(time.time() * 1000)  # Use milliseconds for more uniqueness
        log_placeholder.text_area("Logs", log_stream.getvalue(), height=200, key=f"log_area_{current_time}")

    if uploaded_file is not None:
        try:
            logger.info(f"Processing uploaded file: {uploaded_file.name}")
            
            # Create a temporary file to store the uploaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_audio_path = temp_file.name

            st.audio(temp_audio_path)
            
            if st.button("Generate Subtitled Video"):
                status_placeholder = st.empty()
                progress_bar = st.progress(0)

                output_video_path = None
                mp3_path = None

                try:
                    status_placeholder.text("Processing audio...")
                    progress_bar.progress(10)
                    mp3_path = run_with_timeout(process_audio, temp_audio_path)
                    update_logs()
                    
                    status_placeholder.text("Transcribing audio...")
                    progress_bar.progress(40)
                    transcription = run_with_timeout(transcribe_audio, mp3_path)
                    update_logs()
                    
                    status_placeholder.text("Generating video with subtitles...")
                    progress_bar.progress(70)
                    output_video_path = tempfile.mktemp(suffix=".mp4")
                    run_with_timeout(create_subtitled_video, mp3_path, transcription, output_video_path)
                    update_logs()
                    
                    status_placeholder.text("Processing complete!")
                    progress_bar.progress(100)
                    update_logs()

                    if os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
                        # Provide download link
                        with open(output_video_path, "rb") as file:
                            st.download_button(
                                label="Download Subtitled Video",
                                data=file,
                                file_name="subtitled_video.mp4",
                                mime="video/mp4"
                            )
                        
                        # Display video player
                        st.video(output_video_path)
                    else:
                        st.error("Video file was not created successfully or is empty.")
                except Exception as e:
                    status_placeholder.text("An error occurred during processing.")
                    st.error(f"Error details: {str(e)}")
                    logger.error(f"Error during processing: {str(e)}")
                    update_logs()
                finally:
                    # Clean up temporary files
                    for path in [temp_audio_path, mp3_path]:
                        if path and os.path.exists(path):
                            os.remove(path)
                            logger.info(f"Removed temporary file: {path}")
                    if output_video_path and os.path.exists(output_video_path):
                        os.remove(output_video_path)
                        logger.info(f"Removed temporary file: {output_video_path}")
                    update_logs()
        except Exception as e:
            st.error(f"An error occurred while uploading the file: {str(e)}")
            logger.error(f"Error during file upload: {str(e)}")
            update_logs()

    st.markdown("""
    ### Instructions:
    1. Upload an audio file (MP3, WAV, M4A, or OGG format).
    2. Click the "Generate Subtitled Video" button.
    3. Wait for the processing to complete.
    4. Download the generated video with subtitles or watch it in the app.
    """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in main app: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")
