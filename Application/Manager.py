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
loop = asyncio.get_event_loop()


async def transfer_to_subscribers(client, message: Message):
    for sbr in subscribers.get(message.type, []):
        await sbr.send_bytes(message.dumps())


async def handle_subscribe_intent(client, message: Message):
    if message.data not in subscribers:
        subscribers[message.data] = set()
    subscribers[message.data].add(client)


async def remove_client(client):
    global subscribers
    for lst in subscribers.values():
        lst.discard(client)


message_type_handlers = {
    Message.AUDIO_CHUNK: [transfer_to_subscribers],
    Message.VIDEO_FRAME: [transfer_to_subscribers],
    Message.RECOGNIZED_SPEECH: [transfer_to_subscribers],
    Message.RECOGNIZED_SPEECH_PART: [transfer_to_subscribers],
    Message.SUBSCRIBE: [handle_subscribe_intent],
}


async def accept_client(request):
    client = web.WebSocketResponse()
    await client.prepare(request)
    async for ws_msg in client:
        if ws_msg.type == aiohttp.WSMsgType.BINARY:
            message: Message = Message.loads(ws_msg.data)
            for handle in message_type_handlers[message.type]:
                await handle(client, message)
        elif ws_msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % client.exception())
    return web.Response(text="OK")


async def main():
    server = web.Server(accept_client)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, CFG.MANAGER_HOST, CFG.MANAGER_PORT)
    await site.start()
    print(f"======= Serving on {CFG.MGR_WS_URI} ======")
    await asyncio.sleep(100 * 3600)


try:
    loop.run_until_complete(main())
except KeyboardInterrupt:
    pass
