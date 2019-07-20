try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
import asyncio
from ProjectUtils.Microphone import MicrophoneRecorder
import pyaudio
from queue import Queue
import aiohttp

# снимает звук с микрофона и отправляет его распознавалке^W менеджеру

chunks = Queue()


def streamCallback(in_data, frame_count, time_info, status):
    chunks.put(in_data)
    return in_data, pyaudio.paContinue


async def main():
    try:
        print("Trying to connect...", end=' ', flush=True)
        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as ws:
            print("connected", flush=True)
            while True:
                chunk = chunks.get(block=True)
                message = Message(data=chunk, type_=Message.AUDIO_CHUNK, device_id=CFG.DEVICE_ID).dumps()
                await ws.send_bytes(message)
                # await ws.send_bytes(Message(data="мартышка", type_=Message.RECOGNIZED_SPEECH, device_id=CFG.DEVICE_ID).dumps())
    except ConnectionRefusedError:
        print("refused", flush=True)
    except Exception as e:
        print(f"Unexpected exception: {e}", flush=True)
    await asyncio.sleep(CFG.RECONNECT_TIMEOUT)
    asyncio.get_event_loop().create_task(main())


mic = MicrophoneRecorder()
mic.startStream(callback=streamCallback)

asyncio.get_event_loop().create_task(main())

try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    mic.stopStream()
