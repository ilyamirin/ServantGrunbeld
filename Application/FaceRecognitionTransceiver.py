try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
from FaceRecognition.InsightFaceRecognition import FaceRecognizer, DataBase, RetinaFace, DetectorConfig, RecognizerConfig
import aiohttp
import asyncio

dataBase = DataBase(
    filepath="./FaceRecognitionData/Temp/users_face_exp.hdf"
)

detector = RetinaFace(
    prefix=DetectorConfig.PREFIX,
    epoch=DetectorConfig.EPOCH
)

recognizer = FaceRecognizer(
    prefix=RecognizerConfig.PREFIX,
    epoch=RecognizerConfig.EPOCH,
    dataBase=dataBase,
    detector=detector
)


async def main():
    try:
        print("Trying to connect...", end=' ', flush=True)
        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as mgr:
            print("connected", flush=True)
            await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.VIDEO_FRAME).dumps())
            async for ws_msg in mgr:
                if ws_msg.type == aiohttp.WSMsgType.BINARY:
                    input_message: Message = Message.loads(ws_msg.data)
                    if input_message.type == Message.VIDEO_FRAME:
                        output_message = Message(
                            data=recognizer.detectFaces(input_message.data),
                            type_=Message.RECOGNIZED_FACE_ROI,
                            device_id=input_message.device_id
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

