#!/usr/bin/env python3
import asyncio
import websockets
import json
import numpy as np
import pyaudio
import deepspeech

# DeepSpeechモデルの設定
MODEL_FILE_PATH = "path/to/your/deepspeech-0.9.3-models.pbmm"
SCORER_FILE_PATH = "path/to/your/deepspeech-0.9.3-models.scorer"

# 音声設定
RATE = 16000
CHUNK = 1024

# DeepSpeechモデルの初期化
model = deepspeech.Model(MODEL_FILE_PATH)
model.enableExternalScorer(SCORER_FILE_PATH)


# 音声ストリーム処理
def audio_stream():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    return stream


# 文字起こし処理
def transcribe():
    stream = audio_stream()
    context = model.createStream()

    # 3秒間の音声を録音して文字起こし
    for _ in range(int(RATE / CHUNK * 3)):
        data = stream.read(CHUNK)
        audio_data = np.frombuffer(data, dtype=np.int16)
        context.feedAudioContent(audio_data)

    text = context.finishStream()
    return {"text": text}


async def handle_connection(websocket):
    """
    クライアントから接続があるごとに呼び出されるコールバック関数
    """
    print("クライアントが接続しました")
    try:
        while True:
            # 音声を録音し、文字起こしを実行する
            result = await asyncio.to_thread(transcribe)
            # 結果の辞書を JSON 文字列に変換（ensure_ascii=False で日本語もそのまま表示）
            json_string = json.dumps(result, ensure_ascii=False)
            print(f"送信するデータ: {json_string}")
            await websocket.send(json_string)
            print("データを送信しました")
            # 3秒ごとに処理を繰り返す
    except websockets.exceptions.ConnectionClosed:
        print("クライアントが切断されました")


async def main():
    # localhost の 8765 ポートで WebSocket サーバーを起動
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket サーバーが起動しました。クライアントの接続を待っています...")
        await asyncio.Future()  # 永続的に実行


if __name__ == "__main__":
    asyncio.run(main())
