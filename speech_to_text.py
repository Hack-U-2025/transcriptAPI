import os
import time
from google.cloud import speech
import pyaudio
import websockets
import asyncio
import json

# 音声設定
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# Speech-to-Text クライアントの初期化
client = speech.SpeechClient()

config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="ja-JP",
    enable_automatic_punctuation=True,
)

streaming_config = speech.StreamingRecognitionConfig(
    config=config, interim_results=True
)


# WebSocket接続用の関数
async def send_to_unity(websocket, text):
    await websocket.send(json.dumps({"text": text}))


# マイク入力のストリーム設定
def mic_stream():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    while True:
        data = stream.read(CHUNK)
        yield speech.StreamingRecognizeRequest(audio_content=data)


# メイン処理
async def main():
    uri = "ws://localhost:8888"  # Unityのサーバーアドレス
    async with websockets.connect(uri) as websocket:
        print("Connected to Unity")

        responses = client.streaming_recognize(streaming_config, mic_stream())

        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            if result.is_final:
                print(f"Final: {transcript}")
                await send_to_unity(websocket, transcript)
            else:
                print(f"Interim: {transcript}")


if __name__ == "__main__":
    asyncio.run(main())
