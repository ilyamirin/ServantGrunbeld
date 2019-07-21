try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
import aiohttp
import asyncio
import cv2
import time


# снимает изображение с вебки и отправляет его распознавалкам и отображалке (через transceiver).
# отображалка рисует изображение пользователю и дорисовывает туда информацию, которую ей вышлют распознавалки


async def main():
    try:
        print("Trying to connect...", end=' ', flush=True)
        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as ws:
            print("connected", flush=True)
            cam = cv2.VideoCapture(0)
            while True:
                (grabbed, frame), now = cam.read(), time.time()
                if grabbed:
                    message = Message(data=frame, type_=Message.VIDEO_FRAME, device_id=CFG.DEVICE_ID).dumps()
                    await ws.send_bytes(message)
                await asyncio.sleep(max((now + 1.0/CFG.FPS) - time.time(), 0))
    except ConnectionRefusedError:
        print("refused", flush=True)
    except Exception as e:
        print(f"Unexpected exception: {e}", flush=True)
    await asyncio.sleep(CFG.RECONNECT_TIMEOUT)
    asyncio.get_event_loop().create_task(main())


try:
    asyncio.get_event_loop().create_task(main())
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    pass
cv2.destroyAllWindows()
