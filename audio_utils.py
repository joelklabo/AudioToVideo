from pydub import AudioSegment

def convert_to_wav(input_path):
    if input_path.lower().endswith('.wav'):
        return input_path
    
    audio = AudioSegment.from_file(input_path)
    output_path = "temp_audio.wav"
    audio.export(output_path, format="wav")
    return output_path

def convert_to_mp3(input_path):
    audio = AudioSegment.from_file(input_path)
    output_path = "temp_audio.mp3"
    audio.export(output_path, format="mp3")
    return output_path

def process_audio(input_path):
    if input_path.lower().endswith('.wav'):
        return convert_to_mp3(input_path)
    else:
        wav_path = convert_to_wav(input_path)
        return convert_to_mp3(wav_path)
