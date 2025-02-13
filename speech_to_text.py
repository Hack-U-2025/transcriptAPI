import numpy as np
import pyaudio
import deepspeech
import websockets
import asyncio
import json

# DeepSpeechモデルの設定
MODEL_FILE_PATH = "path/to/your/deepspeech-0.9.3-models.pbmm"
SCORER_FILE_PATH = "path/to/your/deepspeech-0.9.3-models.scorer"

# 音声設定
RATE = 16000
CHUNK = 1024

# DeepSpeechモデルの初期化
model = deepspeech.Model(MODEL_FILE_PATH)
model.enableExternalScorer(SCORER_FILE_PATH)


# WebSocket接続用の関数
async def send_to_unity(websocket, text):
    await websocket.send(json.dumps({"text": text}))


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


# メイン処理
async def main():
    uri = "ws://localhost:8080"  # Unityのサーバーアドレス
    async with websockets.connect(uri) as websocket:
        print("Connected to Unity")

        stream = audio_stream()
        context = model.createStream()

        while True:
            data = stream.read(CHUNK)
            audio_data = np.frombuffer(data, dtype=np.int16)
            context.feedAudioContent(audio_data)
            text = context.intermediateDecode()

            if text:
                print(f"Recognized: {text}")
                await send_to_unity(websocket, text)


if __name__ == "__main__":
    asyncio.run(main())
