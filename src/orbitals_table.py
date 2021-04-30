"""
orbitals_board.py
Orbitals board engine
Tracks:
- teams
- players
- turns
"""
from enum import Enum, auto

from collections import Counter
from threading import Timer
from orbitals_board import OrbitalsBoard

class GameState(Enum):
    WAITING_PLAYERS = 1
    WAITING_START = auto()
    WAITING_CLUE = auto()
    WAITING_GUESS = auto()
    WAITING_APPROVAL = auto()
    GAME_OVER = auto()


class OrbitalsTable:
    def __init__(self, player_limit: int=16,\
                       words_source=None,\
                       tile_count: int=16,\
                       time_limit: float=30):
        self._players = dict()
        self._player_limit = player_limit
        self._time_limit = time_limit
        self._timer = None
        self._start_game = {"blue": False, "orange": False}
        self._game_state = GameState.WAITING_PLAYERS
        self._board = OrbitalsBoard(word_bag=words_source, tile_count=tile_count)
        self._current_turn = ''
        self._current_clue = ''
        self._current_guess_count = 0
        self._winning_team = ''
        self._game_history = list()

    def status(self):
        """
        Returns full game status as a dict:
        player_limit
        time_limit
        players
        game_state
        start_game
        wnner
        current_turn
        guess_count
        tiles
        tiles_left
        """
        status = dict()
        status["player_limit"] = self._player_limit
        status["time_limit"] = self._time_limit
        status["players"] = self._players
        status["game_state"] = self._game_state
        status["start_game"] = self._start_game
        status["winner"] = self._winning_team
        status["current_turn"] = self._current_turn
        status["guess_count"] = self._current_guess_count
        status["tiles"] = self.tiles()
        status["tiles_left"] = dict()
        status["tiles_left"]["orange"] = self._board.tiles_left(team="orange")
        status["tiles_left"]["blue"] = self._board.tiles_left(team="blue")

        return status

    def setTimeLimit(self, *, seconds: float):
        # Set timeout in seconds
        self._time_limit = seconds

    def timerStatus(self):
        return self._timer.is_alive()

    def stopTimer(self):
        if self._timer:
            self._timer.cancel()
            while self._timer.is_alive():
                pass

    def timerTimeout(self):
        self._timer.cancel()
            
        if self._game_state == GameState.WAITING_APPROVAL:
            self._game_state = GameState.WAITING_GUESS
        else:
            self._game_state = GameState.WAITING_CLUE
            self.switchTurns()

        self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        self._timer.start()
        return

    def playerJoins(self, name: str):
        if len(self._players) >= self._player_limit:
            # player limit has been reached
            return "player limit has been reached"
        elif name in self._players.keys():
            # player name exists
            return "player name exists"
        else:
            self._players[name] = ["no-team", "no-hub", False]
       
    def playerLeaves(self, name: str):
        # check game state
        if self._game_state == GameState.WAITING_START or\
            self._game_state == GameState.WAITING_CLUE or\
            self._game_state == GameState.WAITING_APPROVAL or\
            self._game_state == GameState.WAITING_GUESS or\
            self._game_state == GameState.GAME_OVER:
            
            # get team's no-hubs
            no_hubs = self.filter_players(teams=[self.playerTeam(name)], role="no-hub")

            # if only one no-hub remains in the team
            # or
            # the player leaving is a hub,
            # switch state to WAITING PLAYERS and reset game status:
            if len(no_hubs) == 1 or self._players[name][1] == 'hub':
                self.stopTimer()
                self._game_state = GameState.WAITING_PLAYERS
                for team in self._start_game.keys():
                    self._start_game[team] = False
                self._winning_team = ''
                self._current_clue = ''
                self._current_guess_count = 0
                for player in self._players.keys():
                    self._players[player][2] = False

        del self._players[name]
        self.readyToRestart()

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
        # Reset start_game flags
        for key in self._start_game.keys():
            self._start_game[key] = False

        self._board.generateTiles()

        # assign first turn
        self._current_turn = self._board.firstTurn()
        
        # set new state
        self._game_state = GameState.WAITING_CLUE
        
        self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        self._timer.start()
        
    def newClue(self, name: str, clue: str, guess_count: int=1):
        if self._game_state != GameState.WAITING_CLUE:
            return f"not awaiting clues, state: {self._game_state}"

        if self.playerTeam(name) != self._current_turn:
            return "it is the other team's turn"
        
        if self.playerRole(name) == 'no-hub':
            return "only hub can submit clues"

        self._timer.cancel()
        while self._timer.is_alive():
            pass
        self._current_clue = clue
        self._current_guess_count = min(guess_count, self._board.tiles_left(team=self.playerTeam(name)))
        self._game_state = GameState.WAITING_APPROVAL

        self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        self._timer.start()
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

        self.stopTimer()

        if not response:
            self._game_state = GameState.WAITING_CLUE
        else:
            self._game_state = GameState.WAITING_GUESS
        
        self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        self._timer.start()
        return False

    def newGuess(self, name: str, guess: str):
        if self._game_state != GameState.WAITING_GUESS:
            return "not awaiting guesses"

        if self.playerTeam(name) != self._current_turn:
            return "it is the other team's turn"
        
        if self.playerRole(name) == 'hub':
            return "hubs cannot submit guesses"

        if guess not in self.tiles().keys():
            return "guess is not on the board"

        self.stopTimer()
        
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
        if self._current_guess_count == 0:
            self._game_state = GameState.WAITING_CLUE
            self.switchTurns()

        # start timer
        self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        self._timer.start()

    def switchTurns(self):
        if self._current_turn == 'blue':
            self._current_turn = 'orange'
        else:
            self._current_turn = 'blue'

    def tiles(self):
        return self._board.tiles()

    def currentClue(self):
        return self._current_clue

    def winner(self):
        return self._winning_team

    def replayRequest(self, name: str):
        self._players[name][2]=True
        self.readyToRestart()

    def filter_players(self, *, teams: list, role: str):
        players = list()
        for team in teams:
            players.extend([player for player, data in self._players.items() if data[0] == team and data[1] == role])
        return players

    def readyToRestart(self):
        # check all ready flags
        if all([player[2] for player in self._players.values()]):
            self._game_state = GameState.WAITING_START
            self._winning_team = ''
            self._current_clue = ''
            self._current_guess_count = 0
            for player in self._players.keys():
                self._players[player][2] = False
            return True