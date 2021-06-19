import json
import pytest
from pprint import pprint
import asyncio

from orbitals_table_manager import OrbitalsTableManager

class Player():
    def __init__(self, name: ""=str):
        self._msg = ""
        self._name = name
        self._messages = list()
    async def send(self, packet):
        self._messages.append(json.loads(packet))
        if len(self._messages) > 3:
            self._messages.pop(0)
        # self._msg = json.loads(packet)
    def clear_messages(self):
        self._messages.clear()
    def latestEntry(self):
        return self._messages.pop()
    def name(self):
        return self._name

def getResponse(fn, message_dict):
    data = json.dumps(message_dict)
    return json.loads(fn(data))

@pytest.fixture
async def tm_with_players():
    tm = OrbitalsTableManager(player_limit=4, time_limit=1)
    players = list()
    player_Ann = Player("Ann")
    players.append(player_Ann)
    player_Bob = Player("Bob")
    players.append(player_Bob)
    player_Elsa = Player("Elsa")
    players.append(player_Elsa)
    player_Finn = Player("Finn")
    players.append(player_Finn)

    for player in players:
        await tm.playerMessage(player, json.dumps({"type":"name-request", "name":player.name()}))
        resp = player.latestEntry()
        resp = player.latestEntry()
        assert resp["msg"] == "name accepted"
    
    await tm.playerMessage(player_Ann, json.dumps({"type":"team-request","team":"blue"}))
    await tm.playerMessage(player_Bob, json.dumps({"type":"team-request","team":"blue"}))
    await tm.playerMessage(player_Elsa, json.dumps({"type":"team-request","team":"orange"}))
    await tm.playerMessage(player_Finn, json.dumps({"type":"team-request","team":"orange"}))

    for player in players:
        player.clear_messages()

    yield tm, players

@pytest.fixture
async def tm_with_players_pre_start():
    tm = OrbitalsTableManager(player_limit=8, time_limit=1)
    players = list()
    player_Ann = Player("Ann")
    players.append(player_Ann)
    player_Bob = Player("Bob")
    players.append(player_Bob)
    player_Carl = Player("Carl")
    players.append(player_Carl)
    player_Dina = Player("Dina")
    players.append(player_Dina)
    player_Elsa = Player("Elsa")
    players.append(player_Elsa)
    player_Finn = Player("Finn")
    players.append(player_Finn)
    player_Gina = Player("Gina")
    players.append(player_Gina)
    player_Hank = Player("Hank")
    players.append(player_Hank)

    for player in players:
        await tm.playerMessage(player, json.dumps({"type":"name-request", "name":player.name()}))
        player.latestEntry()
        assert player.latestEntry()["msg"] == "name accepted"

    packet = {"type":"team-request", "team":"blue"}
    await tm.playerMessage(player_Ann, json.dumps(packet))
    await tm.playerMessage(player_Bob, json.dumps(packet))
    await tm.playerMessage(player_Carl, json.dumps(packet))
    await tm.playerMessage(player_Dina, json.dumps(packet))
    packet["team"] = "orange"
    await tm.playerMessage(player_Elsa, json.dumps(packet))
    await tm.playerMessage(player_Finn, json.dumps(packet))
    await tm.playerMessage(player_Gina, json.dumps(packet))
    await tm.playerMessage(player_Hank, json.dumps(packet))

    for player in players:
        player.clear_messages()
    packet["type"] = "role-request"
    packet["role"] = "hub"
    await tm.playerMessage(player_Ann, json.dumps(packet))
    player_Ann.latestEntry()
    assert player_Ann.latestEntry()["msg"] == "role accepted"
    for player in players:
        player.clear_messages()
    await tm.playerMessage(player_Elsa, json.dumps(packet))
    player_Elsa.latestEntry()
    assert player_Elsa.latestEntry()["msg"] == "role accepted"
    for player in players:
        player.clear_messages()

    yield tm, players

@pytest.fixture
async def start_game():
    tm = OrbitalsTableManager(player_limit=8, time_limit=3)
    players = list()
    player_Ann = Player("Ann")
    players.append(player_Ann)
    player_Bob = Player("Bob")
    players.append(player_Bob)
    player_Carl = Player("Carl")
    players.append(player_Carl)
    player_Dina = Player("Dina")
    players.append(player_Dina)
    player_Elsa = Player("Elsa")
    players.append(player_Elsa)
    player_Finn = Player("Finn")
    players.append(player_Finn)
    player_Gina = Player("Gina")
    players.append(player_Gina)
    player_Hank = Player("Hank")
    players.append(player_Hank)

    for player in players:
        await tm.playerMessage(player, json.dumps({"type":"name-request", "name":player.name()}))
        player.latestEntry()
        assert player.latestEntry()["msg"] == "name accepted"

    packet = {"type":"team-request", "team":"blue"}
    await tm.playerMessage(player_Ann, json.dumps(packet))
    await tm.playerMessage(player_Bob, json.dumps(packet))
    await tm.playerMessage(player_Carl, json.dumps(packet))
    await tm.playerMessage(player_Dina, json.dumps(packet))
    packet["team"] = "orange"
    await tm.playerMessage(player_Elsa, json.dumps(packet))
    await tm.playerMessage(player_Finn, json.dumps(packet))
    await tm.playerMessage(player_Gina, json.dumps(packet))
    await tm.playerMessage(player_Hank, json.dumps(packet))

    for player in players:
        player.clear_messages()
    packet["type"] = "role-request"
    packet["role"] = "hub"
    await tm.playerMessage(player_Ann, json.dumps(packet))
    await tm.playerMessage(player_Elsa, json.dumps(packet))

    packet = {"type":"start-request"}
    await tm.playerMessage(players[0],json.dumps(packet))
    await tm.playerMessage(players[4],json.dumps(packet))
    
    for player in players:
        player.clear_messages()

    yield tm, players

@pytest.mark.asyncio
async def test_new_connection():
    tm = OrbitalsTableManager()
    player = Player("Player")
    packet = {"type": "connection"}
    await tm.playerMessage(player, json.dumps(packet))
    assert player.latestEntry()["msg"] == "provide name"

@pytest.mark.asyncio
async def test_name_request():
    tm = OrbitalsTableManager(player_limit=4)
    player = Player("Player")
    packet = {"type": "name-request", "name": "Player"}
    await tm.playerMessage(player, json.dumps(packet))
    player.latestEntry()
    assert player.latestEntry()["msg"] == "name accepted"
    player2 = Player("Player 2")
    packet = {"type": "name-request", "name": "Player"}
    await tm.playerMessage(player2, json.dumps(packet))
    assert player2.latestEntry()["msg"] == "player name exists"

@pytest.mark.asyncio
async def test_limit_reached():
    tm = OrbitalsTableManager(player_limit=4)
    players = list()
    player1 = Player("Player 1")
    players.append(player1)
    player2 = Player("Player 2")
    players.append(player2)
    player3 = Player("Player 3")
    players.append(player3)
    player4 = Player("Player 4")
    players.append(player4)
    player5 = Player("Player 5")
    players.append(player5)
    for player in players:
        await tm.playerMessage(player, json.dumps({"type":"name-request","name":player.name()}))

    assert player5.latestEntry()["msg"] == "player limit has been reached"

@pytest.mark.asyncio
async def test_team_request():
    tm = OrbitalsTableManager(player_limit=4)
    player = Player("Player")
    packet = {"type": "name-request", "name":player.name()}
    await tm.playerMessage(player, json.dumps(packet))
    player.clear_messages()
    packet = {"type": "team-request", "team":"blue"}
    await tm.playerMessage(player, json.dumps(packet))
    player.latestEntry()
    assert player.latestEntry()["msg"] == "team accepted"

@pytest.mark.asyncio
async def test_role_request(tm_with_players):
    tm, players = tm_with_players
    packet = {"type": "role-request", "role": "hub"}
    await tm.playerMessage(players[0], json.dumps(packet))
    players[0].latestEntry()
    assert players[0].latestEntry()["msg"] == "role accepted"
    players[1].clear_messages()
    await tm.playerMessage(players[1],json.dumps(packet))
    assert players[1].latestEntry()["msg"] == "hub role not available"

@pytest.mark.asyncio
async def test_start_request(tm_with_players_pre_start):
    tm, players = tm_with_players_pre_start

    packet = {"type": "status-request"}
    await tm.playerMessage(players[0], json.dumps(packet))
    assert players[0].latestEntry()["status"]["game_state"] == "WAITING_START"
    packet = {"type":"start-request"}
    await tm.playerMessage(players[0],json.dumps(packet))
    await tm.playerMessage(players[4],json.dumps(packet))
    packet = {"type": "status-request"}
    await tm.playerMessage(players[0], json.dumps(packet))
    assert players[0].latestEntry()["status"]["game_state"] == "WAITING_CLUE"
    tm._table.stopTimer()

@pytest.mark.asyncio
async def test_submit_clue(start_game):
    tm, players = start_game
    packet = {"type":"new-clue","clue":"FRUIT","count":1}
    await tm.playerMessage(players[0],json.dumps(packet))
    packet = {"type":"status-request"}
    await tm.playerMessage(players[0],json.dumps(packet))
    assert players[0].latestEntry()["status"]["game_state"] == "WAITING_APPROVAL"
    tm._table.stopTimer()

@pytest.mark.asyncio
async def test_clue_approval(start_game):
    tm, players = start_game
    packet = {"type":"new-clue","clue":"FRUIT","count":1}
    await tm.playerMessage(players[0],json.dumps(packet))
    for player in players:
        player.clear_messages()
    packet = {"type":"clue-approved"}
    await tm.playerMessage(players[4],json.dumps(packet))
    packet = {"type":"status-request"}
    await tm.playerMessage(players[0],json.dumps(packet))
    assert players[0].latestEntry()["status"]["game_state"] == "WAITING_GUESS"
    tm._table.stopTimer()

@pytest.mark.asyncio
async def test_clue_rejection(start_game):
    tm, players = start_game
    packet = {"type":"new-clue","clue":"FRUIT","count":1}
    await tm.playerMessage(players[0],json.dumps(packet))
    packet = {"type":"clue-rejected"}
    await tm.playerMessage(players[4],json.dumps(packet))
    for player in players:
        player.clear_messages()
    packet = {"type":"status-request"}
    await tm.playerMessage(players[0],json.dumps(packet))
    response = players[0].latestEntry()
    assert response["status"]["game_state"] == "WAITING_CLUE"
    assert response["status"]["current_turn"] == "blue"
    tm._table.stopTimer()

@pytest.mark.asyncio
async def test_submit_guess(start_game):
    tm, players = start_game
    packet = {"type":"new-clue","clue":"FRUIT","count":1}
    await tm.playerMessage(players[0],json.dumps(packet))
    packet = {"type":"clue-approved"}
    await tm.playerMessage(players[4],json.dumps(packet))
    for player in players:
        player.clear_messages()
    packet = {"type":"new-guess","guess":"APPLE"}
    await tm.playerMessage(players[1],json.dumps(packet))
    response = players[1].latestEntry()
    assert response["status"]["tiles"]["APPLE"] == "blue"
    tm._table.stopTimer()

@pytest.mark.asyncio
async def test_replay_requests(start_game):
    tm, players = start_game
    # 1. play to win
    packet = {"type":"new-clue","clue":"EVERYTHING","count":8}
    await tm.playerMessage(players[0],json.dumps(packet))
    packet = {"type":"clue-approved"}
    await tm.playerMessage(players[4],json.dumps(packet))
    for player in players:
        player.clear_messages()
    blue_tiles = ["APPLE","BOMB","CROWN","DAD","EASTER","FLAG","GIANT","HOME"]
    for tile in blue_tiles:
        packet = {"type":"new-guess","guess":tile}
        await tm.playerMessage(players[1],json.dumps(packet))
    response = players[1].latestEntry()
    assert response["status"]["game_state"] == "GAME_OVER"
    
    # submit replay requests
    packet = json.dumps({"type":"replay-request"})
    for p in players:
        await tm.playerMessage(p,packet)
    resp = players[0].latestEntry()
    assert resp["status"]["game_state"] == "WAITING_START"

@pytest.mark.asyncio
async def test_player_leaves_table(start_game):
    tm, players = start_game
    await tm.playerLeft(players[0])
    response = players[1].latestEntry()
    assert response["status"]["game_state"] == "WAITING_PLAYERS"
    
@pytest.mark.asyncio
async def test_broadcasts():
    tm = OrbitalsTableManager()
    player_1 = Player("Ann")
    player_2 = Player("Bob")
    packet = {"type":"connection"}
    data = json.dumps(packet)
    await tm.playerMessage(player_1, data)
    await tm.playerMessage(player_2, data)
    assert player_1.latestEntry()["msg"] == "provide name"
    packet = {"type":"name-request", "name":"Ann"}
    await tm.playerMessage(player_1, json.dumps(packet))
    assert player_1.latestEntry()["msg"] == "Ann has joined the game"
    assert player_1.latestEntry()["msg"] == "name accepted"
    packet = {"type":"name-request", "name":"Bob"}
    await tm.playerMessage(player_2, json.dumps(packet))
    assert player_1.latestEntry()["msg"] == "Bob has joined the game"
    packet = {"type":"team-request", "team":"blue"}
    await tm.playerMessage(player_1,json.dumps(packet))
    assert player_1.latestEntry()["msg"] == "Ann has joined the blue team"
    assert player_1.latestEntry()["msg"] == "team accepted"
    packet = {"type":"role-request", "role":"hub"}
    await tm.playerMessage(player_1,json.dumps(packet))
    assert player_1.latestEntry()["msg"] == "Ann is now a hub"
    assert player_1.latestEntry()["msg"] == "role accepted"

@pytest.mark.asyncio
async def test_tick(start_game):
    tm, players = start_game

    await asyncio.sleep(1)    
    assert len(players[0]._messages) > 0
    resp = players[0].latestEntry()
    assert resp["type"] == "tick"
    assert resp["time_left"] == 2
    await asyncio.sleep(1)    
    assert len(players[0]._messages) > 0
    resp = players[0].latestEntry()
    assert resp["type"] == "tick"
    assert resp["time_left"] == 1

    tm._table.stopTimer()

@pytest.mark.asyncio
async def test_broadcast_states():
    p_blue_hub = Player("Blue Hub")
    p_blue = Player("Blue")
    p_orange_hub = Player("Orange Hub")
    p_orange = Player("Orange")
   
    tm = OrbitalsTableManager(time_limit=0.05)
    await tm.playerMessage(p_blue_hub, json.dumps({"type":"name-request","name":p_blue_hub.name()}))
    await tm.playerMessage(p_blue, json.dumps({"type":"name-request","name":p_blue.name()}))
    await tm.playerMessage(p_orange_hub, json.dumps({"type":"name-request","name":p_orange_hub.name()}))
    await tm.playerMessage(p_orange, json.dumps({"type":"name-request","name":p_orange.name()}))
    await tm.playerMessage(p_blue_hub, json.dumps({"type":"team-request","team":"blue"}))
    await tm.playerMessage(p_blue, json.dumps({"type":"team-request","team":"blue"}))
    await tm.playerMessage(p_orange_hub, json.dumps({"type":"team-request","team":"orange"}))
    await tm.playerMessage(p_orange, json.dumps({"type":"team-request","team":"orange"}))
    await tm.playerMessage(p_blue_hub,json.dumps({"type":"role-request","role":"hub"}))
    
    # WAITING_PLAYERS -> WAITING_START
    assert p_blue.latestEntry()["status"]["game_state"] == "WAITING_PLAYERS"
    await tm.playerMessage(p_orange_hub,json.dumps({"type":"role-request","role":"hub"}))
    assert p_blue.latestEntry()["status"]["game_state"] == "WAITING_START"
    await tm.playerMessage(p_blue_hub,json.dumps({"type":"start-request"}))
    await tm.playerMessage(p_orange_hub,json.dumps({"type":"start-request"}))
    # WAITING_START -> WAITING_CLUE
    assert p_blue.latestEntry()["status"]["game_state"] == "WAITING_CLUE"
    # WAITING_CLUE -> WAITING_APPROVAL
    await tm.playerMessage(p_blue_hub,json.dumps({"type":"new-clue","clue":"FRUIT","count":1}))
    resp = p_blue.latestEntry()
    # pprint(resp["status"])
    assert resp["status"]["game_state"] == "WAITING_APPROVAL"
    assert "new-clue" not in resp["status"].keys()
    res_hub = p_orange_hub.latestEntry()
    assert res_hub["status"]["clue"] == "FRUIT"
    assert res_hub["status"]["guesses_left"] == 1

    # WAITING_APPROVAL -> WAITING_GUESS
    await tm.playerMessage(p_orange_hub,json.dumps({"type":"clue-approved"}))
    resp = p_blue.latestEntry()
    assert resp["status"]["game_state"] == "WAITING_GUESS"
    assert resp["status"]["clue"] == "FRUIT"
    assert resp["status"]["guesses_left"] == 1
    # WAITING_GUESS -> WAITING_CLUE
    await tm.playerMessage(p_blue,json.dumps({"type":"new-guess","guess":"APPLE"}))
    assert p_orange.latestEntry()["status"]["game_state"] == "WAITING_CLUE"
    # WAITING_CLUE -> WAITING_CLUE for opposite team due to timeout
    await asyncio.sleep(0.06)
    # pprint(p_orange._messages)
    broadcast = p_orange.latestEntry()
    assert broadcast["msg"] == "timeout"
    assert broadcast["status"]["current_turn"] == "blue"
    # WAITING_CLUE -> WAITING APPROVAL
    await tm.playerMessage(p_blue_hub,json.dumps({"type":"new-clue","clue":"EVERYTHING","count":7}))
    assert p_blue.latestEntry()["status"]["game_state"] == "WAITING_APPROVAL"
    # WAITING APPROVAL -> WAITING GUESS
    await tm.playerMessage(p_orange_hub,json.dumps({"type":"clue-approved"}))
    status = p_blue.latestEntry()["status"]
    assert status["game_state"] == "WAITING_GUESS"
    assert status["guesses_left"] == 7
    # WAITING GUESS -> GAME_OVER
    await tm.playerMessage(p_blue,json.dumps({"type":"new-guess","guess":"BOMB"}))
    await tm.playerMessage(p_blue,json.dumps({"type":"new-guess","guess":"CROWN"}))
    await tm.playerMessage(p_blue,json.dumps({"type":"new-guess","guess":"DAD"}))
    await tm.playerMessage(p_blue,json.dumps({"type":"new-guess","guess":"EASTER"}))
    await tm.playerMessage(p_blue,json.dumps({"type":"new-guess","guess":"FLAG"}))
    await tm.playerMessage(p_blue,json.dumps({"type":"new-guess","guess":"GIANT"}))
    await tm.playerMessage(p_blue,json.dumps({"type":"new-guess","guess":"HOME"}))
    status = p_blue.latestEntry()["status"]
    assert status["game_state"] == "GAME_OVER"
    assert status["winner"] == "blue"
    # GAME_OVER -> WAITING_START
    await tm.playerMessage(p_blue_hub, json.dumps({"type":"replay-request"}))
    await tm.playerMessage(p_blue, json.dumps({"type":"replay-request"}))
    await tm.playerMessage(p_orange, json.dumps({"type":"replay-request"}))
    await tm.playerMessage(p_orange_hub, json.dumps({"type":"replay-request"}))        
    status = p_blue.latestEntry()["status"]
    assert status["game_state"] == "WAITING_START"
    
    tm._table.stopTimer()
    