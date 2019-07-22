try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
from SpeechRecognition.KaldiRecognition import KaldiOnlineRecognizer
import aiohttp
import asyncio


rec = KaldiOnlineRecognizer()
rec.start()


async def listen_recognizer(server):
    while True:
        data = await asyncio.get_event_loop().sock_recv(rec.kaldi_socket, 1024)
        if data.strip() == "":
            continue
        tp = Message.RECOGNIZED_SPEECH if '\n' in data else Message.RECOGNIZED_SPEECH_PART
        message = Message(data=data, type_=tp).dumps()
        await server.send_bytes(message)


async def main():
    try:
        print("Trying to connect...", end=' ', flush=True)
        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as mgr:
            print("connected", flush=True)
            await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.AUDIO_CHUNK).dumps())
            asyncio.get_event_loop().create_task(listen_recognizer(mgr))
            async for ws_msg in mgr:
                if ws_msg.type == aiohttp.WSMsgType.BINARY:
                    message: Message = Message.loads(ws_msg.data)
                    await asyncio.get_event_loop().sock_sendall(message.data)
                elif ws_msg.type == aiohttp.WSMsgType.ERROR:
                    print('ws connection closed with exception %s' % mgr.exception())
    except ConnectionRefusedError:
        print("refused", flush=True)
    except Exception as e:
        print(f"Unexpected exception: {e}", flush=True)
    await asyncio.sleep(CFG.RECONNECT_TIMEOUT)
    asyncio.get_event_loop().create_task(main())


asyncio.get_event_loop().create_task(main())
try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    pass
