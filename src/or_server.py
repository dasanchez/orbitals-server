"""
Orbitals WebSockets Server
"""
import asyncio
import json
import websockets
from or_table import OrbitalsTable

orTable = OrbitalsTable(wordCount=16, turnTimeout=30)

def main():
    """ starts the game loop """
    print("State set to 'waiting-players'")
    print("Starting WebSocket server...")

    # Set up async routines
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(websockets.serve(handler, '0.0.0.0', 9001))
        loop.run_forever()
    finally:
        loop.close()

async def handle_message(websocket, data):
    """ handles incoming message from players """
    await orTable.newMessage(websocket, data)

async def handler(websocket, _):
    """ register(websocket) sends user_event() to websocket """
    await orTable.newConnection(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            print(data)
            await handle_message(websocket, data)
    finally:
        await orTable.deleteConnection(websocket)

if __name__ == "__main__":
    # program entry point
    main()
