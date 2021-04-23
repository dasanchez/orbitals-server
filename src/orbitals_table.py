"""
orbitals_board.py
Orbitals board engine
Tracks:
- teams
- players
- turns
"""
from enum import Enum, auto

# import asyncio
# import json
# import or_comms as orbComms
# from or_players import OrbitalsPlayers
# from or_timer import OrbitalsTimer
from collections import Counter
from orbitals_board import OrbitalsBoard


class GameState(Enum):
    WAITING_PLAYERS = 1
    WAITING_START = auto()
    WAITING_CLUE = auto()
    WAITING_GUESS = auto()
    WAITING_APPROVAL = auto()
    GAME_OVER = auto()


class OrbitalsTable:
    """ Top level class """

    def __init__(self, words_source=None, player_limit: int=16):
        self._players = dict()
        self._player_limit = player_limit
        self._start_game = {"blue": False, "orange": False}
        self._game_state = GameState.WAITING_PLAYERS
        self._board = OrbitalsBoard(word_bag=words_source)
        self._current_turn = ''
        self._current_clue = ''
        self._current_guess_count = 0
        self._winning_team = ''
        self._game_history = list()

    def status(self):
        """
        Returns full game status as a dict:
        player_limit (default=16)
        player_count
        game_state
        current_turn
        orange_tiles_left
        blue_tiles_left
        """
        status = dict()
        status["player_limit"] = self._player_limit
        status["player_count"] = len(self._players)
        status["spots_available"] = status["player_limit"]-status["player_count"]
        status["game_state"] = self._game_state
        status["current_turn"] = self._current_turn
        status["guess_count"] = self._current_guess_count
        status["tiles"] = self.tiles()
        status["orange_tiles_left"] = self._board.tiles_left(team="orange")
        status["blue_tiles_left"] = self._board.tiles_left(team="blue")
        status["players"] = self._players

        # status["blue_tiles_guessed"] = 
        # status["blue_tiles_left"] = 
        # status["orange_tiles_guessed"] = 
        # status["orange_tiles_left"] =
        # status["neutral_tiles_guessed"] = 
        # status["neutral_tiles_left"] = 
        return status

    def state(self):
        return self._game_state, self._current_turn

    def playerJoins(self, name: str):
        if len(self._players) >= self._player_limit:
            # player limit has been reached
            return "player limit has been reached"
        elif name in self._players.keys():
            # player name exists
            return "player name exists"
        else:
            self._players[name] = ["no-team", "no-hub", False]
            return False
       
    def playerLeaves(self, name: str):
        # check game state
        if self._game_state == GameState.WAITING_PLAYERS:
            del self._players[name]
        elif self._game_state == GameState.WAITING_START or\
             self._game_state == GameState.WAITING_CLUE or\
             self._game_state == GameState.WAITING_APPROVAL or\
             self._game_state == GameState.WAITING_GUESS:
            # get team's no-hubs
            no_hubs = self.filter_players(teams=[self.playerTeam(name)], role="no-hub")

            # if only one no-hub remains in the team
            # or
            # the player leaving is a hub,
            # switch state to WAITING PLAYERS and reset game status:
            if len(no_hubs) == 1 or self._players[name][1] == 'hub':
                self._game_state = GameState.WAITING_PLAYERS
                self._winning_team = ''
                self._current_clue = ''
                self._current_guess_count = 0
                for player in self._players.keys():
                    self._players[player][2] = False

            del self._players[name]

    def playerTeam(self, name: str):
        return self._players[name][0]

    def playerRole(self, name: str):
        return self._players[name][1]

    def teamRequest(self, name: str, team: str):
        self._players[name][0] = team
    
    def roleRequest(self, name: str, role: str):
        """
        Assign requested role only if no one else in the team has it
        """
        # we have a dictionary, collect all the values
        team_roles = [spec[1] for spec in self._players.values() \
            if spec[0] == self.playerTeam(name)]
        if "hub" not in team_roles:
            self._players[name][1] = role

        # check game state
        if self._game_state == GameState.WAITING_PLAYERS:
            # do we have one hub for both teams?
            blue_hub = self.filter_players(teams=["blue"], role="hub")
            blue_no_hubs = self.filter_players(teams=["blue"], role="no-hub")
            orange_hub = self.filter_players(teams=["orange"], role="hub")
            orange_no_hubs = self.filter_players(teams=["orange"], role="no-hub")

            if (blue_hub and blue_no_hubs) and (orange_hub and orange_no_hubs):
                self._game_state = GameState.WAITING_START

    def players(self):
        return self._players

    def startRequest(self, name: str):
        # do we have at least one player in each role?
        # 1 hub and 1 no-hub per team
        blue_roles = [role[1] for (player, role) in self._players.items() if self._players[player][0] == 'blue']
        orange_roles = [role[1] for (player, role) in self._players.items() if self._players[player][0] == 'orange']
        if not ("hub" in blue_roles and "hub" in orange_roles):
            return "hub roles are not filled"
        elif not ("no-hub" in blue_roles and "no-hub" in orange_roles):
            return "no-hub roles are not filled"

        elif self.playerRole(name) != 'hub':
            return "only hub roles can request start" 
        
        self._start_game[self.playerTeam(name)] = True
        if all(self._start_game.values()):
            self.startNewGame()
            
    def startNewGame(self):
        self._board.generateTiles()

        # assign first turn
        self._current_turn = self._board.firstTurn()
        
        # set new state
        self._game_state = GameState.WAITING_CLUE
        
        # Reset start_game flags
        for key in self._start_game.keys():
            self._start_game[key] = False

    def newClue(self, name: str, clue: str, guess_count: int=1):
        if self._game_state != GameState.WAITING_CLUE:
            return "not awaiting clues"

        if self.playerTeam(name) != self._current_turn:
            return "it is the other team's turn"
        
        if self.playerRole(name) == 'no-hub':
            return "only hub can submit clues"

        self._current_clue = clue
        self._current_guess_count = min(guess_count, self._board.tiles_left(team=self.playerTeam(name)))
        self._game_state = GameState.WAITING_APPROVAL
        return False

    def clueResponse(self, name: str, response: bool=True):
        # is the clue response expected?
        if self._game_state != GameState.WAITING_APPROVAL:
            return "not awaiting clue responses"

        # is player on the opposite team?
        if self.playerTeam(name) == self._current_turn:
            return "it is the other team's turn"
        
        # is player not a hub?
        if self.playerRole(name) != 'hub':
            return "only hub can respond to clues"

        if not response:
            self._game_state = GameState.WAITING_CLUE
        else:
            self._game_state = GameState.WAITING_GUESS

    def newGuess(self, name: str, guess: str):
        if self._game_state != GameState.WAITING_GUESS:
            return "not awaiting guesses"

        if self.playerTeam(name) != self._current_turn:
            return "it is the other team's turn"
        
        if self.playerRole(name) == 'hub':
            return "hubs cannot submit guesses"

        self._board.flipTile(guess)

        # has this team won?
        winner = self._board.winner()
        if winner:
            self._winning_team = winner
            self._game_state = GameState.GAME_OVER
            self._current_turn = ''
            self._current_clue = ''
            self._current_guess_count = 0
            return
        # switch if guess is for opposing team
        if self.tiles()[guess] != self._current_turn:
            self._current_guess_count = 1
        self._current_guess_count -= 1
        # switch if we're out of guesses
        if (self._current_guess_count) == 0:
            self.switchTurns()

    def switchTurns(self):
        self._game_state = GameState.WAITING_CLUE
        if self._current_turn == 'blue':
            self._current_turn = 'orange'
        else:
            self._current_turn = 'blue'

    def tiles(self):
        return self._board.tiles()

    def currentClue(self):
        return self._current_clue, self._current_guess_count

    def winner(self):
        return self._winning_team

    def replayRequest(self, name: str):
        self._players[name][2]=True

        ready_flags = [player[2] for player in self._players]
        if all(ready_flags):
            self._game_state = GameState.WAITING_START
            self._winning_team = ''
            self._current_clue = ''
            self._current_guess_count = 0
            for player in self._players.keys():
                self._players[player][2] = False

    def filter_players(self, *, teams: list, role: str):
        players = list()
        for team in teams:
            players.extend([player for player, data in self._players.items() if data[0] == team and data[1] == role])
        return players


