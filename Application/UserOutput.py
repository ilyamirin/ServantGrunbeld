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
speech_ignored = False


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


async def ignore_speech_while_and_then(func, afunc=None):
    async def unset_when_not_func():
        while func():
            await asyncio.sleep(0.01)
        global speech_ignored
        speech_ignored = False
        if afunc:
            await afunc
    asyncio.get_event_loop().create_task(unset_when_not_func())


async def handle_message(server, ws_msg):
    if ws_msg.type == aiohttp.WSMsgType.BINARY:
        message: Message = Message.loads(ws_msg.data)
        if message.type == Message.VIDEO_FRAME:
            await display_frame(message)
        if message.type == Message.RECOGNIZED_SPEECH_PART:
            print(message.data.strip(), end="\n" if message.data.strip() else "")
        if message.type == Message.RECOGNIZED_SPEECH:
            if message.data.strip() != "":
                prefix = "" if message.type == Message.RECOGNIZED_SPEECH_PART else "Y:"
                print(prefix, message.data, flush=True)
        if message.type == Message.BOT_ANSWER and not mixer.get_busy():
            print("B:", message.data, flush=True)
            voice = await synthesize_voice(message.data)
            play_robovoice(voice)
            asyncio.get_event_loop().create_task(ignore_speech_while_and_then(
                mixer.get_busy,
                afunc=server.send_bytes(Message(type_=Message.MSG_TYPE_UNMUTE, data=Message.AUDIO_CHUNK).dumps())
            ))
        if message.type == Message.MSG_TYPE_MUTE:
            global speech_ignored
            speech_ignored = True
    elif ws_msg.type == aiohttp.WSMsgType.ERROR:
        print("ws connection closed with exception %s" % server.exception())


async def reconnect():
    print("Trying to connect...", end=' ', flush=True)
    async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as mgr:
        print("connected", flush=True)
        await asyncio.gather(
            mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.MSG_TYPE_MUTE).dumps()),
            mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.RECOGNIZED_SPEECH).dumps()),
            mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.RECOGNIZED_SPEECH_PART).dumps()),
            mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.BOT_ANSWER).dumps()),
            mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.ROBOVOICE).dumps()),
            mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.VIDEO_FRAME).dumps()))
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
            radius, color, (height, width, _) = 25, (0, 0, 255) if speech_ignored else (0, 255, 0), frame.shape
            frame = cv2.circle(frame, (width - radius, radius), radius, color, thickness=-1)
            cv2.imshow(CFG.WINDOW_NAME, frame)
            cv2.waitKey(1)
        except Empty:
            pass
        except Exception as e:
            print(f"Unexpected exception: {e}", flush=True)
        await asyncio.sleep(1/(2*CFG.FPS))


try:
    asyncio.get_event_loop().run_until_complete(asyncio.gather(main(), cam()))
except KeyboardInterrupt:
    cv2.destroyWindow(CFG.WINDOW_NAME)
