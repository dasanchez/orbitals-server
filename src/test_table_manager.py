import json
import pytest
from pprint import pprint

from orbitals_table_manager import OrbitalsTableManager

class Player():
    def __init__(self, name: ""=str):
        self._msg = ""
        self._name = name
        self._messages = list()
    def new_data(self, packet):
        self._messages.append(json.loads(packet))
        # self._msg = json.loads(packet)
    def clear_messages(self):
        self._messages.clear()
    def latestEntry(self):
        return self._messages.pop(0)
    def name(self):
        return self._name

def getResponse(fn, message_dict):
    data = json.dumps(message_dict)
    return json.loads(fn(data))

@pytest.fixture
def create_table_manager_with_players():
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
        tm.playerMessage(player, json.dumps({"type":"name-request", "name":player.name()}))
        assert player.latestEntry()["msg"] == "name accepted"
    
    tm.playerMessage(player_Ann, json.dumps({"type":"team-request","team":"blue"}))
    tm.playerMessage(player_Bob, json.dumps({"type":"team-request","team":"blue"}))
    tm.playerMessage(player_Elsa, json.dumps({"type":"team-request","team":"orange"}))
    tm.playerMessage(player_Finn, json.dumps({"type":"team-request","team":"orange"}))

    for player in players:
        player.clear_messages()

    yield tm, players

@pytest.fixture
def create_table_manager_with_players_pre_start():
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
        tm.playerMessage(player, json.dumps({"type":"name-request", "name":player.name()}))
        assert player.latestEntry()["msg"] == "name accepted"

    packet = {"type":"team-request", "team":"blue"}
    tm.playerMessage(player_Ann, json.dumps(packet))
    tm.playerMessage(player_Bob, json.dumps(packet))
    tm.playerMessage(player_Carl, json.dumps(packet))
    tm.playerMessage(player_Dina, json.dumps(packet))
    packet["team"] = "orange"
    tm.playerMessage(player_Elsa, json.dumps(packet))
    tm.playerMessage(player_Finn, json.dumps(packet))
    tm.playerMessage(player_Gina, json.dumps(packet))
    tm.playerMessage(player_Hank, json.dumps(packet))

    for player in players:
        player.clear_messages()
    packet["type"] = "role-request"
    packet["role"] = "hub"
    tm.playerMessage(player_Ann, json.dumps(packet))
    assert player_Ann.latestEntry()["msg"] == "role accepted"
    for player in players:
        player.clear_messages()
    tm.playerMessage(player_Elsa, json.dumps(packet))
    assert player_Elsa.latestEntry()["msg"] == "role accepted"
    for player in players:
        player.clear_messages()

    yield tm, players

@pytest.fixture
def start_game():
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
        tm.playerMessage(player, json.dumps({"type":"name-request", "name":player.name()}))
        assert player.latestEntry()["msg"] == "name accepted"

    packet = {"type":"team-request", "team":"blue"}
    tm.playerMessage(player_Ann, json.dumps(packet))
    tm.playerMessage(player_Bob, json.dumps(packet))
    tm.playerMessage(player_Carl, json.dumps(packet))
    tm.playerMessage(player_Dina, json.dumps(packet))
    packet["team"] = "orange"
    tm.playerMessage(player_Elsa, json.dumps(packet))
    tm.playerMessage(player_Finn, json.dumps(packet))
    tm.playerMessage(player_Gina, json.dumps(packet))
    tm.playerMessage(player_Hank, json.dumps(packet))

    for player in players:
        player.clear_messages()
    packet["type"] = "role-request"
    packet["role"] = "hub"
    tm.playerMessage(player_Ann, json.dumps(packet))
    tm.playerMessage(player_Elsa, json.dumps(packet))

    packet = {"type":"start-request"}
    tm.playerMessage(players[0],json.dumps(packet))
    tm.playerMessage(players[4],json.dumps(packet))
    
    for player in players:
        player.clear_messages()

    yield tm, players


def test_new_connection():
    tm = OrbitalsTableManager()
    player = Player("Player")
    packet = {"type": "connection"}
    tm.playerMessage(player, json.dumps(packet))
    assert player.latestEntry()["msg"] == "provide name"

def test_name_request():
    tm = OrbitalsTableManager(player_limit=4)
    player = Player("Player")
    packet = {"type": "name-request", "name": "Player"}
    tm.playerMessage(player, json.dumps(packet))
    assert player.latestEntry()["msg"] == "name accepted"
    player2 = Player("Player 2")
    packet = {"type": "name-request", "name": "Player"}
    tm.playerMessage(player2, json.dumps(packet))
    assert player2.latestEntry()["msg"] == "player name exists"

def test_limit_reached():
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
        tm.playerMessage(player, json.dumps({"type":"name-request","name":player.name()}))

    assert player5.latestEntry()["msg"] == "player limit has been reached"

def test_team_request():
    tm = OrbitalsTableManager(player_limit=4)
    player = Player("Player")
    packet = {"type": "name-request", "name":player.name()}
    tm.playerMessage(player, json.dumps(packet))
    player.clear_messages()
    packet = {"type": "team-request", "team":"blue"}
    tm.playerMessage(player, json.dumps(packet))
    assert player.latestEntry()["msg"] == "team accepted"

def test_role_request(create_table_manager_with_players):
    tm, players = create_table_manager_with_players
    packet = {"type": "role-request", "role": "hub"}
    tm.playerMessage(players[0], json.dumps(packet))
    assert players[0].latestEntry()["msg"] == "role accepted"
    players[1].clear_messages()
    tm.playerMessage(players[1],json.dumps(packet))
    assert players[1].latestEntry()["msg"] == "hub role not available"

def test_start_request(create_table_manager_with_players_pre_start):
    tm, players = create_table_manager_with_players_pre_start

    packet = {"type": "status-request"}
    tm.playerMessage(players[0], json.dumps(packet))
    assert players[0].latestEntry()["status"]["game_state"] == "WAITING_START"
    packet = {"type":"start-request"}
    tm.playerMessage(players[0],json.dumps(packet))
    tm.playerMessage(players[4],json.dumps(packet))
    packet = {"type": "status-request"}
    tm.playerMessage(players[0], json.dumps(packet))
    assert players[0].latestEntry()["status"]["game_state"] == "WAITING_CLUE"
    tm._table.stopTimer()

def test_submit_clue(start_game):
    tm, players = start_game
    packet = {"type":"new-clue","clue":"FRUIT","count":1}
    tm.playerMessage(players[0],json.dumps(packet))
    packet = {"type":"status-request"}
    tm.playerMessage(players[0],json.dumps(packet))
    assert players[0].latestEntry()["status"]["game_state"] == "WAITING_APPROVAL"
    tm._table.stopTimer()

def test_clue_approval(start_game):
    tm, players = start_game
    packet = {"type":"new-clue","clue":"FRUIT","count":1}
    tm.playerMessage(players[0],json.dumps(packet))
    for player in players:
        player.clear_messages()
    packet = {"type":"clue-approved"}
    tm.playerMessage(players[4],json.dumps(packet))
    packet = {"type":"status-request"}
    tm.playerMessage(players[0],json.dumps(packet))
    assert players[0].latestEntry()["status"]["game_state"] == "WAITING_GUESS"
    tm._table.stopTimer()

def test_clue_rejection(start_game):
    tm, players = start_game
    packet = {"type":"new-clue","clue":"FRUIT","count":1}
    tm.playerMessage(players[0],json.dumps(packet))
    packet = {"type":"clue-rejected"}
    tm.playerMessage(players[4],json.dumps(packet))
    for player in players:
        player.clear_messages()
    packet = {"type":"status-request"}
    tm.playerMessage(players[0],json.dumps(packet))
    response = players[0].latestEntry()
    assert response["status"]["game_state"] == "WAITING_CLUE"
    assert response["status"]["current_turn"] == "blue"
    tm._table.stopTimer()

def test_submit_guess(start_game):
    tm, players = start_game
    packet = {"type":"new-clue","clue":"FRUIT","count":1}
    tm.playerMessage(players[0],json.dumps(packet))
    packet = {"type":"clue-approved"}
    tm.playerMessage(players[4],json.dumps(packet))
    for player in players:
        player.clear_messages()
    packet = {"type":"new-guess","guess":"APPLE"}
    tm.playerMessage(players[1],json.dumps(packet))
    response = players[1].latestEntry()
    assert response["status"]["tiles"]["APPLE"] == "blue"
    tm._table.stopTimer()

def test_player_leaves_table(start_game):
    tm, players = start_game
    tm.playerLeft(players[0])
    response = players[1].latestEntry()
    assert response["status"]["game_state"] == "WAITING_PLAYERS"
    
def test_broadcasts():
    tm = OrbitalsTableManager()
    player_1 = Player("Ann")
    player_2 = Player("Bob")
    packet = {"type":"connection"}
    data = json.dumps(packet)
    tm.playerMessage(player_1, data)
    tm.playerMessage(player_2, data)
    assert player_1.latestEntry()["msg"] == "provide name"
    packet = {"type":"name-request", "name":"Ann"}
    tm.playerMessage(player_1, json.dumps(packet))
    assert player_1.latestEntry()["msg"] == "name accepted"
    assert player_1.latestEntry()["msg"] == "Ann has joined the game"
    packet = {"type":"name-request", "name":"Bob"}
    tm.playerMessage(player_2, json.dumps(packet))
    assert player_1.latestEntry()["msg"] == "Bob has joined the game"
    packet = {"type":"team-request", "team":"blue"}
    tm.playerMessage(player_1,json.dumps(packet))
    assert player_1.latestEntry()["msg"] == "team accepted"
    assert player_1.latestEntry()["msg"] == "Ann has joined the blue team"
    packet = {"type":"role-request", "role":"hub"}
    tm.playerMessage(player_1,json.dumps(packet))
    assert player_1.latestEntry()["msg"] == "role accepted"
    assert player_1.latestEntry()["msg"] == "Ann is now a hub"
    
def test_broadcast_state_change(create_table_manager_with_players_pre_start):
    tm, players = create_table_manager_with_players_pre_start
