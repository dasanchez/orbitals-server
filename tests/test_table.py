import pytest
from collections import Counter
import asyncio
import time
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

@pytest.fixture
def start_game():
    ot = OrbitalsTable()
    ot.playerJoins("Ann")
    ot.playerJoins("Bob")
    ot.playerJoins("Cary")
    ot.playerJoins("Dina")
    ot.playerJoins("Elsa")
    ot.playerJoins("Finn")
    ot.playerJoins("Gina")
    ot.playerJoins("Hank")
    ot.teamRequest("Ann", "blue")
    ot.teamRequest("Bob", "blue")
    ot.teamRequest("Cary", "blue")
    ot.teamRequest("Dina", "blue")
    ot.teamRequest("Elsa", "orange")
    ot.teamRequest("Finn", "orange")
    ot.teamRequest("Gina", "orange")
    ot.teamRequest("Hank", "orange")
    ot.roleRequest("Ann", "hub")
    ot.roleRequest("Elsa", "hub")
    ot.startRequest("Ann")
    ot.startRequest("Elsa")
    yield ot

def test_set_timeout():
    table = OrbitalsTable(time_limit=60)
    assert table.status()["time_limit"] == 60

def test_player_count_limit():
    table = OrbitalsTable(player_limit=4)
    set_limit = table.status()['player_limit']
    assert set_limit == 4

def test_accept_full_teams(create_game_and_teams):
    table = create_game_and_teams
    assert table.players()["Ann"][0] == "blue"
    assert table.players()["Gina"][0] == "orange"
    assert table.players()["Ann"][0] == "blue"

def test_waiting_players_to_waiting_start():
    ot = OrbitalsTable()
    ot.playerJoins("Ann")
    ot.playerJoins("Bob")
    ot.playerJoins("Elsa")
    ot.playerJoins("Finn")
    ot.teamRequest("Ann", "blue")
    ot.teamRequest("Bob", "blue")
    ot.teamRequest("Elsa", "orange")
    ot.roleRequest("Ann", "hub")
    ot.roleRequest("Elsa","hub")
    assert ot.status()["game_state"] == "WAITING_PLAYERS"
    ot.teamRequest("Finn", "orange")
    assert ot.status()["game_state"] == "WAITING_START"

def test_two_hubs_requested(create_game_and_teams):
    table = create_game_and_teams
    assert table.players()["Ann"][1] == "hub"
    assert table.players()["Elsa"][1] == "hub"

def test_second_hub_requested_same_team(create_game_and_teams):
    table = create_game_and_teams
    table.roleRequest("Finn", "hub")
    assert table.players()["Finn"][1] == "orbital"

def test_start_requests(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Bob")
    assert table.status()["game_state"] ==  GameState.WAITING_START
    table.startRequest("Elsa")
    assert table.status()["game_state"] ==  GameState.WAITING_CLUE
    table.stopTimer()
    
def test_tile_board_created(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    assert table.tiles()['APPLE'] == ''
    table.stopTimer()

def test_assign_first_turn(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")

    # count tiles, turn should belong to colour with higher count
    tile_counter = Counter([tile[0] for tile in table._board._tiles.values()])
    blue_tiles = tile_counter['blue']
    orange_tiles = tile_counter['orange']
    if blue_tiles > orange_tiles:
        assert table.status()["current_turn"] == 'blue'
    table.stopTimer()

@pytest.mark.asyncio
async def test_switch_teams_after_timeout_waiting_clue(create_game_and_teams):
    table = create_game_and_teams
    table.setTimeLimit(seconds=0.05)
    assert table.status()["time_limit"] == 0.05
    table.startRequest("Ann")
    table.startRequest("Elsa")
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    assert table.status()["current_turn"] == "blue"
    await asyncio.sleep(0.06)
    assert table.status()["current_turn"] == "orange"
    table.stopTimer()

@pytest.mark.asyncio
async def test_switch_teams_after_timeout_waiting_guess(create_game_and_teams):
    table = create_game_and_teams
    table.setTimeLimit(seconds=0.05)
    assert table.status()["time_limit"] == 0.05
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", response=True)
    assert table.status()["game_state"] == GameState.WAITING_GUESS
    assert table.status()["current_turn"] == "blue"
    await asyncio.sleep(0.06)
    assert table.status()["current_turn"] == "orange"
    table.stopTimer()

@pytest.mark.asyncio
async def test_waiting_guess_and_waiting_clue_timeout(create_game_and_teams):
    table = create_game_and_teams
    table.setTimeLimit(seconds=0.05)
    assert table.status()["time_limit"] == 0.05
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", response=True)
    assert table.status()["game_state"] == GameState.WAITING_GUESS
    assert table.status()["current_turn"] == "blue"
    await asyncio.sleep(0.06)
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    assert table.status()["current_turn"] == "orange"
    await asyncio.sleep(0.06)
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    assert table.status()["current_turn"] == "blue"
    table.stopTimer()

def test_accept_clue(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    assert table.newClue("Ann", "FRUIT") == "clue submitted"
    assert table.status()["game_state"] == GameState.WAITING_APPROVAL
    table.stopTimer()

def test_approve_clue(start_game):
    table = start_game
    table.newClue("Ann", "FRUIT")
    assert table.status()["game_state"] == GameState.WAITING_APPROVAL
    table.clueResponse("Elsa", True)
    assert table.status()["game_state"] == GameState.WAITING_GUESS
    table.stopTimer()

def test_reject_clue(start_game):
    table = start_game
    table.newClue("Ann", "FRUIT")
    assert table.status()["game_state"] == GameState.WAITING_APPROVAL
    table.clueResponse("Elsa", False)
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    table.stopTimer()

@pytest.mark.asyncio
async def test_waiting_approval_timeout(create_game_and_teams):
    table = create_game_and_teams
    table.setTimeLimit(seconds=0.05)
    assert table.status()["time_limit"] == 0.05
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "FRUIT")
    assert table.status()["game_state"] == GameState.WAITING_APPROVAL
    # await asyncio.sleep(0.08)
    # assert table.status()["game_state"] == GameState.WAITING_GUESS
    # assert table.status()["current_turn"] == "blue"
    table.stopTimer()

def test_single_guess_turn_switch(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", True)
    table.newGuess("Bob", "APPLE")
    assert table.tiles()["APPLE"]
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    assert table.status()["current_turn"] == 'orange'
    table.stopTimer()

def test_accept_clue_with_count(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", True)
    table.newGuess("Bob", "APPLE")
    table.newClue("Elsa", "COUNTRY", 2)
    assert table.currentClue() == "COUNTRY"
    assert table.guessesLeft() == 2
    table.stopTimer()

def test_multiple_guesses_turn_switch(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", True)
    table.newGuess("Bob", "APPLE")
    table.newClue("Elsa", "COUNTRY", 2)
    table.clueResponse("Ann", True)
    table.newGuess("Finn", "INDIA")
    table.newGuess("Finn", "MEXICO")
    assert table.tiles()["INDIA"][1]
    assert table.tiles()["MEXICO"][1]
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    assert table.status()["current_turn"] == 'blue'
    table.stopTimer()

def test_switch_turn_incorrect_guess(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", True)
    table.newGuess("Bob", "APPLE")
    table.newClue("Elsa", "COUNTRY", 2)
    table.clueResponse("Ann", True)
    table.newGuess("Finn", "FLAG")
    assert table.tiles()["FLAG"]
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    assert table.status()["current_turn"] == 'blue'
    table.stopTimer()

def test_play_to_win(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "ALLWORDS", 8)
    table.clueResponse("Elsa", True)
    table.newGuess("Bob", "APPLE")
    table.newGuess("Bob", "BOMB")
    table.newGuess("Bob", "CROWN")
    table.newGuess("Bob", "DAD")
    table.newGuess("Bob", "EASTER")
    table.newGuess("Bob", "FLAG")
    table.newGuess("Bob", "GIANT")
    table.newGuess("Bob", "HOME")
    assert table.status()["game_state"] == GameState.GAME_OVER
    assert table.status()["winner"] == 'blue'
    
def test_replay_requests(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "ALLWORDS", 8)
    table.clueResponse("Elsa", True)
    table.newGuess("Bob", "APPLE")
    table.newGuess("Bob", "BOMB")
    table.newGuess("Bob", "CROWN")
    table.newGuess("Bob", "DAD")
    table.newGuess("Bob", "EASTER")
    table.newGuess("Bob", "FLAG")
    table.newGuess("Bob", "GIANT")
    table.newGuess("Bob", "HOME")
    table.replayRequest("Ann")
    table.replayRequest("Bob")     
    table.replayRequest("Cary")
    table.replayRequest("Dina")
    table.replayRequest("Elsa")
    table.replayRequest("Finn")
    table.replayRequest("Gina")
    table.replayRequest("Hank")
    assert table.status()["game_state"] == GameState.WAITING_START

def test_get_approver(start_game):
    table = start_game
    assert table.getApprover() == "Elsa"
    table.stopTimer()

def test_player_leaves_table():
    table = OrbitalsTable()
    table.playerJoins("Ann")
    table.playerLeaves("Ann")
    assert len(table.status()["players"]) == 0

def test_no_hub_leaves_game_over(start_game):
    table = start_game
    table.newClue("Ann", "EVERYTHING", 10)
    table.clueResponse("Elsa", True)
    assert table.status()['game_state'] == GameState.WAITING_GUESS
    table.newGuess("Bob", "APPLE")
    table.newGuess("Bob", "BOMB")
    table.newGuess("Bob", "CROWN")
    table.newGuess("Bob", "DAD")
    table.newGuess("Bob", "EASTER")
    table.newGuess("Bob", "FLAG")
    table.newGuess("Bob", "GIANT")
    table.newGuess("Bob", "HOME")
    assert table.status()['game_state'] == GameState.GAME_OVER
    table.replayRequest("Ann")
    table.replayRequest("Dina")
    table.replayRequest("Elsa")
    table.replayRequest("Finn")
    table.replayRequest("Gina")
    table.replayRequest("Hank")
    table.playerLeaves("Bob")
    assert table.status()['game_state'] == GameState.GAME_OVER
    table.playerLeaves("Cary")
    assert table.status()['game_state'] == GameState.WAITING_START

def test_last_no_hub_leaves_waiting_start_one_start_request(create_game_and_teams):
    table = create_game_and_teams
    assert table.status()["game_state"] == GameState.WAITING_START
    table.startRequest("Ann")
    table.playerLeaves("Bob")
    table.playerLeaves("Cary")
    table.playerLeaves("Dina")
    assert table.status()['game_state'] == GameState.WAITING_PLAYERS
    assert not any(table.status()["start_game"].values())

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
    table.newClue("Ann", "COUNTRY", 1)
    table.clueResponse("Elsa", True)
    assert table.status()['game_state'] == GameState.WAITING_GUESS
    table.playerLeaves("Bob")
    table.playerLeaves("Cary")
    table.playerLeaves("Dina")
    assert table.status()['game_state'] == GameState.WAITING_PLAYERS

def test_last_no_hub_leaves_game_over(start_game):
    table = start_game
    table.newClue("Ann", "EVERYTHING", 10)
    table.clueResponse("Elsa", True)
    assert table.status()['game_state'] == GameState.WAITING_GUESS
    table.newGuess("Bob", "APPLE")
    table.newGuess("Bob", "BOMB")
    table.newGuess("Bob", "CROWN")
    table.newGuess("Bob", "DAD")
    table.newGuess("Bob", "EASTER")
    table.newGuess("Bob", "FLAG")
    table.newGuess("Bob", "GIANT")
    table.newGuess("Bob", "HOME")
    assert table.status()['game_state'] == GameState.GAME_OVER
    table.playerLeaves("Bob")
    table.playerLeaves("Cary")
    table.playerLeaves("Dina")
    assert table.status()['game_state'] == GameState.WAITING_PLAYERS

def test_hub_leaves_waiting_start_one_start_request(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    assert table.status()['game_state'] == GameState.WAITING_START
    table.playerLeaves("Elsa")
    assert table.status()['game_state'] == GameState.WAITING_PLAYERS
    assert not any(table.status()["start_game"].values())

def test_hub_leaves_waiting_clue(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    assert table.status()['game_state'] == GameState.WAITING_CLUE
    table.playerLeaves("Ann")
    assert table.status()['game_state'] == GameState.WAITING_PLAYERS

def test_hub_leaves_waiting_guess(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    table.newClue("Ann", "COUNTRY", 1)
    table.clueResponse("Elsa", True)
    assert table.status()['game_state'] == GameState.WAITING_GUESS
    table.playerLeaves("Elsa")
    assert table.status()['game_state'] == GameState.WAITING_PLAYERS

def test_hub_leaves_waiting_game_over(start_game):
    table = start_game
    table.newClue("Ann", "EVERYTHING", 10)
    table.clueResponse("Elsa", True)
    assert table.status()['game_state'] == GameState.WAITING_GUESS
    table.newGuess("Bob", "APPLE")
    table.newGuess("Bob", "BOMB")
    table.newGuess("Bob", "CROWN")
    table.newGuess("Bob", "DAD")
    table.newGuess("Bob", "EASTER")
    table.newGuess("Bob", "FLAG")
    table.newGuess("Bob", "GIANT")
    table.newGuess("Bob", "HOME")
    assert table.status()['game_state'] == GameState.GAME_OVER
    table.playerLeaves("Elsa")
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
    assert table.startRequest("Ann") == "orbital roles are not filled"
    table.teamRequest("Bob", "orange")
    assert table.startRequest("Bob") == "only hub roles can request start"
    assert not table.startRequest("Ann")
    table.stopTimer()

def test_cap_guess_count_unexposed_tiles(create_game_and_teams):
    table = create_game_and_teams
    table.startRequest("Ann")
    table.startRequest("Elsa")
    assert table.status()["tiles_left"]["blue"] == 8
    table.newClue("Ann", "COUNTRY", 12)
    assert table.guessesLeft() == 8
    table.stopTimer()

def test_sad_player_limit_reached():
    table = OrbitalsTable(player_limit=6)
    table.playerJoins("Ann")
    table.playerJoins("Bob")
    table.playerJoins("Cat")
    table.playerJoins("Don")
    table.playerJoins("Eve")
    assert table.playerJoins("Fog") == "name accepted"
    assert table.playerJoins("Gus") == "player limit has been reached"

def test_sad_player_name_exists():
    table = OrbitalsTable()
    table.playerJoins("Ann")
    assert table.playerJoins("Ann") == "player name exists"

def test_sad_clue_wrong_team(start_game):
    table = start_game
    assert table.newClue("Finn", "FRUIT") == "it is the other team's turn"
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    table.stopTimer()

def test_sad_clue_wrong_role(start_game):
    table = start_game
    assert table.newClue("Bob", "FRUIT") == "only hub can submit clues"
    assert table.status()["game_state"] == GameState.WAITING_CLUE
    table.stopTimer()

def test_sad_clue_wrong_state(start_game):
    table = start_game
    assert table.newClue("Ann", "FRUIT") == "clue submitted"
    assert table.status()["game_state"] == GameState.WAITING_APPROVAL
    assert table.newClue("Ann", "FRUIT") == "not awaiting clues, state: WAITING_APPROVAL"
    table.stopTimer()

def test_sad_guess_wrong_team(start_game):
    table = start_game
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", True)
    assert table.status()["game_state"] == GameState.WAITING_GUESS
    assert table.newGuess("Finn", "ORANGE") == "it is the other team's turn"
    table.stopTimer()
    
def test_sad_guess_wrong_role(start_game):
    table = start_game
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", True)
    assert table.status()["game_state"] == GameState.WAITING_GUESS
    assert table.newGuess("Ann", "ORANGE") == "hubs cannot submit guesses"
    table.stopTimer()

def test_sad_guess_wrong_state(start_game):
    table = start_game
    assert table.newGuess("Ann", "FRUIT") == "not awaiting guesses"
    table.stopTimer()

def test_sad_guess_not_on_board(start_game):
    table = start_game
    table.newClue("Ann", "FRUIT")
    table.clueResponse("Elsa", response=True)
    assert table.status()["game_state"] == GameState.WAITING_GUESS
    assert table.newGuess("Bob", "ORANGE") == "guess is not on the board"
    table.stopTimer()
      
def test_sad_clue_response_wrong_team(start_game):
    table = start_game
    table.newClue("Ann", "FRUIT")
    assert table.clueResponse("Ann", True) == "it is the other team's turn"
    table.stopTimer()

def test_sad_clue_response_wrong_role(start_game):
    table = start_game
    table.newClue("Ann", "FRUIT")
    assert table.clueResponse("Finn", True) == "only hub can respond to clues"
    table.stopTimer()

def test_sad_clue_response_wrong_state(start_game):
    table = start_game
    assert table.clueResponse("Ann", True) == "not awaiting clue responses"
    table.stopTimer()
