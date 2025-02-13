完全無料のAPIを使用し、日本語でリアルタイム文字起こしを行うシステムを構築します。この要件を満たすために、Mozillaが開発したオープンソースの音声認識モデルである「DeepSpeech」を使用します。

## 1. 環境設定

1. Python 3.11.9がインストールされていることを確認します。

2. 必要なライブラリをインストールします:

```bash
pip install deepspeech pyaudio numpy websockets
```

3. DeepSpeechの日本語モデルをダウンロードします:
   - <https://github.com/mozilla/DeepSpeech/releases> から最新の日本語モデルをダウンロードし、プロジェクトフォルダに配置します。

## 2. 音声入力とDeepSpeech連携

`speech_to_text.py`ファイルを作成し、以下のコードを記述します:

```python
import numpy as np
import pyaudio
import deepspeech
import websockets
import asyncio
import json

# DeepSpeechモデルの設定
MODEL_FILE_PATH = 'path/to/your/deepspeech-0.9.3-models.pbmm'
SCORER_FILE_PATH = 'path/to/your/deepspeech-0.9.3-models.scorer'

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
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    
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
```

## 3. Unity側の設定

UnityプロジェクトでWebSocketサーバーを設定し、受信したテキストを表示するスクリプトを作成します。この部分はUnity側で実装する必要があります。

## 4. システムの実行

1. Unityプロジェクトを実行し、WebSocketサーバーを起動します。

2. コマンドプロンプトで以下のコマンドを実行し、Pythonスクリプトを起動します:

```bash
python speech_to_text.py
```

3. マイクに向かって話すと、リアルタイムで文字起こしが行われ、Unity側に送信されます。

## ディレクトリ構成

```
project_root/
│
├── speech_to_text.py
├── deepspeech-0.9.3-models.pbmm
└── deepspeech-0.9.3-models.scorer
```

このシステムは、DeepSpeechを使用して完全無料で日本語のリアルタイム文字起こしを実現します。マイクからの入力をリアルタイムで処理し、結果をWebSocketを通じてUnityに送信します。DeepSpeechは軽量なモデルであり、GPUなしのノートPCでも比較的高速に動作します。環境設定から実装まで、一貫性のある手順で説明しました。必要に応じて、Unity側の実装やエラーハンドリングなどを追加することで、より堅牢なシステムを構築できます。

Citations:
[1] <https://mojiokoshi3.com/ja/post/free-9-tools-ai-transcription/>
[2] <https://note.com/nyosubro/n/n8f4a670c6953>
[3] <https://qiita.com/ryosuke_ohori/items/9634c1fd8a9cc9ff7c36>
[4] <https://withteam.jp/mojiokoshi/blog/application%EF%BC%BFtool/>
[5] <https://jitera.com/ja/insights/24922>
[6] <https://qiita.com/ysugiyama12/items/bf246e80ae4d1dc16441>
[7] <https://cloud.google.com/speech-to-text?hl=ja>
[8] <https://ainow.jp/deepgram/>

---
