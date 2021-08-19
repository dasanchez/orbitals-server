import argparse
import asyncio
import websockets
import json
from pprint import pprint
import pytest
from orbitals_ws_server import Orbitals_WS_Server

async def connect_player(name: str, uri: str):
    ws = await websockets.connect(uri)
    await ws.recv() # "provide name" response
    packet = json.dumps({"type":"name-request","name":name})
    await ws.send(packet)
    await ws.recv()
    return ws

async def clean_connect_player(name: str, uri: str, players):
    ws = await websockets.connect(uri)
    await ws.recv() # "provide name" response
    packet = json.dumps({"type":"name-request","name":name})
    await ws.send(packet)
    await ws.recv()
    await ws.recv()
    for p in players:
        await p.recv()
    return ws

async def request_team(ws, team: str, players):
    packet = json.dumps({"type":"team-request","team":team})
    await ws.send(packet)
    await ws.recv()
    for p in players:
        await p.recv()

async def request_role(ws, role: str, players):
    packet = json.dumps({"type":"role-request","role":role})
    await ws.send(packet)
    await ws.recv()
    for p in players:
        await p.recv()

@pytest.fixture
async def start_orbitals_server():
    messages = [""]
    srv = Orbitals_WS_Server(server_out=messages)
    messages.pop()
    await srv.start_server()
    yield srv, messages

@pytest.fixture
async def ready_players():
    messages = [""]
    players = []
    srv = Orbitals_WS_Server(server_out=messages)
    messages.pop()
    await srv.start_server()
    uri = "ws://localhost:" + str(srv.serverPort())
    
    # populate players
    ann = await clean_connect_player("Ann", uri, players)
    players.append(ann)
    await request_team(ann, "blue", players)
    await request_role(ann, "hub", players)
    bob = await clean_connect_player("Bob", uri, players)
    players.append(bob)
    await request_team(bob, "blue", players)
    eve = await clean_connect_player("Eve", uri, players)
    players.append(eve)
    await request_team(eve, "orange", players)
    await request_role(eve, "hub", players)
    fog = await clean_connect_player("Fog", uri, players)
    players.append(fog)
    await request_team(fog, "orange", players)
 

    yield srv, messages, players

@pytest.fixture
async def start_game():
    messages = [""]
    players = []
    # srv = Orbitals_WS_Server(server_out=messages, timeout=0.05)
    srv = Orbitals_WS_Server(server_out=messages)
    messages.pop()
    await srv.start_server()
    uri = "ws://localhost:" + str(srv.serverPort())
    
    # populate players
    ann = await clean_connect_player("Ann", uri, players)
    players.append(ann)
    await request_team(ann, "blue", players)
    await request_role(ann, "hub", players)
    bob = await clean_connect_player("Bob", uri, players)
    players.append(bob)
    await request_team(bob, "blue", players)
    eve = await clean_connect_player("Eve", uri, players)
    players.append(eve)
    await request_team(eve, "orange", players)
    await request_role(eve, "hub", players)
    fog = await clean_connect_player("Fog", uri, players)
    players.append(fog)
    await request_team(fog, "orange", players)
 
    # start game
    packet = json.dumps({"type":"start-request"})
    await ann.send(packet)
    for p in players:
        await p.recv()
    await eve.send(packet)
    for p in players:
        await p.recv()
        

    yield srv, messages, players

@pytest.mark.asyncio
async def test_start_stop_server(start_orbitals_server):
    srv, msg = start_orbitals_server
    assert msg.pop()["status"] == "Server is running"
    await srv.stop_server()
    assert msg.pop()["status"] == "Server is not running"

@pytest.mark.asyncio
async def test_player_connection():
    messages = [""]
    srv = Orbitals_WS_Server(server_out=messages)
    messages.pop()
    await srv.start_server()
    
    uri = "ws://localhost:" + str(srv.serverPort())
    async with websockets.connect(uri) as websocket:
        greeting = json.loads(await websocket.recv())
        assert greeting["msg"] == "provide name"
    
    await srv.stop_server()   

@pytest.mark.asyncio
async def test_name_request(start_orbitals_server):
    srv, _ = start_orbitals_server
    uri = "ws://localhost:" + str(srv.serverPort())

    ws = await connect_player("Ann", uri)

    ws2 = await websockets.connect(uri)
    await ws2.recv()
    packet = json.dumps({"type":"name-request","name":"Ann"})
    await ws2.send(packet)
    resp = json.loads(await ws2.recv())
    assert resp["msg"] == "player name exists"
    
    await ws.close()
    await ws2.close()
    
    await srv.stop_server()

@pytest.mark.asyncio
async def test_team_request(start_orbitals_server):
    srv, _ = start_orbitals_server
    uri = "ws://localhost:" + str(srv.serverPort())

    ws = await connect_player("Ann", uri)
    await ws.recv()
    packet = json.dumps({"type":"team-request","team":"blue"})
    await ws.send(packet)
    resp = json.loads(await ws.recv())
    assert resp["msg"] == "team accepted"
    await ws.close()    
    await srv.stop_server()

@pytest.mark.asyncio
async def test_role_request(start_orbitals_server):
    srv, _ = start_orbitals_server
    uri = "ws://localhost:" + str(srv.serverPort())

    ws = await connect_player("Ann", uri)
    await ws.recv()
    packet = json.dumps({"type":"team-request","team":"blue"})
    await ws.send(packet)
    await ws.recv()
    await ws.recv()
    packet = json.dumps({"type":"role-request","role":"hub"})
    await ws.send(packet)
    resp = json.loads(await ws.recv())
    assert resp["msg"] == "role accepted"

    await ws.close()
    await srv.stop_server()

@pytest.mark.asyncio
async def test_start_game(ready_players):
    srv, _, players = ready_players
    packet = json.dumps({"type":"status-request"})
    await players[0].send(packet)
    resp = json.loads(await players[0].recv())
    assert resp["status"]["game_state"] == "WAITING_START"
    packet = json.dumps({"type":"start-request"})
    await players[0].send(packet)
    # clear broadcast
    for p in players:
        await p.recv()
    await players[2].send(packet)
    resp = json.loads(await players[2].recv())
    assert resp["status"]["game_state"] == "WAITING_CLUE"
    
    for p in players:
        await p.close()
    await srv.stop_server()

@pytest.mark.asyncio
async def test_waiting_start_to_waiting_players(ready_players):
    # reset to WAITING_PLAYERS after critical player leaves
    srv, _, players = ready_players
    packet = json.dumps({"type":"status-request"})
    await players[0].send(packet)
    resp = json.loads(await players[0].recv())
    assert resp["status"]["game_state"] == "WAITING_START"
    
    await players[0].close()
    del players[0]
    resp = json.loads(await players[0].recv())
    assert resp["status"]["game_state"] == "WAITING_PLAYERS"

    for p in players:
        await p.close()
    await srv.stop_server()

@pytest.mark.asyncio
async def test_waiting_clue_to_waiting_players(start_game):
    # reset to WAITING_PLAYERS after critical player leaves
    srv, _, players = start_game
    packet = json.dumps({"type":"status-request"})
    await players[0].send(packet)
    resp = json.loads(await players[0].recv())
    assert resp["status"]["game_state"] == "WAITING_CLUE"
    
    await players[0].close()
    del players[0]
    resp = json.loads(await players[0].recv())
    assert resp["status"]["game_state"] == "WAITING_PLAYERS"

    for p in players:
        await p.close()
    await srv.stop_server()

@pytest.mark.asyncio
async def test_end_turn(start_game):
    # end turn voluntarily after getting the first guess correct
    srv, _, players = start_game
    packet = json.dumps({"type":"new-clue","clue":"EVERYTHING","count":8})
    await players[0].send(packet)
    await players[0].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"clue-approved"})
    await players[2].send(packet)
    resp = json.loads(await players[2].recv())
    for p in players:
        await p.recv()

    # send first guess
    packet = json.dumps({"type":"new-guess","guess":"APPLE"})
    await players[1].send(packet)
    await players[1].recv()
    for p in players:
        await p.recv()

    # end turn
    packet = json.dumps({"type":"end-turn"})
    await players[1].send(packet)
    resp = json.loads(await players[1].recv())
    assert resp["status"]["game_state"] == "WAITING_CLUE"
    assert resp["status"]["current_turn"] == "orange"

    for p in players:
        await p.close()
    await srv.stop_server()

@pytest.mark.asyncio
async def test_waiting_approval_to_waiting_players(start_game):
    # reset to WAITING_PLAYERS after critical player leaves
    srv, _, players = start_game
    packet = json.dumps({"type":"new-clue","clue":"FRUIT","count":1})
    await players[0].send(packet)
    resp = json.loads(await players[0].recv())
    for p in players:
        await p.recv()

    assert resp["status"]["game_state"] == "WAITING_APPROVAL"

    await players[0].close()
    del players[0]
    resp = json.loads(await players[0].recv())
    assert resp["status"]["game_state"] == "WAITING_PLAYERS"

    for p in players:
        await p.close()
    await srv.stop_server()

@pytest.mark.asyncio
async def test_waiting_guess_to_waiting_players(start_game):
    # reset to WAITING_PLAYERS after critical player leaves
    srv, _, players = start_game
    packet = json.dumps({"type":"new-clue","clue":"FRUIT","count":1})
    await players[0].send(packet)
    await players[0].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"clue-approved"})
    await players[2].send(packet)
    resp = json.loads(await players[2].recv())
    for p in players:
        await p.recv()
    assert resp["status"]["game_state"] == "WAITING_GUESS"

    await players[0].close()
    del players[0]
    resp = json.loads(await players[0].recv())
    assert resp["status"]["game_state"] == "WAITING_PLAYERS"

    for p in players:
        await p.close()
    await srv.stop_server()

# @pytest.mark.asyncio
# async def test_timeout_on_waiting_guess(start_game):
#     # reset to WAITING_PLAYERS after critical player leaves
#     srv, _, players = start_game
#     packet = json.dumps({"type":"new-clue","clue":"FRUIT","count":1})
#     await players[0].send(packet)
#     await players[0].recv()
#     for p in players:
#         await p.recv()
#     packet = json.dumps({"type":"clue-approved"})
#     await players[2].send(packet)
#     resp = json.loads(await players[2].recv())
#     for p in players:
#         await p.recv()
#     assert resp["status"]["game_state"] == "WAITING_GUESS"

#     await asyncio.sleep(0.06)

#     resp = json.loads(await players[0].recv())
#     assert resp["status"]["game_state"] == "WAITING_CLUE"

#     for p in players:
#         await p.close()
#     await srv.stop_server()

@pytest.mark.asyncio
async def test_play_full_game_and_restart(start_game):
    # reset to WAITING_PLAYERS after critical player leaves
    srv, _, players = start_game
    packet = json.dumps({"type":"new-clue","clue":"EVERYTHING","count":8})
    await players[0].send(packet)
    await players[0].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"clue-approved"})
    await players[2].send(packet)
    resp = json.loads(await players[2].recv())
    for p in players:
        await p.recv()

    # send 8 guesses back to back
    packet = json.dumps({"type":"new-guess","guess":"APPLE"})
    await players[1].send(packet)
    await players[1].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"new-guess","guess":"BOMB"})
    await players[1].send(packet)
    await players[1].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"new-guess","guess":"CROWN"})
    await players[1].send(packet)
    await players[1].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"new-guess","guess":"DAD"})
    await players[1].send(packet)
    await players[1].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"new-guess","guess":"EASTER"})
    await players[1].send(packet)
    await players[1].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"new-guess","guess":"FLAG"})
    await players[1].send(packet)
    await players[1].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"new-guess","guess":"GIANT"})
    await players[1].send(packet)
    await players[1].recv()
    for p in players:
        await p.recv()
    packet = json.dumps({"type":"new-guess","guess":"HOME"})
    await players[1].send(packet)
    resp = json.loads(await players[1].recv())
    for p in players:
        await p.recv()
    
    assert resp["status"]["game_state"] == "GAME_OVER"
    assert resp["status"]["winner"] == "blue"

    packet = json.dumps({"type":"replay-request"})
    for p in players[:3]:
        await p.send(packet)
        await p.recv()
        for pl in players:
            await pl.recv()

    await players[3].send(packet)
    resp = json.loads(await players[3].recv())
    assert resp["status"]["game_state"] == "WAITING_START"

    for p in players:
        await p.close()
    await srv.stop_server()

# @pytest.fixture(scope="module")
# def event_loop():
    # loop = asyncio.get_event_loop()
#     test_server = WServer()
#     loop.create_task(test_server.start_server(wss=False, port=9001))
    # yield loop
#     # loop.close()

# @pytest.mark.asyncio
# async def test_client_connect():
#     async with websockets.connect(uri) as websocket:
#         # greeting = await websocket.recv()
#         # resp
#         pass

# @pytest.mark.asyncio
# async def test_multiple_clients(quantity=128):
#     clients = list()
#     for _ in range(quantity):
#         new_client = await websockets.connect(uri)
#         clients.append(new_client)
#     for client in clients:
#         client.close()

# sector_quantity = 1

# def cluster_message(payload):
#     print()
#     print(json.dumps(payload, indent=3))

# @pytest.fixture
# def create_cluster(sectors=sector_quantity):
#     cluster = OrbitalsCluster(sectorCount=sectors, callback=cluster_message)
#     yield cluster

# def test_sector_count(create_cluster):
#     cluster = create_cluster
#     assert len(cluster.getClusterStatus()) == sector_quantity

# def test_cluster_new_player(create_cluster):
#     cluster = create_cluster
#     response = cluster.newPlayer(name="Anna")
#     assert response

#     response = cluster.newPlayer(name="")
#     assert response == "please enter a valid name"

#     response = cluster.newPlayer(name="Anna")
#     assert response == "please enter a different name"

# def test_cluster_player_leaves(create_cluster):
#     cluster = create_cluster
#     cluster.newPlayer("Anna")

#     cluster.playerLeaves("Anna")

# def test_cluster_sector_request(create_cluster):
#     cluster = create_cluster
#     cluster.newPlayer(name="Anna")
#     response = cluster.playerMessage("Anna", {"type":"join-sector", "sector": "ALPHA"})
#     print(response)
#     assert response["msg"] == "joined-sector"

# @pytest.mark.asyncio
# async def test_client_connect():
#    async with websockets.connect(uri) as websocket:
#         player_one_name = 'P1'
#         greeting = await websocket.recv()
#         resp = json.loads(greeting)
        
#         assert(resp == sr.CONN_RESPONSE_OK)

#         name_req = {'type': 'name-request', 'name':player_one_name}
#         await websocket.send(json.dumps(name_req))
#         response = await websocket.recv()
#         resp = json.loads(response)
#         name_accepted = sr.NAME_RESPONSE_OK
#         name_accepted['name'] = player_one_name

#         assert(resp == name_accepted)



# @pytest.mark.asyncio
# async def test_connect_multiple_clients():
#     clients = await connect_multiple_clients(32)
#     print("First response: ", await clients[0].recv())
#     name_req = {'type': 'name-request', 'name':'first'}

#     await clients[0].send(json.dumps(name_req))
#     response = await clients[0].recv()
    
#     name_ok = sr.NAME_RESPONSE_OK
#     name_ok['name'] = 'first'
#     assert(name_ok == json.loads(response))

#     print("Last client response: ", await clients[-1].recv())
#     name_req = {'type': 'name-request', 'name':'last'}
#     await clients[-1].send(json.dumps(name_req))
#     response = await clients[-1].recv()

#     name_ok = sr.NAME_RESPONSE_OK
#     name_ok['name'] = 'last'
#     assert(name_ok == json.loads(response))

#     for client in clients:
#         await client.close()
    
# @pytest.mark.asyncio
# async def test_join_sector_request():
#     # connection
#     ws = await websockets.connect(uri)
#     await ws.recv()

#     # name request
#     name_req = {'type': 'name-request', 'name':'P1'}
#     await ws.send(json.dumps(name_req))
#     response = await ws.recv()

#     # join sector request
#     sector_req = {'type': 'join-sector', 'sector':'ALPHA'}
#     await ws.send(json.dumps(sector_req))
#     response = await ws.recv()

#     assert(sr.SECTOR_RESPONSE_OK == json.loads(response))

#     await ws.close()

# @pytest.mark.asyncio
# async def test_leave_sector_request():
#     # connection
#     ws = await websockets.connect(uri)
#     await ws.recv()

#     # name request
#     name_req = {'type': 'name-request', 'name':'P1'}
#     await ws.send(json.dumps(name_req))
#     response = await ws.recv()

#     # join sector request
#     sector_req = {'type': 'join-sector', 'sector':'ALPHA'}
#     await ws.send(json.dumps(sector_req))
#     response = await ws.recv() # joined ok
#     print("> ", response)
#     response = await ws.recv() # state
#     print("> ", response) 
#     response = await ws.recv() # players
#     print("> ", response) 
#     response = await ws.recv() # joined sector broadcast
#     print("> ", response) 
    
#     # leave sector request
#     leave_req = {'type': 'leave-sector'}
#     await ws.send(json.dumps(leave_req))
#     response = await ws.recv()

#     print(">", response)
#     assert(sr.LEAVE_SECTOR_RESPONSE_OK == json.loads(response))

#     await ws.close()

    