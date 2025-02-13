## 1. 環境設定

1. Python 3.11.9がインストールされていることを確認します。

2. 新しいプロジェクトフォルダを作成し、その中に移動します。

3. 仮想環境を作成し、有効化します：

```
python -m venv venv
venv\Scripts\activate
```

4. 必要なライブラリをインストールします：

```
pip install google-cloud-speech pyaudio websockets
```

5. `requirements.txt` ファイルを作成します：

```
google-cloud-speech==2.21.0
pyaudio==0.2.13
websockets==11.0.3
```

## 2. Google Cloud設定

1. Google Cloud Consoleにアクセスし、新しいプロジェクトを作成します。

2. Speech-to-Text APIを有効にします。

3. サービスアカウントを作成し、JSONキーファイルをダウンロードします。

4. ダウンロードしたJSONキーファイルを `google_cloud_key.json` という名前でプロジェクトフォルダに配置します。

## 3. 音声認識とWebSocket通信の実装

`speech_to_text.py` ファイルを作成し、以下のコードを記述します：

```python
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
    with open('google_cloud_key.json', 'r') as f:
        return json.load(f)['private_key']

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
```

## 4. Unity側の設定

Unity プロジェクトで以下の C# スクリプトを作成し、適当な GameObject にアタッチします。

```csharp
using UnityEngine;
using System;
using WebSocketSharp;
using Newtonsoft.Json.Linq;

public class WebSocketClient : MonoBehaviour
{
    private WebSocket ws;

    void Start()
    {
        ws = new WebSocket("ws://localhost:8765");

        ws.OnMessage += (sender, e) =>
        {
            JObject json = JObject.Parse(e.Data);
            string text = (string)json["text"];
            Debug.Log("Received: " + text);
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

Unity 側で WebSocketSharp と Newtonsoft.Json ライブラリを導入する必要があります。

## 5. システムの実行

1. コマンドプロンプトで以下のコマンドを実行し、Python スクリプトを起動します：

```
python speech_to_text.py
```

2. Unity プロジェクトを実行します。

3. マイクに向かって話すと、リアルタイムで文字起こしが行われ、Unity 側に送信されます。

## 6. GitHub での共有準備

1. `.gitignore` ファイルを作成し、以下の内容を記述します：

```
# Python
__pycache__/
*.py[cod]
*$py.class
venv/

# Google Cloud API Key
google_cloud_key.json

# Unity
/[Ll]ibrary/
/[Tt]emp/
/[Oo]bj/
/[Bb]uild/
/[Bb]uilds/
/[Ll]ogs/
/[Uu]ser[Ss]ettings/

# IDE
.vscode/
.idea/

# OS generated
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
```

2. `README.md` ファイルを作成し、プロジェクトの説明、セットアップ手順、使用方法などを記述します。

3. `LICENSE` ファイルを作成し、適切なライセンス（例：MIT ライセンス）を記述します。

## ディレクトリ構成

```
project_root/
│
├── speech_to_text.py
├── requirements.txt
├── google_cloud_key.json
├── .gitignore
├── README.md
└── LICENSE
```

このシステムは、Google Cloud Speech-to-Text APIを使用して、日本語のリアルタイム文字起こしを実現します。マイクからの入力をリアルタイムで処理し、結果を WebSocket を通じて Unity に送信します。APIキーは簡単に変更できるよう、別ファイルで管理しています。環境設定から実装、GitHub での共有準備まで、一貫性のある手順で説明しました。必要に応じて、エラーハンドリングや UI 実装などを追加することで、より堅牢なシステムを構築できます。

---
