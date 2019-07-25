try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
import asyncio
from ProjectUtils.Microphone import MicrophoneRecorder
import pyaudio
from queue import Queue, Empty
import aiohttp

# снимает звук с микрофона и отправляет его распознавалке^W менеджеру

chunks = Queue()
mic_started = False


def streamCallback(in_data, frame_count, time_info, status):
    if mic_started:
        chunks.put(in_data)
    return in_data, pyaudio.paContinue


async def send_chunks(mgr):
    while True:
        try:
            import time
            chunk = chunks.get(block=False)
            message = Message(data=chunk, type_=Message.AUDIO_CHUNK, device_id=CFG.DEVICE_ID).dumps()
            await mgr.send_bytes(message)
        except Empty:
            await asyncio.sleep(0.0001)


async def main():
    #silence = b"\0" * mic.rate * 2 * 2 * 2
    silence = open("silence", "rb").read()
    try:
        print("Trying to connect...", end=' ', flush=True)
        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as mgr:
            print("connected", flush=True)
            asyncio.get_event_loop().create_task(send_chunks(mgr))
            await asyncio.gather(
                mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.MIC_START).dumps()),
                mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.MIC_STOP).dumps())
            )
            async for ws_msg in mgr:
                global mic_started
                if ws_msg.type == aiohttp.WSMsgType.BINARY:
                    input_message = Message.loads(ws_msg.data)
                    if input_message.type == Message.MIC_START and not mic_started:
                        # mic.startStream(streamCallback)
                        print("mic started")
                        mic_started = True
                    if input_message.type == Message.MIC_STOP and mic_started:
                        # mic.stopStream()
                        chunks.put(silence)
                        mic_started = False
    except ConnectionRefusedError:
        print("refused", flush=True)
    except Exception as e:
        print(f"Unexpected exception: {e}", flush=True)
    await asyncio.sleep(CFG.RECONNECT_TIMEOUT)
    asyncio.get_event_loop().create_task(main())


mic = MicrophoneRecorder(chunkSize=4096)
mic.startStream(streamCallback)

asyncio.get_event_loop().create_task(main())

try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    mic.stopStream()
