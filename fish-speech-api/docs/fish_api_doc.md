Raw WebSocket API Usage
The WebSocket API provides real-time, bidirectional communication for Text-to-Speech streaming. Here’s how the protocol works:

​
WebSocket Protocol
Connection Endpoint:

URL: wss://api.fish.audio/v1/tts/live
Connection Headers:

Authorization: Bearer token authentication with your API key
model (optional): Specify which TTS model to use. Available options include:
speech-1.5 (default)
speech-1.6
s1
s1-mini
Events:

a. start - Initializes the TTS session:


Copy
{
  "event": "start",
  "request": {
    "text": "",  // Initial empty text
    "latency": "normal",  // "normal" or "balanced"
    "format": "opus",  // "opus", "mp3", or "wav"
    "temperature": 0.7,  // Controls randomness in speech generation
    "top_p": 0.7,  // Controls diversity via nucleus sampling
    // Optional: Use prosody to control speech speed and volume
    "prosody": {
      "speed": 1.0,  // Speech speed (0.5-2.0)
      "volume": 0    // Volume adjustment in dB
    },
    "reference_id": "MODEL_ID_UPLOADED_OR_CHOSEN_FROM_PLAYGROUND"
    // Optional: Use reference audio instead of reference_id
    "references": [{
      "audio": "<binary_audio_data>",
      "text": "Reference text for the audio"
    }],
  }
}
b. text - Sends text chunks:


Copy
{
  "event": "text",
  "text": "Hello world " // Don't forget the space since all text is concatenated
}
There is a text buffer on the server side. Only when this buffer reaches a certain size will an audio event be generated.

Sending a stop event will force the buffer to be flushed, return an audio event, and end the session.

c. audio - Receives audio data (server response):


Copy
{
  "event": "audio",
  "audio": "<binary_audio_data>",
  "time": 3.012 // Time taken in milliseconds
}
d. stop - Ends the session:


Copy
{
  "event": "stop"
}
e. flush - Flushes the text buffer: This immediately generates the audio and returns it, if text is too short, it may lead to under-quality audio.


Copy
{
  "event": "flush"
}
f. finish - Ends the session (server side):


Copy
{
  "event": "finish",
  "reason": "stop" // or "error"
}
g. log - Logs messages from the server if debug is true:


Copy
{
  "event": "log",
  "message": "Log message from server"
}
Message Format: All messages use MessagePack encoding

​
Example Usage with OpenAI + MPV
websocket_example.py

Copy
import asyncio
import websockets
import ormsgpack
import subprocess
import shutil
from openai import AsyncOpenAI

aclient = AsyncOpenAI()


def is_installed(lib_name):
    """Check if a system command is available"""
    return shutil.which(lib_name) is not None


async def stream_audio(audio_stream):
    """
    Stream audio data using mpv player
    Args:
        audio_stream: Async iterator yielding audio chunks
    """
    if not is_installed("mpv"):
        raise ValueError(
            "mpv not found, necessary to stream audio. "
            "Install instructions: https://mpv.io/installation/"
        )

    # Initialize mpv process for real-time audio playback
    mpv_process = subprocess.Popen(
        ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    async for chunk in audio_stream:
        if chunk:
            mpv_process.stdin.write(chunk)
            mpv_process.stdin.flush()

    if mpv_process.stdin:
        mpv_process.stdin.close()
    mpv_process.wait()


async def text_to_speech_stream(text_iterator):
    """
    Stream text to speech using WebSocket API
    Args:
        text_iterator: Async iterator yielding text chunks
    """
    uri = "wss://api.fish.audio/v1/tts/live"  # Updated URI

    async with websockets.connect(
        uri, extra_headers={"Authorization": f"Bearer YOUR_API_KEY"}
    ) as websocket:
        # Send initial configuration
        await websocket.send(
            ormsgpack.packb(
                {
                    "event": "start",
                    "request": {
                        "text": "",
                        "latency": "normal",
                        "format": "opus",
                        "reference_id": "MODEL_ID_UPLOADED_OR_CHOSEN_FROM_PLAYGROUND",
                    },
                    "debug": True,  # Added debug flag
                }
            )
        )

        # Handle incoming audio data
        async def listen():
            while True:
                try:
                    message = await websocket.recv()
                    data = ormsgpack.unpackb(message)
                    if data["event"] == "audio":
                        yield data["audio"]
                except websockets.exceptions.ConnectionClosed:
                    break

        # Start audio streaming task
        listen_task = asyncio.create_task(stream_audio(listen()))

        # Stream text chunks
        async for text in text_iterator:
            if text:
                await websocket.send(ormsgpack.packb({"event": "text", "text": text}))

        # Send stop signal
        await websocket.send(ormsgpack.packb({"event": "stop"}))
        await listen_task


async def chat_completion(query):
    """Retrieve text from OpenAI and pass it to the text-to-speech function."""
    response = await aclient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": query}],
        max_completion_tokens=512,
        temperature=1,
        stream=True,
    )

    async def text_iterator():
        async for chunk in response:
            delta = chunk.choices[0].delta
            yield delta.content

    await text_to_speech_stream(text_iterator())  # Updated function name


# Main execution
if __name__ == "__main__":
    user_query = "Hello, tell me a very short story, including filler words, don't use * or #."
    asyncio.run(chat_completion(user_query))
This example demonstrates:

Real-time text streaming with WebSocket connection
Handling audio chunks as they arrive
Using MPV player for real-time audio playback
Reference audio support for voice cloning
Proper connection handling and cleanup
Make sure to install required dependencies:


Copy
pip install websockets ormsgpack openai
And install MPV player for audio playback (optional):

Linux: apt-get install mpv
macOS: brew install mpv
Windows: Download from mpv.io