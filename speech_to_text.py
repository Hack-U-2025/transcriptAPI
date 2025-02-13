#!/usr/bin/env python3
import asyncio
import websockets
import json
import os
from google.cloud import speech
import pyaudio

# Google Cloud認証設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_cloud_key.json"

# 音声設定
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# Speech clientの初期化
client = speech.SpeechClient()

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="ja-JP",
)

streaming_config = speech.StreamingRecognitionConfig(
    config=config, interim_results=True
)


def get_api_key():
    """APIキーを取得する関数"""
    with open("google_cloud_key.json", "r") as f:
        return json.load(f)["private_key"]


# マイクストリームを生成する関数
def mic_stream():
    audio_interface = pyaudio.PyAudio()
    audio_stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    while True:
        data = audio_stream.read(CHUNK)
        yield speech.StreamingRecognizeRequest(audio_content=data)


async def transcribe():
    """音声認識を行い、テキストを返す関数"""
    api_key = get_api_key()
    stream = client.streaming_recognize(streaming_config, mic_stream())

    for response in stream:
        for result in response.results:
            if result.is_final:
                return {"text": result.alternatives[0].transcript}


async def handle_connection(websocket):
    """クライアントとの接続を処理するコールバック関数"""
    print("クライアントが接続しました")
    try:
        while True:
            # 音声認識を実行
            result = await transcribe()
            # 結果を JSON 文字列に変換
            json_string = json.dumps(result, ensure_ascii=False)
            print(f"送信するデータ: {json_string}")
            await websocket.send(json_string)
            print("データを送信しました")
    except websockets.exceptions.ConnectionClosed:
        print("クライアントが切断されました")


async def main():
    # localhost の 8765 ポートで WebSocket サーバーを起動
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket サーバーが起動しました。クライアントの接続を待っています...")
        await asyncio.Future()  # 永続的に実行


if __name__ == "__main__":
    asyncio.run(main())
