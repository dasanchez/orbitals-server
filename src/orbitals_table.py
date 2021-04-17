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
    WAITING_START = 1
    WAITING_CLUE = auto()
    WAITING_GUESS = auto()
    GAME_OVER = auto


class OrbitalsTable:
    """ Top level class """

    def __init__(self, words_source=None, player_limit: int=16):
        self._players = dict()
        self._player_limit = player_limit
        self._start_game = {"blue": False, "orange": False}
        self._game_state = GameState.WAITING_START
        self._board = OrbitalsBoard(word_bag=words_source)
        self._current_turn = ''
        self._current_clue = ''
        self._current_guess_count = 0
        self._winning_team = ''

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
        # status["blue_tiles_guessed"] = 
        # status["blue_tiles_left"] = 
        # status["orange_tiles_guessed"] = 
        # status["orange_tiles_left"] =
        # status["neutral_tiles_guessed"] = 
        # status["neutral_tiles_left"] = 
        return status

    def state(self):
        return self._game_state, self._current_turn

    def newPlayer(self, name: str):
        if self._player_limit > len(self._players):
            self._players[name] = ["no-team", "no-hub", False]
            return True
        else:
            return False

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

    def players(self):
        return self._players

    def startRequest(self, name: str):
        if self.playerRole(name) == 'hub':
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
        if self._players[name][0] == self._current_turn and \
            self._players[name][1] == 'hub':
            self._current_clue = clue
            self._current_guess_count = guess_count
            self._game_state = GameState.WAITING_GUESS

    def newGuess(self, name: str, guess: str):
        if self._players[name][0] == self._current_turn and \
        self._players[name][1] == 'no-hub':
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

        # self._gameInfo = {'state': 'waiting-players',
        #                   'hint': {'hintWord': '',
        #                            'count': 0,
        #                            'sender': '',
        #                            'team': ''},
        #                   'turn': 'N',
        #                   'guesses': 0,
        #                   'winner': '',
        #                   'orange-hub': False,
        #                   'blue-hub': False,
        #                   'enough-players': False}
        # self._users = set()
        # self._gameWords = OrbitalsWords(wordCount)
        # self._orbTimer = OrbitalsTimer(turnTimeout)
        # self._players = OrbitalsPlayers()
        # self._sectorName = name
        # self._sectorSymbol = symbol
        # self._playerNames = set()


    # async def newMessage(self, websocket, data):
    #     """ handles incoming message from players """
    #     if data['type'] == 'name-request':
    #         await self.newPlayer(data['name'], websocket)
    #     elif data['type'] == 'team-request':
    #         await self.teamRequest(websocket, data['team'])
    #     elif data['type'] == 'hub-request':
    #         await self.hubRequest(websocket)
    #     elif data['type'] == 'ready':
    #         await self.startRequest(websocket)
    #     elif data['type'] == 'message':
    #         await self.processMessage(websocket, data['message'])
    #     elif data['type'] == 'hint':
    #         await self.processHint(websocket, data['hint'], int(data['guesses']))
    #     elif data['type'] == 'hint-response':
    #         await self.processHintResponse(websocket, data['response'])
    #     elif data['type'] == 'guess':
    #         await self.processGuess(websocket, data['guess'])
    #     elif data['type'] == 'replay':
    #         await self.processReplayRequest(websocket)

    # async def countdown(self):
    #     """ limits turns to a set amount of time """
    #     print("Starting countdown")
    #     while self._orbTimer.getTime() > 0:
    #         await asyncio.sleep(1)
    #         self._orbTimer.tick()
    #         await orbComms.publishTime(self._orbTimer.getTime(), self._players.getPlayers())
    #         if self._orbTimer.getTime() == 0 and self._orbTimer.isActive():
    #             # timeout!
    #             self._orbTimer.stop()
    #             self.timeout()
    #             await orbComms.publishState(self._gameInfo, players=self._players.getPlayers())
    #             print(
    #                 f"After the timeout, it's team {self._gameInfo['turn']}'s turn")
    #             state = self._gameInfo['state']
    #             if state == 'hint-submission' or state == 'guess-submission':
    #                 print("Restarting timer")
    #                 self._orbTimer.start()
    #     return True

    # async def deleteConnection(self, websocket):
    #     """
    #     Handles a player leaving the game:
    #     If there aren't enough players left:
    #     - change state to 'waiting-players'
    #     - stop timer
    #     """
    #     self._users.remove(websocket)
    #     player = self._players.playerId(websocket)
       
    #     messageDict = {'msg': '[LEFT THE SECTOR]', 'msgSender': player.getName(),
    #                        'msgTeam': player.getTeam()}
        
    #     if not self._players.removePlayer(websocket):
    #         self._gameInfo['state'] = 'waiting-players'
    #         self._orbTimer.stop()

    #     self._gameInfo['blue-hub'] = self._players.haveBlueHub()
    #     self._gameInfo['orange-hub'] = self._players.haveOrangeHub()
    #     print(f"gameInfo: {self._gameInfo}")
        
    #     await orbComms.publishMessage(messageDict, self._players.getPlayers())
    #     await orbComms.publishPlayers(self._players.getPlayerData(),
    #                                   self._players.enoughPlayers(), self._users)
    #     await orbComms.publishState(self._gameInfo, self._players.getPlayers())

    # def newPlayerName(self, name):
    #     if name not in self._playerNames:
    #         self._playerNames.add(name)
    #         sectorPacket = {'type': 'response',
    #             'msg': 'joined-sector',
    #             'sector': self._sectorName}
    #         return sectorPacket

    # async def newPlayer(self, name, websocket):
    #     """ tries to register a new player in sector """
    #     self._users.add(websocket)
    #     self._players.addPlayer(name, websocket)

    #     sectorPacket = {'type': 'response',
    #                     'msg': 'joined-sector',
    #                     'sector': self._sectorName}
    #     msg = json.dumps(sectorPacket)
    #     await websocket.send(msg)
    #     # issue state
    #     playerId = self._players.playerId(websocket)

    #     gameState = self._gameInfo['state']
    #     await orbComms.publishState(self._gameInfo, [playerId])

    #     player = self._players.playerId(websocket)
    #     await orbComms.publishPlayers(self._players.getPlayerData(),
    #                                   self._players.enoughPlayers(), self._users)
    #     messageDict = {'msg': '[JOINED THE SECTOR]', 'msgSender': player.getName(),
    #                    'msgTeam': player.getTeam()}
    #     await orbComms.publishMessage(messageDict, self._players.getPlayers())

    #     # has the game started  already?
    #     if (gameState == 'hint-submission' or gameState == 'hint-response'
    #        or gameState == 'guess-submission' or gameState == 'game-start'):
    #         # Send word info
    #         packet = {'type': 'words', 'words': self._gameWords.getWords()}
    #         msg = json.dumps(packet)
    #         await websocket.send(msg)        

        
    # async def teamRequest(self, websocket, team):
    #     """ assigns player to requested team """
    #     player = self._players.playerId(websocket)
    #     current_state = self._gameInfo['state']

    #     if current_state == 'waiting-players' or current_state == 'waiting-start' or current_state == 'game-over':
    #         if player.getTeam() is not team:
    #             success, response = self._players.joinTeam(websocket, team)
    #             if success:
    #                 packet = {'type': 'response', 'msg': response, "team": team}
    #                 msg = json.dumps(packet)
    #                 await websocket.send(msg)
    #                 self._gameInfo['orange-hub'] = self._players.haveOrangeHub()
    #                 self._gameInfo['blue-hub'] = self._players.haveBlueHub()
    #                 if self._players.enoughPlayers():
    #                     if self._gameInfo['state'] == 'waiting-players':
    #                         self._gameInfo['state'] = 'waiting-start'
    #                 else:
    #                     self._gameInfo['state'] = 'waiting-players'
    #                 await orbComms.publishState(self._gameInfo, self._players.getPlayers())
    #                 await orbComms.publishPlayers(self._players.getPlayerData(),
    #                                               self._players.enoughPlayers(), self._users)
    #                 teamString = 'N'
    #                 if player.getTeam() == 'O':
    #                     teamString = 'ORANGE'
    #                 elif player.getTeam() == 'B':
    #                     teamString = 'BLUE'
    #                 messageDict = {'msg': f'[JOINED TEAM {teamString}]', 'msgSender': player.getName(),
    #                                'msgTeam': player.getTeam()}
    #                 await orbComms.publishMessage(messageDict, self._players.getPlayers())

    #                 if self._gameInfo['state'] == 'game-over':
    #                     self._players.requestReplay(websocket)

    #             else:
    #                 packet = {'type': 'response', 'msg': 'team-rejected', "reason": response}
    #                 msg = json.dumps(packet)
    #                 await websocket.send(msg)

    # async def hubRequest(self, websocket):
    #     """
    #     tries to assign hub role to player
    #     """
    #     success, response = self._players.requestHub(websocket)
    #     team = self._players.playerId(websocket).getTeam()
    #     if success:
    #         player = self._players.playerId(websocket)
    #         packet = {'type': 'response', 'msg': response, 'team': team}
    #         msg = json.dumps(packet)
    #         await websocket.send(msg)
    #         self._gameInfo['orange-hub'] = self._players.haveOrangeHub()
    #         self._gameInfo['blue-hub'] = self._players.haveBlueHub()
    #         if self._players.enoughPlayers():
    #             if self._gameInfo['state'] == 'waiting-players':
    #                 self._gameInfo['state'] = 'waiting-start'
    #         else:
    #             self._gameInfo['state'] = 'waiting-players'
    #         await orbComms.publishPlayers(self._players.getPlayerData(),
    #                                       self._players.enoughPlayers(), self._users)
    #         await orbComms.publishState(self._gameInfo, self._players.getPlayers())
    #         messageDict = {'msg': f'[ROLE CHANGED]', 'msgSender': player.getName(),
    #                        'msgTeam': player.getTeam()}
    #         await orbComms.publishMessage(messageDict, self._players.getPlayers())
    #     else:
    #         packet = {'type': 'response', 'msg': 'hub-rejected', 'reason': response}
    #         msg = json.dumps(packet)
    #         await websocket.send(msg)

    # async def startRequest(self, websocket):
    #     """
    #     sets the team to "ready" status
    #     """
    #     if self._players.requestStart(websocket):
    #         self._gameInfo['state'] = 'game-start'
    #         self.clearBoard()
    #         self.setupBoard()

    #     packet = {'type': 'response', 'msg': "start-accepted"}
    #     msg = json.dumps(packet)
    #     await websocket.send(msg)

    #     await orbComms.publishPlayers(self._players.getPlayerData(),
    #                                   self._players.enoughPlayers(), self._users)
    #     await orbComms.publishState(self._gameInfo, self._players.getPlayers())

    #     if self._gameInfo['state'] == 'game-start':
    #         await self.startNewGame()

    # async def processHint(self, websocket, hint, count):
    #     """ hint is published and sent for aproval """
    #     # stop countdown
    #     self._orbTimer.stop()

    #     player = self._players.playerId(websocket)
    #     if player.getTeam() == self._gameInfo['turn'] and player.isHub():
    #         # Limit guess count to 4
    #         if count > 4:
    #             count = 4
    #         # Limit guess count to the amount of words left
    #         wordsLeft = self._gameWords.wordsLeft(self._gameInfo['turn'])
    #         if count > wordsLeft:
    #             count = wordsLeft

    #         self._gameInfo['guesses'] = count
    #         self._gameInfo['state'] = 'hint-response'
    #         self._gameInfo['hint']['hintWord'] = hint
    #         self._gameInfo['hint']['count'] = count
    #         self._gameInfo['hint']['sender'] = self._players.playerName(
    #             websocket)
    #         self._gameInfo['hint']['team'] = self._gameInfo['turn']

    #         print(f"Team {self._gameInfo['turn']} has submitted hint '{hint}',"
    #               f" guesses: {count}.")
    #         await orbComms.publishState(self._gameInfo, self._players.getPlayers())
    #     else:
    #         name = player.getName()
    #         print(f"{name} is not allowed to submit hints at this point.")

    # async def processHintResponse(self, websocket, response):
    #     """ process hint approval / rejection """
    #     # respond to hint:
    #     player = self._players.playerId(websocket)
    #     if player.getTeam() != self._gameInfo['turn'] and player.isHub():
    #         if response:
    #             self._gameInfo['state'] = 'guess-submission'
    #             print(f"Hint has been approved.")
    #         else:
    #             self._gameInfo['state'] = 'hint-submission'
    #             print(f"Hint has been rejected.")
    #             messageDict = {'msg': '[HINT REJECTED]', 'msgSender': player.getName(),
    #                            'msgTeam': player.getTeam()}
    #             await orbComms.publishMessage(messageDict, self._players.getPlayers())

    #         await orbComms.publishState(self._gameInfo, self._players.getPlayers())
    #         # restart timer
    #         self._orbTimer.start()
    #         loop = asyncio.get_event_loop()
    #         loop.create_task(self.countdown())

    #     else:
    #         name = self._players.playerName(websocket)
    #         print(f"{name} is not allowed to respond to hints at this point.")

    # async def processGuess(self, websocket, guess):
    #     """ publishes guess from non-hub players """
    #     # need to check that the right team is submitting guesses!
    #     player = self._players.playerId(websocket)
    #     currentTurn = self._gameInfo['turn']
    #     # is the guesser in the right team and not a hub?
    #     if player.getTeam() == currentTurn and not player.isHub():
    #         # update words
    #         response = self._gameWords.newGuess(guess, currentTurn)
    #         print(response)
    #     # TODO: response for people submitting guesses when they shouldn't
    #     else:
    #         return

    #     # has this word been guessed before?
    #     if response["newGuess"]:
    #         # game over?
    #         if response["gameOver"]:
    #             print(f"{response['winner']} team wins.")
    #             self._gameInfo['guesses'] = 0
    #             self._gameInfo['winner'] = response["winner"]
    #             self._gameInfo['state'] = 'game-over'

    #         else:
    #             self._gameInfo['guesses'] -= 1
    #             if response["switch"]:
    #                 self._gameInfo['guesses'] = 0

    #             if not self._gameInfo['guesses']:
    #                 print("Switching teams")
    #                 self._gameInfo['state'] = 'hint-submission'
    #                 self.switchTurns()

    #         guessDict = {'word': guess,
    #                      'wordTeam': self._gameWords.getTeam(guess),
    #                      'guesser': player.getName(),
    #                      'guesserTeam': player.getTeam(),
    #                      'guessesLeft': self._gameInfo['guesses']}
    #         print(f"Guesses left: {self._gameInfo['guesses']}")
    #         await orbComms.publishGuess(guessDict, self._players.getPlayers())

    #         if self._gameInfo['guesses'] == 0:
    #             self._orbTimer.stop()
    #             await orbComms.publishState(self._gameInfo, self._players.getPlayers())
    #             await asyncio.sleep(1)
    #         if self._gameInfo['state'] == 'hint-submission':
    #             # restart timer
    #             self._orbTimer.start()
    #             loop = asyncio.get_event_loop()
    #             loop.create_task(self.countdown())

    # async def processMessage(self, websocket, message):
    #     """
    #     Handles requests to publish messages
    #     if the state is 'game-over':
    #     - all players can send messages
    #     if the state is not 'game-over':
    #     - only non-hub players can send messages
    #     """
    #     player = self._players.playerId(websocket)
    #     state = self._gameInfo['state']
    #     if player:
    #         if not player.isHub() or state == 'waiting-players' or state == 'waiting-start' or state == 'game-over':
    #             messageDict = {'msg': message, 'msgSender': player.getName(),
    #                            'msgTeam': player.getTeam()}
    #             await orbComms.publishMessage(messageDict, self._players.getPlayers())

    # async def processReplayRequest(self, websocket):
    #     """ captures all players' signal to start another game """

    #     packet = {'type': 'replay-ack'}
    #     msg = json.dumps(packet)
    #     await websocket.send(msg)
    #     if self._players.requestReplay(websocket):
    #         self._gameInfo['state'] = 'waiting-start'
    #         await orbComms.publishState(self._gameInfo, self._players.getPlayers())

    # async def startNewGame(self):
    #     """ publishes words and starts the counter for the first turn """
    #     await orbComms.publishWords(self._gameWords.getWords(),
    #                                 self._gameWords.getKeywords(),
    #                                 self._players.getPlayers())
    #     self._orbTimer.start(5)
    #     loop = asyncio.get_event_loop()
    #     loop.create_task(self.countdown())
    #     print(f"{self._gameInfo['turn']} team goes first")

    # def clearBoard(self):
    #     """
    #     Reset game status:
    #     - new words are read
    #     - turn is set to none
    #     - hint is cleared
    #     - words remaining by either team are cleared
    #     - guesses left are cleared
    #     """
    #     self._gameInfo['hint']['hintWord'] = ''
    #     self._gameInfo['hint']['count'] = 0
    #     self._gameInfo['hint']['sender'] = ''
    #     self._gameInfo['hint']['team'] = ''
    #     self._gameInfo['turn'] = ''
    #     self._gameInfo['guesses'] = 0
    #     self._gameInfo['winner'] = ''
    #     self._gameWords.reset()

    # def switchTurns(self):
    #     """ Toggles _currentTurn between teams """
    #     if self._gameInfo['turn'] == 'B':
    #         self._gameInfo['turn'] = 'O'
    #     else:
    #         self._gameInfo['turn'] = 'B'

    # def timeout(self):
    #     """ Changes states after the time runs out """
    #     if self._gameInfo['state'] == 'game-start':
    #         self._gameInfo['state'] = 'hint-submission'
    #     elif self._gameInfo['state'] == 'hint-submission':
    #         self.switchTurns()
    #     elif self._gameInfo['state'] == 'guess-submission':
    #         self._gameInfo['state'] = 'hint-submission'
    #         self.switchTurns()

    # def setupBoard(self):
    #     """ Shuffles the deck and assigns keywords """
    #     self._gameWords.shuffleDeck()
    #     self._gameWords.assignKeys()
    #     self._gameInfo['turn'] = self._gameWords.getFirstTurn()

    # def startSimulation(self):
    #     """ Utility function for development """
    #     self._gameWords.setSimulationWords()
    #     self._gameInfo['turn'] = 'O'

    # def getSectorDetails(self):
    #     # return player count for both teams and sector name
    #     sectorDetails = dict()
        
    #     # populate sector dictionary
    #     sectorDetails['name'] = self._sectorName
    #     sectorDetails['symbol'] = self._sectorSymbol
    #     sectorDetails['orangeHub'] = self._players.haveOrangeHub()
    #     sectorDetails['blueHub'] = self._players.haveBlueHub()
    #     orangeOrbitals = self._players.getOrangeTeamCount()
    #     blueOrbitals = self._players.getBlueTeamCount()
    #     if sectorDetails['orangeHub']:
    #         orangeOrbitals -= 1
    #     if sectorDetails['blueHub']:
    #         blueOrbitals -= 1
    #     sectorDetails['orangeOrbitals'] = orangeOrbitals
    #     sectorDetails['blueOrbitals'] = blueOrbitals
    #     if (self._players.getBlueTeamCount() + self._players.getOrangeTeamCount()) < 8:
    #         sectorDetails['open'] = True
    #     else:
    #         sectorDetails['open'] = False
    #     return sectorDetails