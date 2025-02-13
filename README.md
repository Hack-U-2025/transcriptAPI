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
#!/usr/bin/env python3
import asyncio
import websockets
import json
import numpy as np
import pyaudio
import deepspeech

# DeepSpeechモデルの設定
MODEL_FILE_PATH = 'path/to/your/deepspeech-0.9.3-models.pbmm'
SCORER_FILE_PATH = 'path/to/your/deepspeech-0.9.3-models.scorer'

# 音声設定
RATE = 16000
CHUNK = 1024

# DeepSpeechモデルの初期化
model = deepspeech.Model(MODEL_FILE_PATH)
model.enableExternalScorer(SCORER_FILE_PATH)

# 音声ストリーム処理
def audio_stream():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
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
```

## 3. Unity側の設定

Unityプロジェクトで以下のC#スクリプトを作成し、適当なGameObjectにアタッチします。

```csharp
using UnityEngine;
using System;
using System.Collections;
using WebSocketSharp;

public class WebSocketClient : MonoBehaviour
{
    private WebSocket ws;

    void Start()
    {
        ws = new WebSocket("ws://localhost:8765");

        ws.OnMessage += (sender, e) =>
        {
            Debug.Log("Received: " + e.Data);
            // ここで受信したテキストを処理（例：UI表示など）
        };

        ws.OnOpen += (sender, e) =>
        {
            Debug.Log("WebSocket Open");
        };

        ws.OnError += (sender, e) =>
        {
            Debug.LogError("WebSocket Error Message: " + e.Message);
        };

        ws.OnClose += (sender, e) =>
        {
            Debug.Log("WebSocket Close");
        };

        ws.Connect();
    }

    void OnDestroy()
    {
        if (ws != null)
        {
            ws.Close();
        }
    }
}
```

Unity側でWebSocketSharpライブラリを導入する必要があります。

## 4. システムの実行

1. コマンドプロンプトで以下のコマンドを実行し、Pythonスクリプトを起動します:

```bash
python speech_to_text.py
```

2. Unityプロジェクトを実行します。

3. マイクに向かって話すと、リアルタイムで文字起こしが行われ、Unity側に送信されます。

## ディレクトリ構成

```
project_root/
│
├── speech_to_text.py
├── deepspeech-0.9.3-models.pbmm
└── deepspeech-0.9.3-models.scorer
```

このシステムは、DeepSpeechを使用して完全無料で日本語のリアルタイム文字起こしを実現し、WebSocketを通じてUnityフロントエンドと通信を行います。マイクからの入力を3秒ごとに処理し、結果をJSON形式でUnityに送信します。DeepSpeechは軽量なモデルであり、GPUなしのノートPCでも比較的高速に動作します。環境設定から実装まで、一貫性のある手順で説明しました。必要に応じて、エラーハンドリングやUI実装などを追加することで、より堅牢なシステムを構築できます。

---
