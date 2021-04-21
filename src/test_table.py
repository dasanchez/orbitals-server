import pytest
from collections import Counter
from orbitals_table import OrbitalsTable, GameState

@pytest.fixture
def create_game_and_teams():
    orbitals_board = OrbitalsTable()
    orbitals_board.playerJoins("Ann")
    orbitals_board.playerJoins("Bob")
    orbitals_board.playerJoins("Cary")
    orbitals_board.playerJoins("Dina")
    orbitals_board.playerJoins("Elsa")
    orbitals_board.playerJoins("Finn")
    orbitals_board.playerJoins("Gina")
    orbitals_board.playerJoins("Hank")
    orbitals_board.teamRequest("Ann", "blue")
    orbitals_board.teamRequest("Bob", "blue")
    orbitals_board.teamRequest("Cary", "blue")
    orbitals_board.teamRequest("Dina", "blue")
    orbitals_board.teamRequest("Elsa", "orange")
    orbitals_board.teamRequest("Finn", "orange")
    orbitals_board.teamRequest("Gina", "orange")
    orbitals_board.teamRequest("Hank", "orange")
    orbitals_board.roleRequest("Ann", "hub")
    orbitals_board.roleRequest("Elsa", "hub")
    yield orbitals_board

def test_player_count_limit():
    table = OrbitalsTable(player_limit=10)
    assert table.status()['player_limit'] == 10
    assert table.status()['player_count'] == 0
    table.playerJoins("Isaac")
    assert table.status()['spots_available'] == 9

def test_accept_full_teams(create_game_and_teams):
    board = create_game_and_teams
    assert board.players()["Ann"][0] == "blue"
    assert board.players()["Gina"][0] == "orange"
    assert board.players()["Ann"][0] == "blue"

def test_two_hubs_requested(create_game_and_teams):
    board = create_game_and_teams
    assert board.players()["Ann"][1] == "hub"
    assert board.players()["Elsa"][1] == "hub"

def test_second_hub_requested_same_team(create_game_and_teams):
    board = create_game_and_teams
    board.roleRequest("Finn", "hub")
    assert board.players()["Finn"][1] == "no-hub"

def test_start_requests(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Bob")
    assert board.state()[0] ==  GameState.WAITING_START
    board.startRequest("Elsa")
    assert board.state()[0] ==  GameState.WAITING_CLUE
    
def test_tile_board_created(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    assert board.tiles()['APPLE'] == ''

def test_assign_first_turn(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    # count tiles, turn should belong to colour with higher count
    tile_counter = Counter([tile[0] for tile in board._board._tiles.values()])
    blue_tiles = tile_counter['blue']
    orange_tiles = tile_counter['orange']
    if blue_tiles > orange_tiles:
        assert board.state()[1] == 'blue'

def test_accept_clue(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    board.newClue("Ann", "FRUIT")
    assert board.currentClue() == ("FRUIT",1)
    assert board.state() == (GameState.WAITING_GUESS, 'blue')

def test_single_guess_turn_switch(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    board.newClue("Ann", "FRUIT")
    board.newGuess("Bob", "APPLE")
    assert board.tiles()["APPLE"]
    assert board.state() == (GameState.WAITING_CLUE, 'orange')

def test_accept_clue_with_count(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    board.newClue("Ann", "FRUIT")
    board.newGuess("Bob", "APPLE")
    board.newClue("Elsa", "COUNTRY", 2)
    assert board.currentClue() == ("COUNTRY", 2)

def test_multiple_guesses_turn_switch(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    board.newClue("Ann", "FRUIT")
    board.newGuess("Bob", "APPLE")
    board.newClue("Elsa", "COUNTRY", 2)
    board.newGuess("Finn", "INDIA")
    board.newGuess("Finn", "MEXICO")
    assert board.tiles()["INDIA"][1]
    assert board.tiles()["MEXICO"][1]
    assert board.state() == (GameState.WAITING_CLUE, 'blue')

def test_switch_turn_incorrect_guess(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    board.newClue("Ann", "FRUIT")
    board.newGuess("Bob", "APPLE")
    board.newClue("Elsa", "COUNTRY", 2)
    board.newGuess("Finn", "FLAG")
    assert board.tiles()["FLAG"]
    assert board.state() == (GameState.WAITING_CLUE, 'blue')

def test_play_to_win(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    board.newClue("Ann", "ALLWORDS", 8)
    board.newGuess("Bob", "APPLE")
    board.newGuess("Bob", "BOMB")
    board.newGuess("Bob", "CROWN")
    board.newGuess("Bob", "DAD")
    board.newGuess("Bob", "EASTER")
    board.newGuess("Bob", "FLAG")
    board.newGuess("Bob", "GIANT")
    board.newGuess("Bob", "HOME")
    assert board.state()[0] == GameState.GAME_OVER
    assert board.winner() == 'blue'
    
def test_replay_requests(create_game_and_teams):
    board = create_game_and_teams
    board.startRequest("Ann")
    board.startRequest("Elsa")
    board.newClue("Ann", "ALLWORDS", 8)
    board.newGuess("Bob", "APPLE")
    board.newGuess("Bob", "BOMB")
    board.newGuess("Bob", "CROWN")
    board.newGuess("Bob", "DAD")
    board.newGuess("Bob", "EASTER")
    board.newGuess("Bob", "FLAG")
    board.newGuess("Bob", "GIANT")
    board.newGuess("Bob", "HOME")
    board.replayRequest("Ann")
    board.replayRequest("Bob")     
    board.replayRequest("Cary")
    board.replayRequest("Dina")
    board.replayRequest("Elsa")
    board.replayRequest("Finn")
    board.replayRequest("Gina")
    board.replayRequest("Hank")
    assert board.state()[0] == GameState.WAITING_START

def test_player_leaves_table():
    table = OrbitalsTable()
    table.playerJoins("Ann")
    table.playerLeaves("Ann")
    assert table.status()["player_count"] == 0

def test_last_no_hub_leaves_waiting_clue(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.playerLeaves("Bob")
    table.playerLeaves("Cary")
    table.playerLeaves("Dina")
    assert table.status()['game_state'] == GameState.WAITING_PLAYERS

def test_last_no_hub_leaves_waiting_guess(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "ALLWORDS", 8)
    table.playerLeaves("Bob")
    table.playerLeaves("Cary")
    table.playerLeaves("Dina")
    assert table.status()['game_state'] == GameState.WAITING_PLAYERS

def test_start_game_if_conditions_met():
    table = OrbitalsTable()
    table.playerJoins("Ann")
    table.playerJoins("Abe")
    table.playerJoins("Bea")
    table.playerJoins("Bob")
    table.teamRequest("Ann", "blue")
    table.teamRequest("Abe", "blue")
    table.teamRequest("Bea", "orange")
    assert table.startRequest("Ann") == "hub roles are not filled"
    table.roleRequest("Ann", "hub")
    assert table.startRequest("Ann") == "hub roles are not filled"
    table.roleRequest("Bea", "hub")
    assert table.startRequest("Ann") == "no-hub roles are not filled"
    table.teamRequest("Bob", "orange")
    assert table.startRequest("Bob") == "only hub roles can request start"
    assert not table.startRequest("Ann")

def test_sad_player_limit_reached():
    table = OrbitalsTable(player_limit=6)
    table.playerJoins("Ann")
    table.playerJoins("Bob")
    table.playerJoins("Cat")
    table.playerJoins("Don")
    table.playerJoins("Eve")
    assert not table.playerJoins("Fog")
    assert table.playerJoins("Gus") == "player limit has been reached"

def test_sad_player_name_exists():
    table = OrbitalsTable()
    table.playerJoins("Ann")
    assert table.playerJoins("Ann") == "player name exists"
    

# @pytest.fixture
# def create_cluster(sectors=sector_quantity):
#     cluster = OrbitalsCluster(sectorCount=sectors, callback=cluster_message)
#     yield cluster

# def test_sector_count(create_cluster):
#     cluster = create_cluster
#     assert len(cluster.getClusterStatus()) == sector_quantity