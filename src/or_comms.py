"""
or_comms.py
Utility functions for Orbitals communications
"""
import asyncio
import json


async def publishState(gameInfo, players):
    """
    publishes the game state and current turn to all players:
    - adds the hint and remaining guesses if state is 'waiting guess'
    - adds the winner if the state is 'game-over'
    - sends a customized set of data to each player:
        - prompt
        - show hint or not
        - hint info
        - name request
        - team request
        - role request
        - start request
    """
    packet = {}
    state = gameInfo['state']
    turn = gameInfo['turn']
    packet['type'] = 'state'
    packet['state'] = state
    packet['showTurn'] = False
    packet['turn'] = turn
    packet['entry'] = 'view-only'

    # send a custom state array to all connected players
    for player in players:
        packet['name'] = player.getName()
        packet['showHint'] = False
        packet['updateComms'] = False
        packet['enableGuesses'] = False
        if state == 'waiting-players':
            # If we are waiting for players:
            # - everyone should have a name by now
            # - asking for a team should be the default
            # - if the player has a team and that team doesn't have a hub,
            #   allow them to request the hub role
            packet['entry'] = 'team-selection'
            packet['prompt'] = 'Waiting for players'
            if player.isHub():
                packet['entry'] = 'role-selection'
                packet['hub'] = True
            else:
                packet['hub'] = False
                # print(f"gameInfo: {gameInfo}")
                if player.getTeam() == 'B' and not gameInfo['blue-hub']:
                    packet['entry'] = 'role-selection'
                if player.getTeam() == 'O' and not gameInfo['orange-hub']:
                    packet['entry'] = 'role-selection'

        elif state == 'waiting-start':
            packet['entry'] = 'team-selection'
            packet['prompt'] = 'Waiting for game start'
            if player.isHub():
                packet['entry'] = 'ready-area'
                packet['ready'] = player.isReady()
        elif state == 'game-start':
            packet['prompt'] = 'Study the words'
            packet['showTurn'] = True
            if player.isHub():
                packet['updateComms'] = True
                packet['comms'] = ''
        elif state == 'hint-submission':
            packet['showTurn'] = True
            packet['prompt'] = 'Waiting for hint'
            if player.isHub():
                packet['updateComms'] = True
                packet['comms'] = ''
                if player.getTeam() == turn:
                    packet['prompt'] = 'Submit a hint'
                    packet['comms'] = 'hint-submission'
        elif state == 'hint-response':
            packet['showTurn'] = True
            packet['prompt'] = 'Waiting for hint response'
            if player.isHub():
                packet['updateComms'] = True
                packet['comms'] = ''
                if player.getTeam() != turn:
                    packet['prompt'] = 'Respond to hint'
                    packet['showHint'] = True
                    packet['hint'] = gameInfo['hint']['hintWord']
                    packet['guesses'] = gameInfo['guesses']
                    packet['comms'] = 'hint-response'
        elif state == 'guess-submission':
            packet['showTurn'] = True
            packet['prompt'] = 'Waiting for guesses'
            packet['showHint'] = True
            packet['hint'] = gameInfo['hint']['hintWord']
            packet['guesses'] = gameInfo['guesses']
            if player.getTeam() == turn and not player.isHub():
                packet['prompt'] = 'Guess a related word'
                packet['enableGuesses'] = True
            if player.isHub():
                packet['updateComms'] = True
                packet['comms'] = ''
        elif state == 'game-over':
            if gameInfo['winner'] == 'O':
                winner = 'Orange'
            elif gameInfo['winner'] == 'B':
                winner = 'Blue'
            packet['prompt'] = 'Team ' + winner + ' wins!'
            if player.getTeam() == 'B' or player.getTeam() == 'O':
                if not player.wantsReplay():
                    packet['updateComms'] = True
                    packet['comms'] = 'replay'
                else:
                    packet['updateComms'] = True
                    packet['comms'] = 'message'
            else:
                packet['entry'] = 'team-selection'

        # print(f"Packet: {packet}")
        msg = json.dumps(packet)
        await player.getWebSocket().send(msg)

async def publishPlayers(playerData, enough, users):
    """
    sends the list of players (name, team, role, and readiness)
    to everyone (not just players)
    """
    # build playerData dict
    if users:
        packet = {'type': 'players', 'players': playerData,
                  'enough': enough}
        msg = json.dumps(packet)
        # print(f"Sending message: {str(packet)}")
        await asyncio.wait([user.send(msg) for user in users])


async def publishTime(seconds, players):
    """ sends remaining time in turn to all players """
    packet = {'type': 'time', 'time': seconds}
    msg = json.dumps(packet)
    for player in players:
        await player.getWebSocket().send(msg)


async def publishWords(words, keywords, players):
    """ publish all public words to all players """
    # print(f"Words: {str(words)}")
    # print(f"Key: {str(keywords)}")
    packet = {'type': 'words', 'words': words}
    keyPacket = {'type': 'keys', 'keywords': keywords}
    msg = json.dumps(packet)
    keyMsg = json.dumps(keyPacket)
    for player in players:
        await player.getWebSocket().send(msg)
        if player.isHub():
            await player.getWebSocket().send(keyMsg)

async def publishGuess(guess, players):
    """
    publish a single word, its sender, its team, to all players
    """
    word = guess['word']
    wordTeam = guess['wordTeam']
    guesser = guess['guesser']
    guesserTeam = guess['guesserTeam']

    # print(f"Guessed word: {word}, wordTeam: {wordTeam}, "
    #       f"guesser: {guesser}, guesserTeam: {guesserTeam}")
    packet = {'type': 'guess', 'word': word, 'wordTeam': wordTeam,
              'guesser': guesser, 'guesserTeam': guesserTeam,
              'guesses': int(guess['guessesLeft'])}
    msg = json.dumps(packet)
    for player in players:
        await player.getWebSocket().send(msg)

async def publishMessage(message, players):
    """ publishes chat message from non-hub player """
    packet = {'type': 'msg', 'sender': message['msgSender'],
              'team': message['msgTeam'], 'msg': message['msg']}
    msg = json.dumps(packet)
    for player in players:
        await player.getWebSocket().send(msg)
