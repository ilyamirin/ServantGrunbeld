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


async def handle_video_frame(client, message: Message):
    if message.type not in subscribers:
        return
    # for sbr in subscribers[message.type]:
    #     await sbr.send_bytes(message.dumps())


async def handle_audio_chunk(client, message: Message):
    if message.type not in subscribers:
        return


async def handle_recognized_speech(client, message: Message):
    print(message.data, flush=True)
    if message.type not in subscribers:
        return
    for sbr in subscribers[message.type]:
        await sbr.send_bytes(message.dumps())


async def handle_subscribe_intent(client, message: Message):
    if message.data not in subscribers:
        subscribers[message.data] = set()
    subscribers[message.data].add(client)


async def remove_client(client):
    global subscribers
    for lst in subscribers.values():
        lst.discard(client)


handle_message = {
    Message.AUDIO_CHUNK: handle_audio_chunk,
    Message.VIDEO_FRAME: handle_video_frame,
    Message.SUBSCRIBE: handle_subscribe_intent,
    Message.RECOGNIZED_SPEECH: handle_recognized_speech,
}


async def accept_client(request):
    client = web.WebSocketResponse()
    await client.prepare(request)
    async for ws_msg in client:
        if ws_msg.type == aiohttp.WSMsgType.BINARY:
            message: Message = Message.loads(ws_msg.data)
            await handle_message[message.type](client, message)
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


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(main())
except KeyboardInterrupt:
    pass
loop.close()

# async def listen_client(client: websockets.WebSocketClientProtocol):
#     while True:
#         data = await client.recv()
#         message = Message.loads(data)
#         # print(message.type, flush=True)
#         print(message)
#
#
# async def client_connected(client, path):
#     print(f"Connected from {path}", flush=True)
#     asyncio.get_event_loop().create_task(listen_client(client))
#
#
# acceptor = websockets.serve(client_connected, CFG.MANAGER_HOST, CFG.MANAGER_PORT, max_queue=-1)
# try:
#     asyncio.get_event_loop().run_until_complete(acceptor)
#     asyncio.get_event_loop().run_forever()
# except KeyboardInterrupt:
#     pass


# async def handle_input():
#     pass
# #
# async def handle_conn(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
#     data = await reader.read(CFG.BUFFER_LEN)
#     message = Message.loads(data)
#     print(message.type, flush=True)
#
#     sock = writer.get_extra_info('socket')
#
#     if sock is not None:
#         address = sock.getpeername() if sock else None
#         print(f"Received from {address!r}")
#         asyncio.get_event_loop().add_reader(sock, )
#     # addr = writer.get_extra_info('peername')


#
#     print(f"Received {message!r} from {addr!r}")
#
#     print(f"Send: {message!r}")
#     writer.write(data)
#     await writer.drain()
#
#     print("Close the connection")
#     writer.close()


# async def main():
#     server = await asyncio.start_server(handle_conn, CFG.MANAGER_HOST, CFG.MANAGER_PORT)
#     print(f'Serving on {server.sockets[0].getsockname()}')
#
#     async with server:
#         await server.serve_forever()
#
#
# try:
#     asyncio.run(main())
# except KeyboardInterrupt:
#     pass

#
# async def handle_connections():
#     while True:
#         await None
#
#
# loop = asyncio.get_event_loop()
# loop.create_task(handle_connections())
# try:
#     loop.run_forever()
# except KeyboardInterrupt:
#     pass
