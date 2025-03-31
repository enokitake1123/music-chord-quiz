from pydub import AudioSegment
import os

def convert_midi_to_mp3(midi_file, output_mp3):
    sound = AudioSegment.from_file(midi_file, format="mid")
    sound.export(output_mp3, format="mp3")

midi_dir = "static/midi/"
mp3_dir = "static/sounds/"

os.makedirs(mp3_dir, exist_ok=True)

for midi_file in os.listdir(midi_dir):
    if midi_file.endswith(".mid"):
        input_path = os.path.join(midi_dir, midi_file)
        output_path = os.path.join(mp3_dir, midi_file.replace(".mid", ".mp3"))
        convert_midi_to_mp3(input_path, output_path)
        print(f"Converted {midi_file} to MP3")
