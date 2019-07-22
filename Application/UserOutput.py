try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
import asyncio
import aiohttp
import cv2
from queue import Queue, Empty, Full
import pygame
import sys
import time


pygame.init()
mixer = pygame.mixer
mixer.init(channels=1)
frames_to_display = Queue(maxsize=CFG.FRAMES_QUEUE_MAX_LEN)


async def recv_frame():
    return None


async def recv_face_roi():
    await None


async def recv_user_request():
    await None


async def synthesize_voice(text):
    proc = await asyncio.create_subprocess_shell(
        f"text2wave -f {CFG.FESTIVAL_FREQ} -eval '(voice_msu_ru_nsh_clunits)'",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate(text.encode())
    if stderr:
        print(stderr.decode(), file=sys.stderr)
    return stdout


def play_robovoice(audio_bytes):
    sound = mixer.Sound(buffer=audio_bytes)
    sound.play()


async def display_frame(message: Message):
    frame = message.data
    try:
        frames_to_display.put_nowait(frame)
    except Full:
        frames_to_display.get_nowait()
        frames_to_display.put_nowait(frame)


async def handle_message(server, ws_msg):
    if ws_msg.type == aiohttp.WSMsgType.BINARY:
        message: Message = Message.loads(ws_msg.data)
        if message.type == Message.VIDEO_FRAME:
            await display_frame(message)
        if message.type == Message.RECOGNIZED_SPEECH_PART:
            print(message.data, flush=True)
        if message.type == Message.RECOGNIZED_SPEECH:
            print(message.data, flush=True)
            voice = await synthesize_voice(message.data)
            play_robovoice(voice)
    elif ws_msg.type == aiohttp.WSMsgType.ERROR:
        print('ws connection closed with exception %s' % server.exception())


async def reconnect():
    print("Trying to connect...", end=' ', flush=True)
    async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as mgr:
        print("connected", flush=True)
        await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.RECOGNIZED_SPEECH).dumps())
        await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.BOT_ANSWER).dumps())
        await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.ROBOVOICE).dumps())
        await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.VIDEO_FRAME).dumps())
        async for ws_msg in mgr:
            try:
                await handle_message(mgr, ws_msg)
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


async def cam():
    while True:
        try:
            frame = frames_to_display.get_nowait()
            cv2.imshow(CFG.WINDOW_NAME, frame)
            if cv2.waitKey(1) == 27:
                pass
        except Empty:
            pass
        except Exception as e:
            print(f"Unexpected exception: {e}", flush=True)
        await asyncio.sleep(1/(CFG.FPS**2))


try:
    asyncio.get_event_loop().run_until_complete(asyncio.gather(main(), cam()))
except KeyboardInterrupt:
    cv2.destroyWindow(CFG.WINDOW_NAME)
