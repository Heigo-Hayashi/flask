from flask import Flask, render_template, request, redirect, url_for, jsonify
import openai
from threading import Thread
import speech_recognition as sr
from gtts import gTTS
import tempfile
import pygame
import re
import requests
from queue import Queue

app = Flask(__name__, static_folder='./templates/img')

##############
# 音声認識関数 #
##############
def recognize_speech():
    recognizer = sr.Recognizer()
    # Set timeout settings.
    recognizer.dynamic_energy_threshold = False
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while(True):
            print(">> Please speak now...")
            audio = recognizer.listen(source, timeout=1000.0)
            try:
                # Google Web Speech API を使って音声をテキストに変換
                text = recognizer.recognize_google(audio, language="ja-JP")
                print("[You]")
                print(text)
                return text
            except sr.UnknownValueError:
                print("Sorry, I could not understand what you said. Please speak again.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                
#############################
# 音声ファイル(mp3)再生用の関数 #
#############################
def play_mp3_blocking(file_path):
    pygame.init()
    pygame.mixer.init()
    mp3_file = pygame.mixer.Sound(file_path)    # MP3ファイルをロード
    print(">> Ready to Sppeach!")
    mp3_file.play()     # MP3ファイルを再生
    # 再生が終了するまで待つ(ブロッキング処理)
    while pygame.mixer.get_busy():
        pygame.time.Clock().tick(10)  # 10msごとに再生状態をチェック
    pygame.mixer.quit()
                
####################################################################################
# Google Text-to-Speech(gTTS)を用いてChatGPTによるレスポンス(テキスト)を.mp3形式に変換する #
####################################################################################
def text_to_speech(text):

    tts = gTTS(text=text, lang='ja', slow=False)
    
    with tempfile.NamedTemporaryFile(delete=True) as fp:
        temp_filename = f"{fp.name}.mp3"
        tts.save(temp_filename)

        # 音声ファイル再生（ブロッキング処理）
        play_mp3_blocking(temp_filename)

from flask import Flask, render_template, request, jsonify
from threading import Thread

app = Flask(__name__)

conversation_history = []
openai.api_key = "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"

@app.route('/')
def index():
    # return jsonify({})
    return render_template('index.html')

@app.route('/recognize_and_respond', methods=['POST'])
def start_recognition():
    result_queue = Queue()
    user_input = request.json['user_input']  # フロントエンドからのデータを取得
    # Start a new thread for processing the user input
    # recognition_thread = Thread(target=lambda: recognize_and_respond(user_input))
    recognition_thread = Thread(target=lambda: recognize_and_respond(user_input,result_queue))
    recognition_thread.start()
    recognition_thread.join()
    result = result_queue.get()
    return jsonify(result)


@app.route('/get_conversation')
def get_conversation():
    return jsonify(history=conversation_history)

# def recognize_and_respond(user_input):
def recognize_and_respond(user_input,result_queue):
    # Your speech recognition and ChatGPT response logic here
    # You may need to update conversation_history during the process
    global conversation_history

    recognizer = sr.Recognizer()


    try:
        # Google Web Speech API を使って音声をテキストに変換
        print("[User]")
        print(user_input)

        # ユーザの発言を履歴に追加
        user_message = {"role": "user", "content": user_input}
        conversation_history.append(user_message)

        if "送って" in user_input:
            # トリガーワードの追加の処理
            print("トリガーワード '送って' を検出しました。追加のコマンドを実行します。")

            # 正規表現を使用して名前を抽出
            match = re.search(r'([^に]+)に(.+)と送って', user_input)
            if match:
                name = match.group(1)
                greeting = match.group(2)
                print(f"検出された名前: {name}")
                print(f"検出された挨拶: {greeting}")
                
                 # データを組み立てる
                data = {
                    'user_id': 100,
                    'to_user_id': name,
                    'text': greeting
                }

                # HTTP POSTリクエストを送信
                url = 'http://localhost:5000/api/send_message'
                response = requests.post(url, data=data)

                # レスポンスを表示
                print(response.text)
                
                text_to_speech("かしこまりました。送信します。")
            
            match2 = re.search(r'([^に]+)に(.+)って送って', user_input)
            if match2:
                name = match2.group(1)
                greeting = match2.group(2)
                print(f"検出された名前: {name}")
                print(f"検出された挨拶: {greeting}")
                
                 # データを組み立てる
                data = {
                    'user_id': 100,
                    'to_user_id': name,
                    'text': greeting
                }

                # HTTP POSTリクエストを送信
                url = 'http://localhost:5000/api/send_message'
                response = requests.post(url, data=data)

                # レスポンスを表示
                print(response.text)
                text_to_speech("かしこまりました。送信します。")
                
        else:
            # ChatGPT に発言を送信して応答を取得
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=conversation_history,
            )
            chatgpt_response = response["choices"][0]["message"]["content"]

            # ChatGPTの応答を履歴に追加
            chatgpt_message = {"role": "assistant", "content": chatgpt_response}
            conversation_history.append(chatgpt_message)

            print("[ChatGPT]")
            print(chatgpt_response)

            result_queue.put(chatgpt_response)
            # ここで chatgpt_response を適切に処理する
            # 例えば、音声に変換して再生する
            text_to_speech(chatgpt_response)

    except sr.UnknownValueError:
        print("Sorry, I could not understand what you said. Please speak again.")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")

if __name__ == '__main__':
    app.run(debug=True)