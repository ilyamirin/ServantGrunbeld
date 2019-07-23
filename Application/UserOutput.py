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
import numpy as np
import sys
import time
from PIL import Image, ImageDraw, ImageFont


pygame.init()
mixer = pygame.mixer
mixer.init(channels=1)
frames_to_display = Queue(maxsize=CFG.FRAMES_QUEUE_MAX_LEN)
speech_ignored = False
current_phrase, last_recognized_phrase = "", ""
dialogue_you_bot = []


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


def add_frame_to_queue(message: Message):
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


async def handle_bot_answer(server, message: Message):
    voice = await synthesize_voice(message.data)
    play_robovoice(voice)
    asyncio.get_event_loop().create_task(ignore_speech_while_and_then(
        mixer.get_busy,
        afunc=server.send_bytes(Message(type_=Message.MSG_TYPE_UNMUTE, data=Message.AUDIO_CHUNK).dumps())
    ))


async def handle_message(server, ws_msg):
    if ws_msg.type == aiohttp.WSMsgType.BINARY:
        message: Message = Message.loads(ws_msg.data)

        if message.type == Message.VIDEO_FRAME:
            add_frame_to_queue(message)

        if message.type == Message.RECOGNIZED_SPEECH_PART:
            global current_phrase
            current_phrase = message.data.strip()
            if current_phrase:
                print(current_phrase)

        if message.type == Message.RECOGNIZED_SPEECH:
            if message.data.strip() != "":
                global last_recognized_phrase
                prefix = "" if message.type == Message.RECOGNIZED_SPEECH_PART else "Y:"
                current_phrase = last_recognized_phrase = message.data.strip()
                print(prefix, last_recognized_phrase, flush=True)

        if message.type == Message.BOT_ANSWER and not mixer.get_busy():
            dialogue_you_bot.append((last_recognized_phrase, message.data))
            if len(dialogue_you_bot) > 10:
                dialogue_you_bot.pop(0)
            print("B:", message.data, flush=True)
            asyncio.get_event_loop().create_task(handle_bot_answer(server, message))

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

            font_size, font_face, font_scale, text_thick = 16, cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 1, 3
            text_field = Image.new("RGB", (width*3//2, height), (255, 255, 255))
            draw = ImageDraw.Draw(text_field)
            unicode_font = ImageFont.truetype("DejaVuSans.ttf", font_size)
            draw.text((0, height - 3*font_size//2), current_phrase, font=unicode_font, fill=(0, 0, 0))
            newlines = 0
            for y, b in dialogue_you_bot:
                draw.text((0, newlines*font_size), y, font=unicode_font, fill=(0, 0, 255))
                draw.text((0, (newlines + 1) * font_size), b, font=unicode_font, fill=(255, 0, 0))
                newlines += 2 + b.count('\n')

            text_field = np.array(text_field)

            frame = np.concatenate((frame, text_field), axis=1)
            cv2.imshow(CFG.WINDOW_NAME, frame)
            cv2.waitKey(1)
        except Empty:
            pass
        except Exception as e:
            print(f"Unexpected exception: {e}", flush=True)
        await asyncio.sleep(1/(4*CFG.FPS))

cv2.namedWindow(CFG.WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(CFG.WINDOW_NAME, *[256*x for x in ((4 + 4*3//2), 3)])
try:
    asyncio.get_event_loop().run_until_complete(asyncio.gather(main(), cam()))
except KeyboardInterrupt:
    cv2.destroyWindow(CFG.WINDOW_NAME)
