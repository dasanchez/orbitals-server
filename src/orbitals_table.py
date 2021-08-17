"""
orbitals_board.py
Orbitals board engine
Tracks:
- teams
- players
- turns
"""
from enum import Enum, auto

# from threading import Timer
from orbitals_board import OrbitalsBoard

class GameState(str, Enum):
    WAITING_PLAYERS = "WAITING_PLAYERS"
    WAITING_START = "WAITING_START"
    WAITING_CLUE = "WAITING_CLUE"
    WAITING_GUESS = "WAITING_GUESS"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    GAME_OVER = "GAME_OVER"

class OrbitalsTable:
    def __init__(self, player_limit: int=16,\
                       words_source=None,\
                       tile_count: int=16,\
                    #    time_limit: float=30,\
                       callback=None):
        self._players = dict()
        self._player_limit = player_limit
        # self._time_limit = time_limit
        # self._timer = None
        # self._tick_timer = None
        # self._time_left = 0
        self._start_game = {"blue": False, "orange": False}
        self._game_state = GameState.WAITING_PLAYERS
        self._board = OrbitalsBoard(word_bag=words_source, tile_count=tile_count)
        self._current_turn = ''
        self._current_clue = ''
        self._current_guess_count = 0
        self._winning_team = ''
        self._callback = callback

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
        # status["time_limit"] = self._time_limit
        status["players"] = self._players
        status["game_state"] = self._game_state
        status["start_game"] = self._start_game
        status["winner"] = self._winning_team
        status["current_turn"] = self._current_turn
        # status["guess_count"] = self._current_guess_count
        status["tiles"] = self.tiles()
        status["tiles_left"] = dict()
        status["tiles_left"]["orange"] = self._board.tiles_left(team="orange")
        status["tiles_left"]["blue"] = self._board.tiles_left(team="blue")

        return status

    # def setTimeLimit(self, *, seconds: float):
    #     # Set timeout in seconds
    #     self._time_limit = seconds

    # def timerStatus(self):
    #     return self._timer.is_alive()

    # def stopTimer(self):
    #     if self._tick_timer:
    #         self._tick_timer.cancel()
    #     if self._timer:
    #         self._timer.cancel()

    # def tick(self):
    #     if self._timer.is_alive():
    #         self._time_left -= 1
    #         if self._callback:
    #             self._callback(["tick", self._time_left])
    #         self._tick_timer = Timer(interval=1.0, function=self.tick)
    #         self._tick_timer.start()

    # def timerTimeout(self):
        # self._timer.cancel()
        # if self._game_state == GameState.WAITING_APPROVAL:
        #     self._game_state = GameState.WAITING_GUESS
        # else:
        #     self._game_state = GameState.WAITING_CLUE
        #     self.switchTurns()

        # self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        # if self._time_limit > 1.0:
        #     self._time_limit = self._time_limit
        #     self._tick_timer = Timer(interval=1.0, function=self.tick)
        #     self._tick_timer.start()
        # self._timer.start()

        # if self._callback:
        #     self._callback(["timeout"])
        # return

    def playerJoins(self, name: str):
        if len(self._players) >= self._player_limit:
            # player limit has been reached
            return "player limit has been reached"
        elif name in self._players.keys():
            # player name exists
            return "player name exists"
        else:
            self._players[name] = ["no-team", "orbital", False]
            return "name accepted"
       
    def playerLeaves(self, name: str):
        # check game state
        if self._game_state == GameState.WAITING_START or\
            self._game_state == GameState.WAITING_CLUE or\
            self._game_state == GameState.WAITING_APPROVAL or\
            self._game_state == GameState.WAITING_GUESS or\
            self._game_state == GameState.GAME_OVER:
            
            # get team's orbitals
            no_hubs = self.filter_players(teams=[self.playerTeam(name)], role="orbital")

            # if only one orbital remains in the team
            # or
            # the player leaving is a hub,
            # switch state to WAITING PLAYERS and reset game status:
            if len(no_hubs) == 1 or self._players[name][1] == 'hub':
                # self.stopTimer()
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
        # can only change team in "WAITING_PLAYERS" and "WAITING_START" states
        if self._game_state == GameState.WAITING_PLAYERS or\
           self._game_state == GameState.WAITING_START:
            return self.changeTeam(name, team)
        else:
            return "team changes are only allowed in WAITING_PLAYERS and WAITING_START states"

    def changeTeam(self, name: str, team: str):
        if self.playerTeam(name) == "no-team":
            self._players[name][0] = team
        elif self.playerRole(name) == "hub":
            self._players[name] = [team, "orbital", False]
        else:
            self._players[name] = [team, "orbital", False]
        self.rosterUpdate()
        return "team accepted"
    
    def roleRequest(self, name: str, role: str):
        if (self.playerTeam(name) != "blue") and (self.playerTeam(name) != "orange"):
            return "player must belong to team to request role"
        # can only change role in "WAITING_PLAYERS" and "WAITING_START" states
        elif (self._game_state != GameState.WAITING_PLAYERS) and\
           self._game_state != GameState.WAITING_START:
            return "role changes are only allowed in WAITING_PLAYERS and WAITING_START states"
        elif self.filter_players(teams=[self.playerTeam(name)], role=role):
            return "hub role not available"
        else:
            return self.changeRole(name, role)
        
    def changeRole(self, name: str, role: str):
        """
        Assign requested role only if no one else in the team has it
        """
        # we have a dictionary, collect all the values
        team_roles = [spec[1] for spec in self._players.values() \
            if spec[0] == self.playerTeam(name)]
        
        if role == "hub":
            if "hub" not in team_roles:
                self._players[name][1] = role
                self.rosterUpdate()
                return "role accepted"
            else:
                return "role not accepted"
        else:
            self._players[name][1] = role
            self.rosterUpdate()
            return "role accepted"

    def players(self):
        return self._players

    def getApprover(self):
        if self._current_turn == "blue":
            return self.filter_players(teams=["orange"], role="hub").pop()
        else:
            return self.filter_players(teams=["blue"], role="hub").pop()

    def startRequest(self, name: str):
        # do we have at least one player in each role?
        # 1 hub and 1 orbital per team
        blue_roles = [role[1] for (player, role) in self._players.items() if self._players[player][0] == 'blue']
        orange_roles = [role[1] for (player, role) in self._players.items() if self._players[player][0] == 'orange']
        if not ("hub" in blue_roles and "hub" in orange_roles):
            return "hub roles are not filled"
        elif not ("orbital" in blue_roles and "orbital" in orange_roles):
            return "orbital roles are not filled"

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
        
        # self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        # if self._time_limit > 1.0:
        #     self._time_left = self._time_limit
        #     self._tick_timer = Timer(interval=1.0, function=self.tick)
        #     self._tick_timer.start()
        # self._timer.start()
        
        
    def newClue(self, name: str, clue: str, guess_count: int=1):
        if self._game_state != GameState.WAITING_CLUE:
            return f"not awaiting clues, state: {self._game_state}"

        if self.playerTeam(name) != self._current_turn:
            return "it is the other team's turn"
        
        if self.playerRole(name) == 'orbital':
            return "only hub can submit clues"

        # self.stopTimer()

        # while self._timer.is_alive() or self._tick_timer.is_alive():
            # pass
        self._current_clue = clue
        self._current_guess_count = min(guess_count, self._board.tiles_left(team=self.playerTeam(name)))
        self._game_state = GameState.WAITING_APPROVAL

        # self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        # if self._time_limit > 1.0:
            # self._time_left = self._time_limit
            # self._tick_timer = Timer(interval=1.0, function=self.tick)
            # self._tick_timer.start()
        # self._timer.start()
        return "clue submitted"

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

        # self.stopTimer()

        if not response:
            self._game_state = GameState.WAITING_CLUE
        else:
            self._game_state = GameState.WAITING_GUESS
        
        # self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
        # if self._time_limit > 1.0:
        #     self._time_left = self._time_limit
        #     self._tick_timer = Timer(interval=1.0, function=self.tick)
        #     self._tick_timer.start()
        # self._timer.start()
        
        if not response:
            return "clue was rejected"
        else:
            return "clue was accepted"

    def newGuess(self, name: str, guess: str):
        if self._game_state != GameState.WAITING_GUESS:
            return "not awaiting guesses"

        if self.playerTeam(name) != self._current_turn:
            return "it is the other team's turn"
        
        if self.playerRole(name) == 'hub':
            return "hubs cannot submit guesses"

        if guess not in self.tiles().keys():
            return "guess is not on the board"

        # self.stopTimer()
        
        self._board.flipTile(guess)

        # has this team won?
        winner = self._board.winner()
        if winner:
            # self.stopTimer()
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
            # self.stopTimer()
            self._game_state = GameState.WAITING_CLUE
            self._current_clue = ""
            self.switchTurns()

            # start timer
            # self._timer = Timer(interval=self._time_limit, function=self.timerTimeout)
            # if self._time_limit > 1.0:
            #     self._time_left = self._time_limit
            #     self._tick_timer = Timer(interval=1.0, function=self.tick)
            #     self._tick_timer.start()
            # self._timer.start()

    def switchTurns(self):
        if self._current_turn == 'blue':
            self._current_turn = 'orange'
        else:
            self._current_turn = 'blue'

    def tiles(self):
        return self._board.tiles()

    def currentClue(self):
        return self._current_clue

    def guessesLeft(self):
        return self._current_guess_count

    def winner(self):
        return self._winning_team

    def replayRequest(self, name: str):
        self._players[name][2]=True
        self.readyToRestart()
        return "request accepted"

    def filter_players(self, *, teams: list, role: str):
        players = list()
        for team in teams:
            players.extend([player for player, data in self._players.items() if data[0] == team and data[1] == role])
        return players

    def rosterUpdate(self):
        # do we have one hub for both teams?
        blue_hub = self.filter_players(teams=["blue"], role="hub")
        blue_no_hubs = self.filter_players(teams=["blue"], role="orbital")
        orange_hub = self.filter_players(teams=["orange"], role="hub")
        orange_no_hubs = self.filter_players(teams=["orange"], role="orbital")

        if (blue_hub and blue_no_hubs) and (orange_hub and orange_no_hubs):
            self._game_state = GameState.WAITING_START
        else:
            self._game_state = GameState.WAITING_PLAYERS

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