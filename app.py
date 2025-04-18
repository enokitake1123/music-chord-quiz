from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import random
import subprocess
import shutil
import mido
from mido import Message, MidiFile, MidiTrack

app = Flask(__name__, static_folder="static")

def convert_midi_to_mp3(midi_file, mp3_file):
    ffmpeg_path = shutil.which("ffmpeg")
    timidity_path = shutil.which("timidity")

    if not ffmpeg_path:
        print("❌ エラー: ffmpeg が見つかりません。")
        return
    if not timidity_path:
        print("❌ エラー: timidity が見つかりません。")
        return

    mp3_dir = os.path.dirname(mp3_file)
    os.makedirs(mp3_dir, exist_ok=True)

    wav_file = midi_file.replace(".mid", ".wav")

    command1 = [timidity_path, midi_file, "-Ow", "-o", wav_file]
    result1 = subprocess.run(command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result1.returncode != 0:
        print(f"❌ Timidity 変換エラー: {result1.stderr}")
        return

    command2 = [ffmpeg_path, "-i", wav_file, "-b:a", "192k", "-y", mp3_file]
    result2 = subprocess.run(command2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result2.returncode != 0:
        print(f"❌ ffmpeg 変換エラー: {result2.stderr}")
    else:
        print(f"✅ '{mp3_file}' が作成されました")

    os.remove(wav_file)

def load_chords(directory="static/sounds"):
    chords = {}
    for file in os.listdir(directory):
        if file.endswith(".mid"):
            chord_name = file.replace(".mid", "").replace("_", "")
            chords[chord_name] = file
    return chords

def create_midi_chord(chord_name, filename):
    base_notes = {
        "C": 60, "C#": 61, "Db": 61, "D": 62, "D#": 63, "Eb": 63, "E": 64, "F": 65,
        "F#": 66, "Gb": 66, "G": 67, "G#": 68, "Ab": 68, "A": 69, "A#": 70, "Bb": 70, "B": 71
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
        "m6": [0, 3, 7, 9]
    }
    base, chord_type = chord_name.rsplit("_", 1) if "_" in chord_name else (chord_name, "major")
    chord_name_clean = f"{base}{chord_type}"
    root_note = base_notes.get(base)
    if root_note is None or chord_type not in chord_types:
        print(f"{chord_name} は未登録のコードです。")
        return
    notes = [root_note + interval for interval in chord_types[chord_type]]
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    for note in notes:
        track.append(Message("note_on", note=note, velocity=64, time=0))
    track.append(Message("note_off", note=notes[0], velocity=64, time=960))
    for note in notes[1:]:
        track.append(Message("note_off", note=note, velocity=64, time=0))
    mid.save(filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_chord')
def get_chord():
    difficulty = request.args.get("difficulty", "easy")
    easy_types = ["major", "minor"]
    medium_types = easy_types + ["7th", "minor7", "dim", "aug", "sus4"]
    hard_types = medium_types + ["add9", "m7-5", "7#9", "7-5", "7-9", "6", "m6", "major7"]

    def filter_chords(types):
        return [chord for chord in chords.keys() if any(t in chord for t in types)]

    if difficulty == "easy":
        pool = filter_chords(easy_types)
    elif difficulty == "medium":
        pool = filter_chords(medium_types)
    else:
        pool = list(chords.keys())

    if not pool:
        return jsonify({"error": "該当するコードがありません"}), 400

    correct_answer = random.choice(pool)
    display_answer = correct_answer.replace("major", "")

    print(f"🎯 正解コード: {correct_answer}")
    print(f"🎧 再生ファイル: /mp3_sounds/{correct_answer}.mp3")

    return jsonify({
        "chord": f"/mp3_sounds/{correct_answer}.mp3",
        "answer": display_answer,
        "correct_raw": correct_answer
    })

@app.route('/mp3_sounds/<path:filename>')
def serve_sound(filename):
    file_path = os.path.join("static/mp3_sounds", filename)
    print(f"🎧 リクエストされたファイル: {filename}")
    print(f"👉 探しているパス: {file_path}")
    if not os.path.exists(file_path):
        available_files = os.listdir("static/mp3_sounds/")
        print(f"❌ エラー: '{filename}' が見つかりません")
        print(f"📂 既存のファイル一覧: {available_files}")
        return jsonify({"error": f"ファイル '{filename}' が見つかりません"}), 404
    return send_from_directory("static/mp3_sounds", filename)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    user = normalize(data['answer'])
    correct = normalize(data['correct_answer']) if 'correct_answer' in data else normalize(data['correct_raw'])
    is_correct = (user == correct)
    display_answer = data.get('correct_answer', data.get('correct_raw', '')).replace("major", "")
    result = "正解！" if is_correct else f"不正解！正解は {display_answer} でした"
    return jsonify({"result": result, "correct": is_correct})

def normalize(answer):
    answer = answer.strip().lower()
    answer = answer.replace(" ", "")
    answer = answer.replace("♯", "#")
    answer = answer.replace("♭", "b")
    answer = answer.replace("major", "")
    answer = answer.replace("minor", "m")
    answer = answer.replace("th", "")
    return answer

if __name__ == '__main__':
    midi_directory = "static/sounds"
    mp3_directory = "static/mp3_sounds"
    os.makedirs(mp3_directory, exist_ok=True)

    for file in os.listdir(mp3_directory):
        if file.endswith(".mp3"):
            os.remove(os.path.join(mp3_directory, file))

    all_chord_types = [
        "major", "minor", "7th", "dim", "aug", "major7", "minor7",
        "sus4", "add9", "m7-5", "7#9", "7-5", "7-9", "6", "m6"
    ]
    all_bases = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    for base in all_bases:
        for ctype in all_chord_types:
            chord_key = f"{base}{ctype}"
            midi_filename = f"{chord_key}.mid"
            midi_path = os.path.join(midi_directory, midi_filename)
            mp3_filename = midi_filename.replace(".mid", ".mp3")
            mp3_path = os.path.join(mp3_directory, mp3_filename)

            create_midi_chord(f"{base}_{ctype}", midi_path)
            convert_midi_to_mp3(midi_path, mp3_path)

    chords = load_chords(midi_directory)

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)