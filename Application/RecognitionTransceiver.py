try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
from SpeechRecognition.KaldiRecognition import KaldiOnlineRecognizer
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor


rec = KaldiOnlineRecognizer()
rec.start()
thread_pool_executor = ThreadPoolExecutor()
speech_ignored = False


async def listen_recognizer(server):
    prev = ""
    while True:
        data = await asyncio.get_event_loop().run_in_executor(thread_pool_executor, rec.recv)
        tp = Message.RECOGNIZED_SPEECH if b'\n' in data else Message.RECOGNIZED_SPEECH_PART
        txt = data.decode().strip()
        txt = prev if tp == Message.RECOGNIZED_SPEECH and not txt else txt
        if txt:
            prev = txt
            await server.send_bytes(Message(data=txt, type_=tp).dumps())
            print("Y:" if tp == Message.RECOGNIZED_SPEECH else "", txt, flush=True)
            if tp == Message.RECOGNIZED_SPEECH:
                global speech_ignored
                speech_ignored = True
                prev = ""
                asyncio.get_event_loop().create_task(
                    server.send_bytes(Message(type_=Message.MSG_TYPE_MUTE, data=Message.AUDIO_CHUNK).dumps())
                )


async def main():
    try:
        print("Trying to connect...", end=' ', flush=True)
        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as mgr:
            print("connected", flush=True)
            await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.AUDIO_CHUNK).dumps())
            await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.MSG_TYPE_UNMUTE).dumps())
            asyncio.get_event_loop().create_task(listen_recognizer(mgr))
            async for ws_msg in mgr:
                if ws_msg.type == aiohttp.WSMsgType.BINARY:
                    global speech_ignored
                    message: Message = Message.loads(ws_msg.data)
                    if message.type == Message.AUDIO_CHUNK and not speech_ignored:
                        await asyncio.get_event_loop().sock_sendall(rec.kaldi_socket, message.data)
                    if message.type == Message.MSG_TYPE_UNMUTE and message.data == Message.AUDIO_CHUNK:
                        speech_ignored = False
                elif ws_msg.type == aiohttp.WSMsgType.ERROR:
                    print('ws connection closed with exception %s' % mgr.exception())
    except ConnectionRefusedError:
        print("refused", flush=True)
    except KeyboardInterrupt:
        return
    except Exception as e:
        print(f"Unexpected exception: {e}", flush=True)
    await asyncio.sleep(CFG.RECONNECT_TIMEOUT)
    asyncio.get_event_loop().create_task(main())


asyncio.get_event_loop().create_task(main())
try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    pass
