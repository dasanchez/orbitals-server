import argparse
import asyncio
import websockets
import json
from pprint import pprint
import pytest
from orbitals_ws_server import Orbitals_WS_Server


async def connect_player(name: str, uri: str):
    ws = await websockets.connect(uri)
    await ws.recv()  # "provide name" response
    packet = json.dumps({"type": "name-request", "name": name})
    await ws.send(packet)
    await ws.recv()
    return ws


async def clean_connect_player(name: str, uri: str, players):
    ws = await websockets.connect(uri)
    await ws.recv()  # "provide name" response
    packet = json.dumps({"type": "name-request", "name": name})
    await ws.send(packet)
    await ws.recv()
    await ws.recv()
    for p in players:
        await p.recv()
    return ws


async def request_team(ws, team: str, players):
    packet = json.dumps({"type": "team-request", "team": team})
    await ws.send(packet)
    await ws.recv()
    for p in players:
        await p.recv()


async def request_role(ws, role: str, players):
    packet = json.dumps({"type": "role-request", "role": role})
    await ws.send(packet)
    await ws.recv()
    for p in players:
        await p.recv()


@pytest.mark.asyncio
async def test_hub_player():
    srv = Orbitals_WS_Server(timeout=30, server_port=9000)
    await srv.start_server()

    uri = "ws://localhost:9000"

    # CLIENT MUST:
    # CONNECT WITH NAME "PLAYER"
    # AND JOIN THE BLUE TEAM

    while "Player" not in srv._tm._table._players:
        await asyncio.sleep(0.1)

    while srv._tm._table._players["Player"][0] != "blue":
        await asyncio.sleep(0.1)

    print("\nPlayer has orbital role")

    b2 = await connect_player("Blue2", uri)
    packet = json.dumps({"type": "team-request", "team": "blue"})
    await b2.send(packet)
    await b2.recv()
    packet = json.dumps({"type": "role-request", "role": "hub"})
    await b2.send(packet)
    await b2.recv()
    packet = json.dumps({"type": "team-request", "team": "orange"})
    o1 = await connect_player("Orange1", uri)
    await o1.send(packet)
    await b2.recv()
    await o1.recv()
    o2 = await connect_player("Orange2", uri)
    await o2.send(packet)
    packet = json.dumps({"type": "role-request", "role": "hub"})
    await o1.send(packet)
    packet = json.dumps({"type": "start-request"})
    await o1.send(packet)
    await b2.send(packet)

    await asyncio.sleep(1)

    packet = json.dumps({"type": "new-clue", "clue":"FRUIT", "count":1})
    await b2.send(packet)
    packet = json.dumps({"type": "clue-approved"})
    await o1.send(packet)

    await asyncio.sleep(0.1)

    # CLIENT MUST SUBMIT GUESS
    status = srv._tm._table.status()
    while status["game_state"] == "WAITING_GUESS":
        status = srv._tm._table.status()
        await asyncio.sleep(0.1)
    print("Player has submitted guess")

    await asyncio.sleep(1)

    packet = json.dumps({"type": "new-clue", "clue": "COUNTRY", "count": 2})
    await o1.send(packet)

    await asyncio.sleep(0.1)

    packet = json.dumps({"type":"clue-approved"})
    await b2.send(packet)
    await asyncio.sleep(0.1)


    # # CLIENT MUST APPROVE CLUE

    # status = srv._tm._table.status()
    # while status["game_state"] == "WAITING_APPROVAL":
    #     status = srv._tm._table.status()
    #     await asyncio.sleep(0.1)
    # print("Player has responded to clue")

    # packet = json.dumps({"type": "new-guess", "guess": "MEXICO"})
    # await o2.send(packet)
    # await asyncio.sleep(0.1)

    # packet = json.dumps({"type": "new-guess", "guess": "INDIA"})
    # await o2.send(packet)
    # await asyncio.sleep(0.1)

    # # CLIENT MUST SUBMIT SECOND CLUE
    # status = srv._tm._table.status()
    # while status["game_state"] == "WAITING_CLUE":
    #     status = srv._tm._table.status()
    #     await asyncio.sleep(0.1)
    # print("Player has submitted clue")

    # packet = json.dumps({"type": "clue-approved"})
    # await o1.send(packet)
    # await asyncio.sleep(0.01)

    # for word in ["BOMB", "CROWN", "DAD", "EASTER", "FLAG", "GIANT", "HOME"]:
    #     packet = json.dumps({"type": "new-guess", "guess": word})
    #     await b2.send(packet)
    #     await asyncio.sleep(0.1)

    # # await asyncio.sleep(0.5)

    # # STATE MUST BE GAME_OVER NOW

    # status = srv._tm._table.status()
    # print(status["game_state"])

    # # WAIT FOR PLAYER TO HIT REPLAY
    # while not srv._tm._table._players["Player"][2]:
    #     await asyncio.sleep(0.1)
    # print("Player has requested replay")
    
    # packet = json.dumps({"type": "replay-request"})
    # await b2.send(packet)
    # await o1.send(packet)
    # await o2.send(packet)
    # await asyncio.sleep(0.2)


    await b2.close()
    await o1.close()
    await o2.close()
    # status = srv._tm._table.status()
    # print(status["game_state"])

    await srv.stop_server()
