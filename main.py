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

    # Define text color
    text_color = font_color_norm

    # Add title if provided
    if title:
        ax.text(
            0.5,
            0.9,
            title,
            color=text_color,
            fontsize=40,
            ha='center',
            va='center',
            transform=ax.transAxes
        )

    # Add byline if provided
    if byline:
        ax.text(
            0.95,
            0.05,
            byline,
            color=text_color,
            fontsize=20,
            ha='right',
            va='bottom',
            transform=ax.transAxes
        )

    # Add sample subtitle at the center
    sample_text = "Sample subtitle text"
    ax.text(
        0.5,
        0.5,  # Center vertically
        sample_text,
        color=text_color,
        fontsize=30,
        ha='center',
        va='center',
        transform=ax.transAxes
    )

    # Add border around the image
    rect = patches.Rectangle(
        (0, 0),
        1,
        1,
        linewidth=5,
        edgecolor=text_color,
        facecolor='none',
        transform=ax.transAxes
    )
    ax.add_patch(rect)

    # Save the figure to an image
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    img = Image.open(buf)

    plt.close(fig)

    return img

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
            # Added new colors
            "Crimson": "#DC143C",
            "Teal": "#008080",
            "Royal Blue": "#4169E1",
            "Olive": "#808000",
            "Gold": "#FFD700"
        }
        selected_color = st.selectbox("Background Color", list(color_options.keys()), index=0)
        bg_color_hex = color_options[selected_color]
        bg_color_rgb = hex_to_rgb(bg_color_hex)

        # Font color selection
        st.subheader("Choose Font Color")
        font_color_options = color_options  # Use the same colors as background
        selected_font_color = st.selectbox(
            "Font Color", 
            list(font_color_options.keys()), 
            index=list(font_color_options.keys()).index("White")
        )
        font_color_hex = font_color_options[selected_font_color]
        font_color_rgb = hex_to_rgb(font_color_hex)

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
    # Create and display preview
    preview_image = create_preview_image(bg_color_rgb, title, byline, font_color_rgb)
    st.image(preview_image, use_column_width=True, caption="Preview of video layout")

    if uploaded_file is not None:
        if st.button("Generate Subtitled Video"):
            try:
                with st.spinner("Processing audio..."):
                    # Save the uploaded file temporarily
                    temp_audio_path = "temp_audio" + os.path.splitext(uploaded_file.name)[1]
                    with open(temp_audio_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Process the audio file
                    mp3_path = process_audio(temp_audio_path)

                with st.spinner("Transcribing audio..."):
                    # Transcribe the audio
                    transcription = transcribe_audio(mp3_path)

                with st.spinner("Generating video..."):
                    # Generate the video
                    output_video_path = "output_video.mp4"
                    create_subtitled_video(
                        mp3_path,
                        transcription,
                        output_video_path,
                        bg_color=bg_color_rgb,
                        font_color=font_color_rgb,
                        title=title,
                        byline=byline
                    )

                # Check if the video file exists
                if os.path.exists(output_video_path):
                    st.success("Processing complete!")
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
                else:
                    st.error(f"Output video file not found: {output_video_path}")
                    logger.error(f"Output video file not found: {output_video_path}")
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                st.error(error_msg)
                logger.error(f"An error occurred: {str(e)}\n\nTraceback:\n{traceback.format_exc()}")
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
