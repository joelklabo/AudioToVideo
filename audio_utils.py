import logging
from pydub import AudioSegment

logger = logging.getLogger(__name__)

def convert_to_wav(input_path):
    logger.info(f"Starting conversion to WAV: {input_path}")
    if input_path.lower().endswith('.wav'):
        logger.info(f"File is already in WAV format: {input_path}")
        return input_path
    
    audio = AudioSegment.from_file(input_path)
    output_path = "temp_audio.wav"
    audio.export(output_path, format="wav")
    logger.info(f"Successfully converted to WAV: {output_path}")
    return output_path

def convert_to_mp3(input_path):
    logger.info(f"Starting conversion to MP3: {input_path}")
    audio = AudioSegment.from_file(input_path)
    output_path = "temp_audio.mp3"
    audio.export(output_path, format="mp3")
    logger.info(f"Successfully converted to MP3: {output_path}")
    return output_path

def process_audio(input_path):
    logger.info(f"Starting audio processing: {input_path}")
    if input_path.lower().endswith('.wav'):
        logger.info("Input is WAV, converting to MP3")
        return convert_to_mp3(input_path)
    else:
        logger.info("Input is not WAV, converting to WAV first")
        wav_path = convert_to_wav(input_path)
        logger.info("Converting WAV to MP3")
        return convert_to_mp3(wav_path)
