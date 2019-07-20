try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
import asyncio
import aiohttp
import cv2


async def recv_frame():
    return None


async def recv_face_roi():
    await None


async def recv_user_request():
    await None


async def play_robovoice():
    await None


async def display_frame(message: Message):
    frame = message.data
    cv2.namedWindow(CFG.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.imshow(CFG.WINDOW_NAME, frame)


async def display_user_requests():
    while True:
        await play_robovoice()


async def handle_message(server, ws_msg):
    if ws_msg.type == aiohttp.WSMsgType.BINARY:
        message: Message = Message.loads(ws_msg.data)
        # if message.type == Message.VIDEO_FRAME:
        #     await display_frame(message)
        if message.type == Message.RECOGNIZED_SPEECH:
            print(message.data, flush=True)
    elif ws_msg.type == aiohttp.WSMsgType.ERROR:
        print('ws connection closed with exception %s' % server.exception())


async def reconnect():
    print("Trying to connect...", end=' ', flush=True)
    async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as server:
        print("connected", flush=True)
        await server.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.RECOGNIZED_SPEECH).dumps())
        await server.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.BOT_ANSWER).dumps())
        await server.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.ROBOVOICE).dumps())
        async for ws_msg in server:
            # while True:
            try:
                # ws_msg = await server.receive_bytes()
                # await asyncio.sleep(1)
                await handle_message(server, ws_msg)
            except Exception as e:
                print(f"Wtf: {e}", flush=True)


async def main():
    while True:
        try:
            await reconnect()
        except ConnectionRefusedError:
            print("refused", flush=True)
        except Exception as e:
            print(f"Unexpected exception: {e}", flush=True)
        await asyncio.sleep(CFG.RECONNECT_TIMEOUT)


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(main())
except KeyboardInterrupt:
    cv2.destroyWindow(CFG.WINDOW_NAME)

while True:
    # forall: if msg.device_id != CFG.device_id: continue

    # принимает информацию от распознавалок фото
    # try
    # face_frames = faces.recv

    # принимает фрейм от вебки и рисует его. дорисовывает рамки и имена, если надо и если они не устарели
    # video_frame = video_transceiver.recv
    # if not face_frames.old => video_frame.draw(face_frames)
    # cv2.imshow(windowName, video_frame)

    # принимает текст от распознавалки (только чтобы отобразить, если надо)
    # try
    # user_text = speech_recogn.recv
    # display(user_text)

    # принимает текст от компаньона и отображает, если надо
    # try
    # bot_text = bot.recv

    # принимает звук от синтезатора и проигрывает его
    # try
    # bot_audio = synthesis.recv
    # play(bot_audio)
    break
