import os
import shutil
import subprocess
from mido import Message, MidiFile, MidiTrack

# 保存先ディレクトリ
midi_dir = "static/sounds"
mp3_dir = "static/mp3_sounds"

os.makedirs(midi_dir, exist_ok=True)
os.makedirs(mp3_dir, exist_ok=True)

# 古いファイルを削除
for f in os.listdir(midi_dir):
    if f.endswith(".mid"):
        os.remove(os.path.join(midi_dir, f))
for f in os.listdir(mp3_dir):
    if f.endswith(".mp3"):
        os.remove(os.path.join(mp3_dir, f))

# コード定義
base_notes = {
    "C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65,
    "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71
}

chord_types = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "7th": [0, 4, 7, 10],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "sus4": [0, 5, 7],
    "add9": [0, 4, 7, 14],
    "m7-5": [0, 3, 6, 10],
    "7#9": [0, 4, 7, 10, 15],
    "7-5": [0, 4, 6, 10],
    "7-9": [0, 4, 7, 10, 13],
    "6": [0, 4, 7, 9],
    "m6": [0, 3, 7, 9],
}

def sanitize_filename(chord_name):
    return chord_name.replace("#", "sharp").replace("-", "").replace("7th", "7")  # ファイル名の特殊文字排除

def create_midi(chord_name, path):
    matched = False
    for base in base_notes:
        if chord_name.startswith(base):
            ctype = chord_name[len(base):]
            if ctype in chord_types:
                root = base_notes[base]
                intervals = chord_types[ctype]
                notes = [root + i for i in intervals]
                mid = MidiFile()
                track = MidiTrack()
                mid.tracks.append(track)

                for note in notes:
                    track.append(Message('note_on', note=note, velocity=64, time=0))
                track.append(Message('note_off', note=notes[0], velocity=64, time=960))
                for note in notes[1:]:
                    track.append(Message('note_off', note=note, velocity=64, time=0))

                mid.save(path)
                matched = True
                break

    if not matched:
        print(f"スキップ: 未定義コード {chord_name}")


def convert_to_mp3(midi_path, mp3_path):
    wav_path = midi_path.replace(".mid", ".wav")
    timidity = shutil.which("timidity")
    ffmpeg = shutil.which("ffmpeg")

    if not timidity or not ffmpeg:
        print("❌ Timidity または ffmpeg が見つかりません。")
        return

    subprocess.run([timidity, midi_path, "-Ow", "-o", wav_path])
    subprocess.run([ffmpeg, "-i", wav_path, "-b:a", "192k", "-y", mp3_path])
    os.remove(wav_path)

# すべてのコードを生成
for base in base_notes:
    for ctype in chord_types:
        chord = f"{base}{ctype}"
        filename = sanitize_filename(chord)
        midi_path = os.path.join(midi_dir, filename + ".mid")
        mp3_path = os.path.join(mp3_dir, filename + ".mp3")

        create_midi(chord, midi_path)
        convert_to_mp3(midi_path, mp3_path)
        print(f"✅ 作成: {filename}")
