try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
import asyncio
import aiohttp
from aiohttp import web

subscribers = {}
muted_msg_types = set()
loop = asyncio.get_event_loop()


async def transfer_to_subscribers(client, message: Message):
    try:
        await asyncio.gather(*[sbr.send_bytes(message.dumps()) for sbr in subscribers.get(message.type, [])])
    except ConnectionResetError as e:
        print(f"{e}", flush=True)
    except Exception as e:
        print(f"Unexpected exception {e}", flush=True)


async def handle_subscribe_intent(client, message: Message):
    if message.data not in subscribers:
        subscribers[message.data] = set()
    subscribers[message.data].add(client)
    print(f"{client} subscribed to {message.data}", flush=True)


async def handle_mute_intent(client, message: Message):
    if message.type == Message.MSG_TYPE_MUTE:
        muted_msg_types.add((message.device_id, message.data))
        print(f"Messages {message.data} on {message.device_id} is muted", flush=True)
    if message.type == Message.MSG_TYPE_UNMUTE:
        muted_msg_types.discard((message.device_id, message.data))
        print(f"Messages {message.data} on {message.device_id} is unmuted", flush=True)


message_type_handlers = {
    Message.BOT_ANSWER: [transfer_to_subscribers],
    Message.AUDIO_CHUNK: [transfer_to_subscribers],
    Message.VIDEO_FRAME: [transfer_to_subscribers],
    Message.RECOGNIZED_SPEECH: [transfer_to_subscribers],
    Message.RECOGNIZED_SPEECH_PART: [transfer_to_subscribers],
    Message.SUBSCRIBE: [handle_subscribe_intent],
    Message.MSG_TYPE_MUTE: [handle_mute_intent, transfer_to_subscribers],
    Message.MSG_TYPE_UNMUTE: [handle_mute_intent, transfer_to_subscribers],
    Message.RECOGNIZED_FACE_ROI: [transfer_to_subscribers],
}


async def accept_client(request):
    client = web.WebSocketResponse()
    await client.prepare(request)
    async for ws_msg in client:
        if ws_msg.type == aiohttp.WSMsgType.BINARY:
            message: Message = Message.loads(ws_msg.data)
            if (message.device_id, message.type) not in muted_msg_types:
                await asyncio.gather(*[h(client, message) for h in message_type_handlers[message.type]])
        elif ws_msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % client.exception())
    return web.Response(text="OK")


async def main():
    server = web.Server(accept_client)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, CFG.MANAGER_HOST, CFG.MANAGER_PORT, reuse_address=True)
    await site.start()
    print(f"======= Serving on {CFG.MGR_WS_URI} ======")
    await asyncio.sleep(100 * 3600)


async def txt():
    while True:
        await transfer_to_subscribers(None, Message(data="привет", type_=Message.RECOGNIZED_SPEECH))
        await asyncio.sleep(2)

# loop.create_task(txt())

try:
    loop.run_until_complete(main())
except KeyboardInterrupt:
    pass
