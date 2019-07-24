try:
    from .Config import Config as CFG
    from .Message import Message
except ModuleNotFoundError:
    from Config import Config as CFG
    from Message import Message
import aiohttp
import asyncio
import socket
from time import sleep
from LinguoCore.Config import AimlCompanionConfig
from concurrent.futures import ThreadPoolExecutor
import json
from programy.clients.events.tcpsocket import client
# x = programy.clients.events.tcpsocket.client

thread_pool = ThreadPoolExecutor()


def connectToAiml(timeout=1, attempts=3, timeout_increment=1):
    aiml_connected = False
    aiml_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while not aiml_connected and attempts > 0:
        attempts -= 1
        timeout_, timedelta = timeout, 0.1
        timeout += timeout_increment
        aiml_connected = aiml_socket.connect_ex((AimlCompanionConfig.HOST, AimlCompanionConfig.PORT)) == 0
        while not aiml_connected and timeout_ > 0:
            timeout_ -= timedelta
            sleep(timedelta)
            aiml_connected = aiml_socket.connect_ex((AimlCompanionConfig.HOST, AimlCompanionConfig.PORT)) == 0
    return aiml_socket, aiml_connected


async def main():
    try:
        print("Trying to connect...", end=' ', flush=True)
        async with aiohttp.ClientSession() as session, session.ws_connect(CFG.MGR_WS_URI) as mgr:
            print("connected", flush=True)
            await mgr.send_bytes(Message(type_=Message.SUBSCRIBE, data=Message.RECOGNIZED_SPEECH).dumps())
            async for ws_msg in mgr:
                if ws_msg.type == aiohttp.WSMsgType.BINARY:
                    input_message: Message = Message.loads(ws_msg.data)
                    query = {
                        "userid": input_message.device_id,
                        "question": input_message.data
                    }
                    print("Y:", input_message.data, flush=True)
                    aiml_socket, aiml_connected = connectToAiml()
                    if not aiml_connected:
                        raise ConnectionRefusedError
                    await asyncio.get_event_loop().sock_sendall(aiml_socket, json.dumps(query).encode())
                    bot_answer = await asyncio.get_event_loop().run_in_executor(thread_pool, lambda: aiml_socket.recv(8192))
                    bot_answer = json.loads(bot_answer.decode())
                    output_message = Message(
                        data=bot_answer["answer"]["text"] if bot_answer["result"] == "OK" else "",
                        type_=Message.BOT_ANSWER, device_id=input_message.device_id
                    )
                    print("B:", output_message.data, flush=True)
                    await mgr.send_bytes(output_message.dumps())
                elif ws_msg.type == aiohttp.WSMsgType.ERROR:
                    print('ws connection closed with exception %s' % mgr.exception())
    except ConnectionRefusedError:
        print("refused", flush=True)
    except Exception as e:
        print(f"Unexpected exception: {e}", flush=True)
    await asyncio.sleep(CFG.RECONNECT_TIMEOUT)
    aiml_connected = False
    asyncio.get_event_loop().create_task(main())


asyncio.get_event_loop().create_task(main())
try:
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    pass
