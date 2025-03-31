from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import random
import subprocess
import shutil
import mido
from mido import Message, MidiFile, MidiTrack

app = Flask(__name__, static_folder="static")

# MIDI を WAV に変換し、MP3 に変換
def convert_midi_to_mp3(midi_file, mp3_file):
    ffmpeg_path = shutil.which("ffmpeg")
    timidity_path = shutil.which("timidity")

    if not ffmpeg_path:
        print("❌ エラー: ffmpeg が見つかりません。")
        return
    if not timidity_path:
        print("❌ エラー: timidity が見つかりません。")
        return

    mp3_file = mp3_file.replace("mp3sounds", "mp3_sounds").replace("#", "sharp").replace("_", "")
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
            chord_name = chord_name.replace("A#", "Asharp").replace("Bb", "Bflat")
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
        "aug": [0, 4, 8]
    }
    base, chord_type = chord_name.rsplit("_", 1) if "_" in chord_name else (chord_name, "major")
    base = base.replace("#", "sharp")
    correct_filename = f"{base}{chord_type}.mid"
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
    mid.save(filename.replace("_", ""))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_chord')
def get_chord():
    if not chords:
        print("❌ エラー: コード音源が見つかりません。")
        return jsonify({"error": "コード音源が見つかりません。'static/sounds/' に .mid ファイルを追加してください。"}), 400
    correct_answer = random.choice(list(chords.keys()))
    formatted_answer = correct_answer.replace("#", "sharp").replace("_", "")
    print(f"🔄 送信するコード: {correct_answer} → {formatted_answer}")
    return jsonify({"chord": f"/mp3_sounds/{formatted_answer}.mp3", "answer": formatted_answer})

@app.route('/mp3_sounds/<path:filename>')
def serve_sound(filename):
    filename = filename.replace("#", "sharp").replace("_", "")
    file_path = os.path.join("static/mp3_sounds", filename)
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
    correct = normalize(data['correct_answer'])

    is_correct = (user == correct)
    result = "正解！" if is_correct else f"不正解！正解は {data['correct_answer']} でした"

    return jsonify({"result": result, "correct": is_correct})




def normalize(answer):
    answer = answer.strip().lower()
    answer = answer.replace(" ", "").replace("_", "")
    answer = answer.replace("♯", "sharp").replace("#", "sharp")
    answer = answer.replace("♭", "flat")

    # 「major」は省略可 → 削除
    if "major" in answer:
        answer = answer.replace("major", "")

    # 「C」だけ入力された場合、正解側が Cmajor だったら一致するように
    # よって正解側も normalize() で "cmajor" → "c" になる
    if answer.endswith("m") or "minor" in answer:
        answer = answer.replace("minor", "m")  # minor は m に統一
    else:
        # major の省略扱い
        pass  # すでに major は削除済み

    # 余計な th を削除（7th → 7 など）
    answer = answer.replace("th", "")

    return answer




if __name__ == '__main__':
    #以下ローカル用のやつ
    #midi_directory = "static/sounds"
    #mp3_directory = "static/mp3_sounds"
    #os.makedirs(mp3_directory, exist_ok=True)
    #chords = load_chords(midi_directory)
    #for chord, midi_file in chords.items():
       #midi_path = os.path.join(midi_directory, midi_file)
        #mp3_path = os.path.join(mp3_directory, midi_file.replace(".mid", ".mp3"))
        #if not os.path.exists(mp3_path):
            #convert_midi_to_mp3(midi_path, mp3_path)

    chords = load_chords("static/sounds")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
