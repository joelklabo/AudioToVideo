import streamlit as st
import os
from video_generator import create_subtitled_video
from transcription import transcribe_audio
from audio_utils import process_audio
import logging
import traceback
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_preview_image(bg_color, title, byline):
    # Create a new image with the selected background color
    img = Image.new('RGB', (1280, 720), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Use default font
    title_font = ImageFont.load_default()
    byline_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()

    # Log font information
    st.write(f"Title font: {title_font}")
    st.write(f"Byline font: {byline_font}")
    st.write(f"Subtitle font: {subtitle_font}")

    # Add title if provided
    if title:
        draw.text((640, 50), title, font=title_font, fill="white", anchor="mt")
        title_bbox = draw.textbbox((640, 50), title, font=title_font, anchor="mt")
        st.write(f"Title bounding box: {title_bbox}")

    # Add byline if provided
    if byline:
        draw.text((1260, 700), byline, font=byline_font, fill="white", anchor="rb")
        byline_bbox = draw.textbbox((1260, 700), byline, font=byline_font, anchor="rb")
        st.write(f"Byline bounding box: {byline_bbox}")

    # Add sample subtitle
    sample_text = "Sample subtitle text"
    draw.text((640, 360), sample_text, font=subtitle_font, fill="white", anchor="mm")
    subtitle_bbox = draw.textbbox((640, 360), sample_text, font=subtitle_font, anchor="mm")
    st.write(f"Subtitle bounding box: {subtitle_bbox}")

    # Add border around the image
    draw.rectangle([0, 0, 1279, 719], outline="white", width=5)

    # Log image size
    st.write(f"Preview image size: {img.size}")

    return img

def get_image_download_link(img, filename, text):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">{text}</a>'
    return href

def get_image_html(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f'<img src="data:image/png;base64,{img_str}" style="width:100%">'

def main():
    st.title("Audio to Subtitled Video Generator")

    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "ogg"])

    # Color picker for background color
    st.subheader("Choose Background Color")
    color_options = {
        "Black": "#000000",
        "Dark Gray": "#333333",
        "Navy Blue": "#000080",
        "Dark Green": "#006400",
        "Maroon": "#800000",
        "Purple": "#800080",
        "Orange": "#FFA500"  # Added orange option
    }
    selected_color = st.selectbox("Select a background color", list(color_options.keys()))
    bg_color_hex = color_options[selected_color]
    bg_color_rgb = hex_to_rgb(bg_color_hex)
    
    st.markdown(f"<div style='background-color: {bg_color_hex}; width: 100px; height: 50px;'></div>", unsafe_allow_html=True)

    # Optional title and byline inputs
    title = st.text_input("Video Title (optional)")
    byline = st.text_input("Byline (optional)")

    # Create and display preview
    preview_image = create_preview_image(bg_color_rgb, title, byline)
    st.subheader("Preview")
    st.image(preview_image, use_column_width=True, caption="Preview of video layout")
    st.write(f"Displayed image size: {preview_image.size}")

    # Add a download link for the preview image
    buffered = io.BytesIO()
    preview_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="preview.png">Download Preview Image</a>'
    st.markdown(href, unsafe_allow_html=True)

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
                create_subtitled_video(mp3_path, transcription, output_video_path, bg_color=bg_color_rgb, title=title, byline=byline)
                
                # Check if the video file exists
                if os.path.exists(output_video_path):
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
                else:
                    st.error(f"Output video file not found: {output_video_path}")
                    logger.error(f"Output video file not found: {output_video_path}")
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
