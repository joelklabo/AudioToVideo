import streamlit as st
import os
from video_generator import create_subtitled_video
from transcription import transcribe_audio
from audio_utils import process_audio
import logging
import traceback
from PIL import Image
import io
import base64
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_preview_image(bg_color, title, byline, font_color):
    # Convert colors from RGB tuples to normalized RGB tuples
    bg_color_norm = tuple(c / 255.0 for c in bg_color)
    font_color_norm = tuple(c / 255.0 for c in font_color)

    # Create a matplotlib figure
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.patch.set_facecolor(bg_color_norm)
    ax.set_facecolor(bg_color_norm)

    # Remove axes
    ax.axis('off')

    # Add title if provided
    if title:
        ax.text(
            0.5, 0.9, title, color=font_color_norm, fontsize=40,
            ha='center', va='center', transform=ax.transAxes
        )

    # Add byline if provided
    if byline:
        ax.text(
            0.95, 0.05, byline, color=font_color_norm, fontsize=20,
            ha='right', va='bottom', transform=ax.transAxes
        )

    # Add sample subtitle at the center
    sample_text = "Sample subtitle text"
    ax.text(
        0.5, 0.5, sample_text, color=font_color_norm, fontsize=30,
        ha='center', va='center', transform=ax.transAxes
    )

    # Add border around the image
    rect = patches.Rectangle(
        (0, 0), 1, 1, linewidth=5, edgecolor=font_color_norm,
        facecolor='none', transform=ax.transAxes
    )
    ax.add_patch(rect)

    # Save the figure to an image
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    img = Image.open(buf)

    plt.close(fig)
    return img

def save_uploaded_file(uploaded_file, dir_path="temp_files"):
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def clean_up_files(paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Removed temporary file: {path}")
            except Exception as e:
                logger.error(f"Error removing temporary file {path}: {str(e)}")

def main():
    st.set_page_config(page_title="Audio to Subtitled Video Generator", layout="wide")
    st.title("Audio to Subtitled Video Generator")
    st.write("Generate a subtitled video from an audio file.")

    # Sidebar for customization options
    with st.sidebar:
        st.header("Customization Options")

        # Color picker for background color
        st.subheader("Choose Background Color")
        color_options = {
            "Black": "#000000",
            "White": "#FFFFFF",
            "Dark Gray": "#333333",
            "Navy Blue": "#000080",
            "Dark Green": "#006400",
            "Maroon": "#800000",
            "Purple": "#800080",
            "Orange": "#FFA500",
            "Crimson": "#DC143C",
            "Teal": "#008080",
            "Royal Blue": "#4169E1",
            "Olive": "#808000",
            "Gold": "#FFD700"
        }
        selected_color = st.selectbox("Background Color", list(color_options.keys()), index=0)
        bg_color_rgb = hex_to_rgb(color_options[selected_color])

        # Font color selection
        st.subheader("Choose Font Color")
        selected_font_color = st.selectbox("Font Color", list(color_options.keys()), index=1)
        font_color_rgb = hex_to_rgb(color_options[selected_font_color])

        # Optional title and byline inputs
        st.subheader("Add Text")
        title = st.text_input("Video Title (optional)")
        byline = st.text_input("Byline (optional)")

    # Upload Audio File section
    st.subheader("Upload Audio File")
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a", "ogg"])

    if uploaded_file is not None:
        st.success("File uploaded successfully!")

    # Preview section
    st.subheader("Preview")
    preview_image = create_preview_image(bg_color_rgb, title, byline, font_color_rgb)
    st.image(preview_image, use_column_width=True, caption="Preview of video layout")

    if uploaded_file is not None and st.button("Generate Subtitled Video"):
        try:
            with st.spinner("Processing audio..."):
                audio_path = save_uploaded_file(uploaded_file)
                mp3_path = process_audio(audio_path)

            with st.spinner("Transcribing audio..."):
                transcription = transcribe_audio(mp3_path)

            with st.spinner("Generating video..."):
                output_video_path = "output_video.mp4"
                create_subtitled_video(
                    mp3_path, transcription, output_video_path,
                    bg_color=bg_color_rgb, font_color=font_color_rgb,
                    title=title, byline=byline
                )

            if os.path.exists(output_video_path):
                st.success("Processing complete!")
                st.video(output_video_path)

                with open(output_video_path, "rb") as file:
                    st.download_button(
                        label="Download Video",
                        data=file,
                        file_name="subtitled_video.mp4",
                        mime="video/mp4"
                    )
            else:
                st.error(f"Output video file not found: {output_video_path}")
                logger.error(f"Output video file not found: {output_video_path}")
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            st.error(error_msg)
            logger.error(f"An error occurred: {str(e)}\n\nTraceback:\n{traceback.format_exc()}")
        finally:
            clean_up_files([audio_path, mp3_path, output_video_path])

if __name__ == "__main__":
    main()