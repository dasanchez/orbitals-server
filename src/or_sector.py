"""
or_sector.py
Orbitals sector module
Tracks:
- teams
- players
- word list
- board
- turns
"""
import asyncio
import json
import or_comms as orbComms
from or_words import OrbitalsWords
from or_players import OrbitalsPlayers
from or_timer import OrbitalsTimer

class OrbitalsSector:
    """ Top level class """

    def __init__(self, wordCount, turnTimeout, name, symbol):
        self._gameInfo = {'state': 'waiting-players',
                          'hint': {'hintWord': '',
                                   'count': 0,
                                   'sender': '',
                                   'team': ''},
                          'turn': 'N',
                          'guesses': 0,
                          'winner': '',
                          'orange-hub': False,
                          'blue-hub': False,
                          'enough-players': False}
        self._users = set()
        self._gameWords = OrbitalsWords(wordCount)
        self._orbTimer = OrbitalsTimer(turnTimeout)
        self._players = OrbitalsPlayers()
        self._sectorName = name
        self._sectorSymbol = symbol


    async def newMessage(self, websocket, data):
        """ handles incoming message from players """
        if data['type'] == 'name-request':
            await self.newPlayer(data['name'], websocket)
        elif data['type'] == 'team-request':
            await self.teamRequest(websocket, data['team'])
        elif data['type'] == 'hub-request':
            await self.hubRequest(websocket)
        elif data['type'] == 'ready':
            await self.startRequest(websocket)
        elif data['type'] == 'message':
            await self.processMessage(websocket, data['message'])
        elif data['type'] == 'hint':
            await self.processHint(websocket, data['hint'], int(data['guesses']))
        elif data['type'] == 'hint-response':
            await self.processHintResponse(websocket, data['response'])
        elif data['type'] == 'guess':
            await self.processGuess(websocket, data['guess'])
        elif data['type'] == 'replay':
            await self.processReplayRequest(websocket)

    async def countdown(self):
        """ limits turns to a set amount of time """
        print("Starting countdown")
        while self._orbTimer.getTime() > 0:
            await asyncio.sleep(1)
            self._orbTimer.tick()
            await orbComms.publishTime(self._orbTimer.getTime(), self._players.getPlayers())
            if self._orbTimer.getTime() == 0 and self._orbTimer.isActive():
                # timeout!
                self._orbTimer.stop()
                self.timeout()
                await orbComms.publishState(self._gameInfo, players=self._players.getPlayers())
                print(
                    f"After the timeout, it's team {self._gameInfo['turn']}'s turn")
                state = self._gameInfo['state']
                if state == 'hint-submission' or state == 'guess-submission':
                    print("Restarting timer")
                    self._orbTimer.start()
        return True

    async def deleteConnection(self, websocket):
        """
        Handles a player leaving the game:
        If there aren't enough players left:
        - change state to 'waiting-players'
        - stop timer
        """
        self._users.remove(websocket)
        player = self._players.playerId(websocket)
       
        messageDict = {'msg': '[LEFT THE SECTOR]', 'msgSender': player.getName(),
                           'msgTeam': player.getTeam()}
        
        if not self._players.removePlayer(websocket):
            self._gameInfo['state'] = 'waiting-players'
            self._orbTimer.stop()

        self._gameInfo['blue-hub'] = self._players.haveBlueHub()
        self._gameInfo['orange-hub'] = self._players.haveOrangeHub()
        print(f"gameInfo: {self._gameInfo}")
        
        await orbComms.publishMessage(messageDict, self._players.getPlayers())
        await orbComms.publishPlayers(self._players.getPlayerData(),
                                      self._players.enoughPlayers(), self._users)
        await orbComms.publishState(self._gameInfo, self._players.getPlayers())

    async def newPlayer(self, name, websocket):
        """ tries to register a new player in sector """
        self._users.add(websocket)
        self._players.addPlayer(name, websocket)

        sectorPacket = {'type': 'response',
                        'msg': 'joined-sector',
                        'sector': self._sectorName}
        msg = json.dumps(sectorPacket)
        await websocket.send(msg)
        # issue state
        playerId = self._players.playerId(websocket)

        gameState = self._gameInfo['state']
        await orbComms.publishState(self._gameInfo, [playerId])

        player = self._players.playerId(websocket)
        await orbComms.publishPlayers(self._players.getPlayerData(),
                                      self._players.enoughPlayers(), self._users)
        messageDict = {'msg': '[JOINED THE SECTOR]', 'msgSender': player.getName(),
                       'msgTeam': player.getTeam()}
        await orbComms.publishMessage(messageDict, self._players.getPlayers())

        # has the game started  already?
        if (gameState == 'hint-submission' or gameState == 'hint-response'
           or gameState == 'guess-submission' or gameState == 'game-start'):
            # Send word info
            packet = {'type': 'words', 'words': self._gameWords.getWords()}
            msg = json.dumps(packet)
            await websocket.send(msg)        

        
    async def teamRequest(self, websocket, team):
        """ assigns player to requested team """
        player = self._players.playerId(websocket)
        current_state = self._gameInfo['state']

        if current_state == 'waiting-players' or current_state == 'waiting-start' or current_state == 'game-over':
            if player.getTeam() is not team:
                success, response = self._players.joinTeam(websocket, team)
                if success:
                    packet = {'type': 'response', 'msg': response, "team": team}
                    msg = json.dumps(packet)
                    await websocket.send(msg)
                    self._gameInfo['orange-hub'] = self._players.haveOrangeHub()
                    self._gameInfo['blue-hub'] = self._players.haveBlueHub()
                    if self._players.enoughPlayers():
                        if self._gameInfo['state'] == 'waiting-players':
                            self._gameInfo['state'] = 'waiting-start'
                    else:
                        self._gameInfo['state'] = 'waiting-players'
                    await orbComms.publishState(self._gameInfo, self._players.getPlayers())
                    await orbComms.publishPlayers(self._players.getPlayerData(),
                                                  self._players.enoughPlayers(), self._users)
                    teamString = 'N'
                    if player.getTeam() == 'O':
                        teamString = 'ORANGE'
                    elif player.getTeam() == 'B':
                        teamString = 'BLUE'
                    messageDict = {'msg': f'[JOINED TEAM {teamString}]', 'msgSender': player.getName(),
                                   'msgTeam': player.getTeam()}
                    await orbComms.publishMessage(messageDict, self._players.getPlayers())

                    if self._gameInfo['state'] == 'game-over':
                        self._players.requestReplay(websocket)

                else:
                    packet = {'type': 'response', 'msg': 'team-rejected', "reason": response}
                    msg = json.dumps(packet)
                    await websocket.send(msg)

    async def hubRequest(self, websocket):
        """
        tries to assign hub role to player
        """
        success, response = self._players.requestHub(websocket)
        team = self._players.playerId(websocket).getTeam()
        if success:
            player = self._players.playerId(websocket)
            packet = {'type': 'response', 'msg': response, 'team': team}
            msg = json.dumps(packet)
            await websocket.send(msg)
            self._gameInfo['orange-hub'] = self._players.haveOrangeHub()
            self._gameInfo['blue-hub'] = self._players.haveBlueHub()
            if self._players.enoughPlayers():
                if self._gameInfo['state'] == 'waiting-players':
                    self._gameInfo['state'] = 'waiting-start'
            else:
                self._gameInfo['state'] = 'waiting-players'
            await orbComms.publishPlayers(self._players.getPlayerData(),
                                          self._players.enoughPlayers(), self._users)
            await orbComms.publishState(self._gameInfo, self._players.getPlayers())
            messageDict = {'msg': f'[ROLE CHANGED]', 'msgSender': player.getName(),
                           'msgTeam': player.getTeam()}
            await orbComms.publishMessage(messageDict, self._players.getPlayers())
        else:
            packet = {'type': 'response', 'msg': 'hub-rejected', 'reason': response}
            msg = json.dumps(packet)
            await websocket.send(msg)

    async def startRequest(self, websocket):
        """
        sets the team to "ready" status
        """
        if self._players.requestStart(websocket):
            self._gameInfo['state'] = 'game-start'
            self.clearBoard()
            self.setupBoard()

        packet = {'type': 'response', 'msg': "start-accepted"}
        msg = json.dumps(packet)
        await websocket.send(msg)

        await orbComms.publishPlayers(self._players.getPlayerData(),
                                      self._players.enoughPlayers(), self._users)
        await orbComms.publishState(self._gameInfo, self._players.getPlayers())

        if self._gameInfo['state'] == 'game-start':
            await self.startNewGame()

    async def processHint(self, websocket, hint, count):
        """ hint is published and sent for aproval """
        # stop countdown
        self._orbTimer.stop()

        player = self._players.playerId(websocket)
        if player.getTeam() == self._gameInfo['turn'] and player.isHub():
            # Limit guess count to 4
            if count > 4:
                count = 4
            # Limit guess count to the amount of words left
            wordsLeft = self._gameWords.wordsLeft(self._gameInfo['turn'])
            if count > wordsLeft:
                count = wordsLeft

            self._gameInfo['guesses'] = count
            self._gameInfo['state'] = 'hint-response'
            self._gameInfo['hint']['hintWord'] = hint
            self._gameInfo['hint']['count'] = count
            self._gameInfo['hint']['sender'] = self._players.playerName(
                websocket)
            self._gameInfo['hint']['team'] = self._gameInfo['turn']

            print(f"Team {self._gameInfo['turn']} has submitted hint '{hint}',"
                  f" guesses: {count}.")
            await orbComms.publishState(self._gameInfo, self._players.getPlayers())
        else:
            name = player.getName()
            print(f"{name} is not allowed to submit hints at this point.")

    async def processHintResponse(self, websocket, response):
        """ process hint approval / rejection """
        # respond to hint:
        player = self._players.playerId(websocket)
        if player.getTeam() != self._gameInfo['turn'] and player.isHub():
            if response:
                self._gameInfo['state'] = 'guess-submission'
                print(f"Hint has been approved.")
            else:
                self._gameInfo['state'] = 'hint-submission'
                print(f"Hint has been rejected.")
                messageDict = {'msg': '[HINT REJECTED]', 'msgSender': player.getName(),
                               'msgTeam': player.getTeam()}
                await orbComms.publishMessage(messageDict, self._players.getPlayers())

            await orbComms.publishState(self._gameInfo, self._players.getPlayers())
            # restart timer
            self._orbTimer.start()
            loop = asyncio.get_event_loop()
            loop.create_task(self.countdown())

        else:
            name = self._players.playerName(websocket)
            print(f"{name} is not allowed to respond to hints at this point.")

    async def processGuess(self, websocket, guess):
        """ publishes guess from non-hub players """
        # need to check that the right team is submitting guesses!
        player = self._players.playerId(websocket)
        currentTurn = self._gameInfo['turn']
        # is the guesser in the right team and not a hub?
        if player.getTeam() == currentTurn and not player.isHub():
            # update words
            response = self._gameWords.newGuess(guess, currentTurn)
            print(response)
        # TODO: response for people submitting guesses when they shouldn't
        else:
            return

        # has this word been guessed before?
        if response["newGuess"]:
            # game over?
            if response["gameOver"]:
                print(f"{response['winner']} team wins.")
                self._gameInfo['guesses'] = 0
                self._gameInfo['winner'] = response["winner"]
                self._gameInfo['state'] = 'game-over'

            else:
                self._gameInfo['guesses'] -= 1
                if response["switch"]:
                    self._gameInfo['guesses'] = 0

                if not self._gameInfo['guesses']:
                    print("Switching teams")
                    self._gameInfo['state'] = 'hint-submission'
                    self.switchTurns()

            guessDict = {'word': guess,
                         'wordTeam': self._gameWords.getTeam(guess),
                         'guesser': player.getName(),
                         'guesserTeam': player.getTeam(),
                         'guessesLeft': self._gameInfo['guesses']}
            print(f"Guesses left: {self._gameInfo['guesses']}")
            await orbComms.publishGuess(guessDict, self._players.getPlayers())

            if self._gameInfo['guesses'] == 0:
                self._orbTimer.stop()
                await orbComms.publishState(self._gameInfo, self._players.getPlayers())
                await asyncio.sleep(1)
            if self._gameInfo['state'] == 'hint-submission':
                # restart timer
                self._orbTimer.start()
                loop = asyncio.get_event_loop()
                loop.create_task(self.countdown())

    async def processMessage(self, websocket, message):
        """
        Handles requests to publish messages
        if the state is 'game-over':
        - all players can send messages
        if the state is not 'game-over':
        - only non-hub players can send messages
        """
        player = self._players.playerId(websocket)
        state = self._gameInfo['state']
        if player:
            if not player.isHub() or state == 'waiting-players' or state == 'waiting-start' or state == 'game-over':
                messageDict = {'msg': message, 'msgSender': player.getName(),
                               'msgTeam': player.getTeam()}
                await orbComms.publishMessage(messageDict, self._players.getPlayers())

    async def processReplayRequest(self, websocket):
        """ captures all players' signal to start another game """

        packet = {'type': 'replay-ack'}
        msg = json.dumps(packet)
        await websocket.send(msg)
        if self._players.requestReplay(websocket):
            self._gameInfo['state'] = 'waiting-start'
            await orbComms.publishState(self._gameInfo, self._players.getPlayers())

    async def startNewGame(self):
        """ publishes words and starts the counter for the first turn """
        await orbComms.publishWords(self._gameWords.getWords(),
                                    self._gameWords.getKeywords(),
                                    self._players.getPlayers())
        self._orbTimer.start(5)
        loop = asyncio.get_event_loop()
        loop.create_task(self.countdown())
        print(f"{self._gameInfo['turn']} team goes first")

    def clearBoard(self):
        """
        Reset game status:
        - new words are read
        - turn is set to none
        - hint is cleared
        - words remaining by either team are cleared
        - guesses left are cleared
        """
        self._gameInfo['hint']['hintWord'] = ''
        self._gameInfo['hint']['count'] = 0
        self._gameInfo['hint']['sender'] = ''
        self._gameInfo['hint']['team'] = ''
        self._gameInfo['turn'] = ''
        self._gameInfo['guesses'] = 0
        self._gameInfo['winner'] = ''
        self._gameWords.reset()

    def switchTurns(self):
        """ Toggles _currentTurn between teams """
        if self._gameInfo['turn'] == 'B':
            self._gameInfo['turn'] = 'O'
        else:
            self._gameInfo['turn'] = 'B'

    def timeout(self):
        """ Changes states after the time runs out """
        if self._gameInfo['state'] == 'game-start':
            self._gameInfo['state'] = 'hint-submission'
        elif self._gameInfo['state'] == 'hint-submission':
            self.switchTurns()
        elif self._gameInfo['state'] == 'guess-submission':
            self._gameInfo['state'] = 'hint-submission'
            self.switchTurns()

    def setupBoard(self):
        """ Shuffles the deck and assigns keywords """
        self._gameWords.shuffleDeck()
        self._gameWords.assignKeys()
        self._gameInfo['turn'] = self._gameWords.getFirstTurn()

    def startSimulation(self):
        """ Utility function for development """
        self._gameWords.setSimulationWords()
        self._gameInfo['turn'] = 'O'

    def getSectorDetails(self):
        # return player count for both teams and sector name
        sectorDetails = dict()
        
        # populate sector dictionary
        sectorDetails['name'] = self._sectorName
        sectorDetails['symbol'] = self._sectorSymbol
        sectorDetails['orangeHub'] = self._players.haveOrangeHub()
        sectorDetails['blueHub'] = self._players.haveBlueHub()
        orangeOrbitals = self._players.getOrangeTeamCount()
        blueOrbitals = self._players.getBlueTeamCount()
        if sectorDetails['orangeHub']:
            orangeOrbitals -= 1
        if sectorDetails['blueHub']:
            blueOrbitals -= 1
        sectorDetails['orangeOrbitals'] = orangeOrbitals
        sectorDetails['blueOrbitals'] = blueOrbitals
        if (self._players.getBlueTeamCount() + self._players.getOrangeTeamCount()) < 8:
            sectorDetails['open'] = True
        else:
            sectorDetails['open'] = False
        return sectorDetails