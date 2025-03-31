from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import random

app = Flask(__name__, static_folder="static")

# コードデータを取得
def load_chords(directory="static/sounds"):
    chords = {}
    for file in os.listdir(directory):
        if file.endswith(".mp3") or file.endswith(".mid"):
            chord_name = file.replace(".mp3", "").replace(".mid", "").replace("_", "")
            chords[chord_name] = file  # ファイル名のみを格納
    return chords

chords = load_chords()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_chord')
def get_chord():
    if not chords:
        return jsonify({"error": "コード音源が見つかりません。'static/sounds/' に .mp3 または .mid ファイルを追加してください。"}), 400

    correct_answer = random.choice(list(chords.keys()))  # 1つのコードを選択
    return jsonify({"chord": f"/sounds/{chords[correct_answer]}", "answer": correct_answer})

@app.route('/sounds/<path:filename>')
def serve_sound(filename):
    file_path = os.path.join("static/sounds", filename)

    # ファイルが存在しない場合、明示的に 404 エラーを返す
    if not os.path.exists(file_path):
        return jsonify({"error": f"ファイル '{filename}' が見つかりません"}), 404

    return send_from_directory("static/sounds", filename)


@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    user_answer = data.get("answer", "").lower().replace(" ", "").replace("_", "")
    correct_answer = data.get("correct_answer", "").lower().replace(" ", "").replace("_", "")

    if user_answer == correct_answer:
        return jsonify({"result": "正解！"})
    else:
        return jsonify({"result": f"不正解！正解は {correct_answer} でした。"})

if __name__ == '__main__':
    app.run(debug=True)
