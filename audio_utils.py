from pydub import AudioSegment

def convert_to_wav(input_path):
    if input_path.lower().endswith('.wav'):
        return input_path
    
    audio = AudioSegment.from_file(input_path)
    output_path = "temp_audio.wav"
    audio.export(output_path, format="wav")
    return output_path
