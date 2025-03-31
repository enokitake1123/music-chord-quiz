import pygame
import random
import os
import mido
from mido import Message, MidiFile, MidiTrack

def create_midi_chord(chord_name, filename):
    """ 指定したコードのMIDIファイルを作成 """
    base_notes = {
        "C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65,
        "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71
    }

    chord_types = {
        "major": [0, 4, 7],
        "minor": [0, 3, 7],
        "7th": [0, 4, 7, 10],
        "9th": [0, 4, 7, 10, 14],
        "dim": [0, 3, 6],
        "aug": [0, 4, 8],
        "m7": [0, 3, 7, 10],
        "M7": [0, 4, 7, 11],
        "mM7": [0, 3, 7, 11],
        "sus4": [0, 5, 7],
        "7sus4": [0, 5, 7, 10],
        "m7-5": [0, 3, 6, 10],
        "add9": [0, 4, 7, 14],
        "6": [0, 4, 7, 9],
        "m6": [0, 3, 7, 9],
        "sus2": [0, 2, 7],
        "7#9": [0, 4, 7, 10, 15],
        "7-5": [0, 4, 6, 10],
        "7-9": [0, 4, 7, 10, 13]
    }

    base, chord_type = chord_name.rsplit("_", 1) if "_" in chord_name else (chord_name, "major")
    if base not in base_notes or chord_type not in chord_types:
        print(f"{chord_name} は未登録のコードです。")
        return

    root_note = base_notes[base]
    notes = [root_note + interval for interval in chord_types[chord_type]]

    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    for note in notes:
        track.append(Message("note_on", note=note, velocity=64, time=0))
    track.append(Message("note_off", note=notes[0], velocity=64, time=960))  # 一定の長さにする
    for note in notes[1:]:
        track.append(Message("note_off", note=note, velocity=64, time=0))

    mid.save(filename)

def load_chords(directory="sounds"):
    """ 指定したディレクトリ内のMIDIファイルを取得 """
    chords = {}
    for file in os.listdir(directory):
        if file.endswith(".mid") and not ("11th" in file or "13th" in file):
            chord_name = file.replace(".mid", "").replace("_", "").replace("th", "")
            chords[chord_name] = os.path.join(directory, file)
    return chords

def play_midi(file_path):
    """ 指定したMIDIファイルを再生 """
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # 再生終了まで待機
        continue

def normalize_answer(answer):
    """ major を M, minor を m として扱い、アンダースコアなしでも正解にする """
    answer = answer.replace("major", "M").replace("minor", "m").replace(" ", "").replace("_", "").replace("th", "")
    if answer[-1].isdigit():
        return answer.lower()
    return answer.lower().replace("m", "")  # majorの場合、何も書かなくても正解

def quiz(chords):
    """ 音楽コードクイズの実行 """
    score = 0
    questions = 10
    chord_names = list(chords.keys())

    print("音楽コード当てクイズを始めます！")
    print("再生されるコードを聞いて、正しいコード名を入力してください。\n")

    for _ in range(questions):
        correct_answer = random.choice(chord_names)
        print("コードを再生します...")
        play_midi(chords[correct_answer])

        user_answer = input("このコードは何ですか？: ")

        if normalize_answer(user_answer) == normalize_answer(correct_answer):
            print("正解！\n")
            score += 1
        else:
            print(f"不正解！正解は {correct_answer} でした。\n")

    print(f"クイズ終了！あなたのスコア: {score}/{questions}")

    if score == 10:
        print("完璧です！素晴らしい耳を持っています！")
    elif score >= 7:
        print("とても良いです！あと少しで完璧です！")
    elif score >= 4:
        print("まあまあです！練習すればもっと良くなります！")
    else:
        print("もっと練習が必要です！頑張りましょう！")

if __name__ == "__main__":
    # MIDIファイルを作成
    midi_directory = "sounds"
    os.makedirs(midi_directory, exist_ok=True)

    chord_list = []
    bases = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    types = ["major", "minor", "dim", "aug", "m7", "M7", "mM7", "sus4", "7sus4", "m7-5", "add9", "6", "m6", "sus2", "7#9", "7-5", "7-9"]

    for base in bases:
        for ctype in types:
            chord_list.append(f"{base}{ctype}")
            create_midi_chord(f"{base}_{ctype}", os.path.join(midi_directory, f"{base}_{ctype}.mid"))

    chords = load_chords(midi_directory)
    if not chords:
        print("エラー: コード音源が見つかりません。'sounds/' フォルダを確認してください。")
    else:
        quiz(chords)
