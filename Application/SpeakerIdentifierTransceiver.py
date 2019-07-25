import asyncio
import aiohttp

from array import array

try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message

from SpeechIdentification.PytorchIdentification import DataBase, Identifier, IdentifierConfig
from ProjectUtils.Microphone import MicrophoneRecorder


dataBase = DataBase(
    filepath=IdentifierConfig.DATA_BASE_PATH
)

identifier = Identifier(
    modelpath=IdentifierConfig.MODEL_PATH,
    dataBase=dataBase
)

voice = array("h")
rate = 16000
sec_threshold = 2

async def main():
    global voice

    try:
        print("Trying to connect...", end=' ', flush=True)

        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as mgr:
            print("connected", flush=True)

            await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.AUDIO_CHUNK).dumps())

            async for ws_msg in mgr:
                if ws_msg.type == aiohttp.WSMsgType.BINARY:
                    message: Message = Message.loads(ws_msg.data)

                    if message.type == Message.AUDIO_CHUNK:
                        chunk = array("h", message.data)
                        voice.extend(chunk)

                        if len(voice) // rate >= sec_threshold:
                            voice = MicrophoneRecorder.trim(voice, 500)
                            voice = MicrophoneRecorder.normalize(voice, 16384)

                            if len(voice) < len(chunk):
                                continue

                            voice = MicrophoneRecorder.convertToWAVFile(voice, 2, 16000)
                            name, _ = identifier.identifyViaFile(voice, unknownThreshold=0.25)

                            voice = array("h")
                            print(name)

                            output_message = Message(
                                data=name,
                                type_=Message.RECOGNIZED_FACE_ROI,
                                device_id=message.device_id
                            )

                            asyncio.get_event_loop().create_task(mgr.send_bytes(output_message.dumps()))

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