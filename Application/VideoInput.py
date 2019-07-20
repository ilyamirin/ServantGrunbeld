try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
import aiohttp
import asyncio
import cv2


# снимает изображение с вебки и отправляет его распознавалкам и отображалке (через transceiver).
# отображалка рисует изображение пользователю и дорисовывает туда информацию, которую ей вышлют распознавалки


async def get_frame(webcam_id):
    capture_size = (640, 480)
    stream = cv2.VideoCapture(webcam_id)
    stream.set(cv2.CAP_PROP_FRAME_WIDTH, capture_size[0])
    stream.set(cv2.CAP_PROP_FRAME_HEIGHT, capture_size[1])

    while True:
        grabbed, frame = stream.read()
        if not grabbed:
            break
        assert capture_size == frame.shape[:-1][::-1]
        await asyncio.sleep(1.0 / CFG.FPS)


async def main():
    try:
        print("Trying to connect...", end=' ', flush=True)
        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as ws:
            print("connected", flush=True)
            while True:
                frame = await get_frame(0)
                message = Message(data=frame, type_=Message.VIDEO_FRAME, device_id=CFG.DEVICE_ID).dumps()
                await ws.send_bytes(message)
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
