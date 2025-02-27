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


async def listen_recognizer(server):
    while True:
        data = await asyncio.get_event_loop().run_in_executor(thread_pool_executor, rec.recv)
        tp = Message.RECOGNIZED_SPEECH if b'4' in data else Message.RECOGNIZED_SPEECH_PART
        txt_debug = data.decode()
        # Гм, это можно сделать лучше
        txt = data.decode().replace("1", "").replace("2", "").replace("3", "").replace("4", "").replace("гм", "").strip()
        if txt and txt != "гм":
            await server.send_bytes(Message(data=txt, type_=tp).dumps())
            print("Y:" if tp == Message.RECOGNIZED_SPEECH else "", txt_debug, flush=True)


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
                    message: Message = Message.loads(ws_msg.data)
                    if message.type == Message.AUDIO_CHUNK:
                        # print("got chunk:", len(message.data))
                        await asyncio.get_event_loop().sock_sendall(rec.kaldi_socket, message.data)
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
