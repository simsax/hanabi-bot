#!/usr/bin/env python3
from copy import deepcopy
from sys import argv, stdout
from threading import Thread, Condition
import GameData
import socket
from constants import *
import os
from rule_based import rule_based_IA, MyCard

# python client.py 127.0.0.1 1024 Hal1 > 'p1.txt'
# python client.py 127.0.0.1 1024 Hal2 > 'p2.txt'
# python client.py 127.0.0.1 1024 Hal3 > 'p3.txt'
# python client.py 127.0.0.1 1024 Hal4 > 'p4.txt'
# python client.py 127.0.0.1 1024 Hal5 > 'p5.txt'

# Avg score over 1000 matches
# 2 players: 19.34
# 3 players: 19.65
# 4 players: 19.23
# 5 players: 18.48

INFINITE_PLAY = False

players = list()
current_player_index = 0

# used for measuring avg score
scores = list()

showed = False
started = False
len_hand = 0
last_player = None
last_card_played = None

if len(argv) < 4:
    print("You need the player name to start the game.")
    #exit(-1)
    playerName = "Test2" # For debug
    ip = HOST
    port = PORT
else:
    playerName = argv[3]
    ip = argv[1]
    port = int(argv[2])

run = True

statuses = ["Lobby", "Game", "GameHint", "Showed"]

game_state = None

status = statuses[0]

players_hints = dict()
finesse_dict = {'finesse':False, 'b_index':None, 'c_index':None, 'pos':None}

def decide(cv):
    global status
    global showed # to avoid repeating the same move multiple times while waiting for a server response
    global finesse_dict

    if status == statuses[0]:
        return 'ready'
    elif status == statuses[1]:
        cv.acquire()
        while (not started or players[current_player_index] != playerName or showed) and run:
            cv.wait()
        status = statuses[3]
        cv.release()
        return 'show'

    elif status == statuses[3]: # game state retrieved
        cv.acquire()
        while not showed:
            cv.wait()
        status = statuses[1]
        cv.release()

        action = rule_based_IA(game_state, len_hand, players_hints, players, current_player_index, finesse_dict, last_player, last_card_played)

        # reset recent hints after a play
        for i in range(len(players_hints[playerName])):
            players_hints[playerName][i].recent = False

        # reset finesse dict after completing a finesse
        if finesse_dict['finesse']:
            finesse_dict = {'finesse':False, 'b_index':None, 'c_index':None, 'pos':None}

        return action


def manageInput(cv):
    global run
    global status
    while run:
        command = decide(cv)
        if run:
            # Choose data to send
            if command == "exit":
                run = False
                os._exit(0)
            elif command == "ready" and status == statuses[0]:
                s.send(GameData.ClientPlayerStartRequest(playerName).serialize())
                status = statuses[1]
            elif command == "show":
                s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
            elif command.split(" ")[0] == "discard":
                try:
                    cardStr = command.split(" ")
                    cardOrder = int(cardStr[1])
                    s.send(GameData.ClientPlayerDiscardCardRequest(playerName, cardOrder).serialize())
                except:
                    print("Maybe you wanted to type 'discard <num>'?")
                    continue
            elif command.split(" ")[0] == "play":
                try:
                    cardStr = command.split(" ")
                    cardOrder = int(cardStr[1])
                    s.send(GameData.ClientPlayerPlayCardRequest(playerName, cardOrder).serialize())
                except:
                    print("Maybe you wanted to type 'play <num>'?")
                    continue
            elif command.split(" ")[0] == "hint":
                try:
                    destination = command.split(" ")[2]
                    t = command.split(" ")[1].lower()
                    if t != "colour" and t != "color" and t != "value":
                        print("Error: type can be 'color' or 'value'")
                        continue
                    value = command.split(" ")[3].lower()
                    if t == "value":
                        value = int(value)
                        if int(value) > 5 or int(value) < 1:
                            print("Error: card values can range from 1 to 5")
                            continue
                    else:
                        if value not in ["green", "red", "blue", "yellow", "white"]:
                            print("Error: card color can only be green, red, blue, yellow or white")
                            continue
                    s.send(GameData.ClientHintData(playerName, destination, t, value).serialize())
                except:
                    print("Maybe you wanted to type 'hint <type> <destinatary> <value>'?")
                    continue
            elif command == "":
                print("[" + playerName + " - " + status + "]: ", end="")
            else:
                print("Unknown command: " + command)
                continue
            stdout.flush()

def my_toClientString():
        c = "[ \n\t"
        for card in players_hints[playerName]:
            c += "\t" + "Card " + str(card.value) + " - " + str(card.color) + " - " + str(card.recent) + " - " + str(card.save) + " \n\t"
        c += " ]"
        return ("Player " + playerName + " { \n\tcards: " + c + "\n}")

def print_state(data):
    print("Current player: " + data.currentPlayer)
    print("Player hands: ")
    for p in data.players:
        if p.name == playerName:
            print(my_toClientString())
        else:
            print(p.toClientString())
    print("Cards in your hand: " + str(data.handSize))
    print("Table cards: ")
    for pos in data.tableCards:
        print(pos + ": [ ")
        for c in data.tableCards[pos]:
            print(c.toClientString() + " ")
        print("]")
    print("Discard pile: ")
    for c in data.discardPile:
        print("\t" + c.toClientString())            
    print("Note tokens used: " + str(data.usedNoteTokens) + "/8")
    print("Storm tokens used: " + str(data.usedStormTokens) + "/3")

def in_chop_zone(hint_cards, pos):
    chop_index = -1
    for i in range(len(hint_cards)):
        if hint_cards[i].value is None and hint_cards[i].color is None:
            chop_index = i
            break
    if chop_index != -1 and chop_index == pos:
        return True
    else:
        return False

def set_ptable(players_hints, game_state):
    for card in players_hints[playerName]:
        card.reset_ptable()
        for discard in game_state.discardPile:
            if discard.value in card.ptable[discard.color]:
                card.ptable[discard.color].remove(discard.value)
        for player in game_state.players: 
            if player.name != playerName:
                for pcard in player.hand:
                    if pcard.value in card.ptable[pcard.color]:
                        card.ptable[pcard.color].remove(pcard.value)
        for color,vals in game_state.tableCards.items():
            if vals and card.ptable[color]:
                for tablecard in vals:
                    if tablecard.value in card.ptable[color]:
                        card.ptable[color].remove(tablecard.value)

    # if i know a card for certain, i can esclude other cards from my hand
    for i in range(len(players_hints[playerName])):
        for j in range(len(players_hints[playerName])):
            if j != i:
                flat_list = [el for vals in players_hints[playerName][j].ptable.values() for el in set(vals)]
                if len(flat_list) == 1: # a sure card
                    for key, vals in players_hints[playerName][j].ptable.items():
                        if vals and vals[0] in players_hints[playerName][i].ptable[key]:
                            players_hints[playerName][i].ptable[key].remove(vals[0])
        print(players_hints[playerName][i].ptable)
      

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    request = GameData.ClientPlayerAddData(playerName)
    s.connect((HOST, PORT))
    s.send(request.serialize())
    data = s.recv(DATASIZE)
    data = GameData.GameData.deserialize(data)
    if type(data) is GameData.ServerPlayerConnectionOk:
        print("Connection accepted by the server. Welcome " + playerName)
    print("[" + playerName + " - " + status + "]: ", end="")
    cv = Condition() # create the condition variable
    t = Thread(target=manageInput, args=(cv,))
    t.start()
    while run:
        dataOk = False
        data = s.recv(DATASIZE)
        if not data:
            continue
        data = GameData.GameData.deserialize(data)
        if type(data) is GameData.ServerPlayerStartRequestAccepted:
            dataOk = True
            print("Ready: " + str(data.acceptedStartRequests) + "/"  + str(data.connectedPlayers) + " players")
            data = s.recv(DATASIZE)
            data = GameData.GameData.deserialize(data)
        if type(data) is GameData.ServerStartGameData:
            dataOk = True
            print("Game start!")
            s.send(GameData.ClientPlayerReadyData(playerName).serialize())
            players = data.players # list of players names in turn order
            # initialize hint dictionary
            if len(players) < 4:
                len_hand = 5
                for p_name in players:
                    hint_cards = list() # the current information each player has about his hand
                    for _ in range(5):
                        hint_cards.append(MyCard(-1, None, None))
                    players_hints[p_name] = hint_cards
            else:
                len_hand = 4
                for p_name in players:
                    hint_cards = list() # the current information each player has about his hand
                    for _ in range(4):
                        hint_cards.append(MyCard(-1, None, None))
                    players_hints[p_name] = hint_cards
            cv.acquire()
            status = statuses[1]
            started = True
            showed = False
            cv.notify()
            cv.release()
        if type(data) is GameData.ServerGameStateData:
            dataOk = True
            game_state = data
            len_hand = data.handSize
            # need to reset because position might be different
            oldhints = deepcopy(players_hints)
            for player in game_state.players:
                if player.name != playerName:
                    hint_cards = list()
                    for i in range(len(player.hand)):
                        # save real ids of cards to find out which cards changed. In this way I take care of repeating hints (if id changes but card has same val and color I can repeat it)
                        hint_cards.append(MyCard(player.hand[i].id, None, None))
                    players_hints[player.name] = hint_cards

            for player in game_state.players:
                if player.name != playerName:
                    hint_cards = list()
                    for i in range(len(player.hand)):
                        for j in range(len(players_hints[player.name])):
                            if players_hints[player.name][j].id == oldhints[player.name][i].id: # this works even if a card changed its position
                                players_hints[player.name][j].value = oldhints[player.name][i].value
                                players_hints[player.name][j].color = oldhints[player.name][i].color
            set_ptable(players_hints, game_state)
            cv.acquire()
            showed = True
            cv.notify()
            cv.release()
            print_state(data)
        if type(data) is GameData.ServerActionInvalid:
            dataOk = True
            print("Invalid action performed. Reason:")
            print(data.message)
        if type(data) is GameData.ServerActionValid:
            dataOk = True
            print("Action valid!")
            print("Current player: " + data.player)
            cv.acquire()
            current_player_index = (current_player_index + 1) % len(players)
            showed = False
            cv.notify()
            cv.release()
        if type(data) is GameData.ServerPlayerMoveOk:
            dataOk = True
            print("Nice move!")
            print("Current player: " + data.player)
            last_player = data.lastPlayer
            last_card_played = data.card
            cv.acquire()
            current_player_index = (current_player_index + 1) % len(players)
            showed = False
            cv.notify()
            cv.release()
        if type(data) is GameData.ServerPlayerThunderStrike:
            dataOk = True
            print("OH NO! The Gods are unhappy with you!")
            cv.acquire()
            current_player_index = (current_player_index + 1) % len(players)
            showed = False
            cv.notify()
            cv.release()
        if type(data) is GameData.ServerHintData:
            dataOk = True        
            print("Hint type: " + data.type)
            print("Player " + data.destination + " cards with value " + str(data.value) + " are:")
            for i in data.positions:
                print("\t" + str(i))

            # save the hint
            for pos in data.positions:
                if (in_chop_zone(players_hints[data.destination], pos) and data.value != 1) or data.value == 5:
                    players_hints[data.destination][pos].save = True
                if data.type == 'color': # value is a color
                    players_hints[data.destination][pos].color = data.value
                else:
                    players_hints[data.destination][pos].value = data.value
                if data.destination == playerName:
                    players_hints[data.destination][pos].recent = True
                if players_hints[data.destination][pos].color is not None and players_hints[data.destination][pos].value is not None:
                    players_hints[data.destination][pos].save = False

            '''Advanced techniques'''
            # finesse
            if len(players) > 2 and (players.index(data.destination) - players.index(data.source)) % len(players) == 2: # check if there is a gap of 1 in the hint
                b_index = (players.index(data.source) + 1) % len(players)
                c_index = (b_index + 1) % len(players)
                finesse_dict = {'finesse':True, 'b_index':b_index, 'c_index':c_index, 'pos':data.positions[-1]}

            # update current player index
            cv.acquire()
            current_player_index = (current_player_index + 1) % len(players)
            showed = False
            cv.notify()
            cv.release()
        if type(data) is GameData.ServerInvalidDataReceived:
            dataOk = True
            print(data.data)
        if type(data) is GameData.ServerGameOver:
            cv.acquire()
            run = False
            cv.notify()
            cv.release()
            t.join()
            dataOk = True
            print(data.message)
            print(data.score)
            print(data.scoreMessage)
            stdout.flush()
            if INFINITE_PLAY:
                scores.append(data.score)
                print(f'Scores history: {scores}')
                print(f'Avg score over {len(scores)} matches: {round(sum(scores)/len(scores), 2)}')
                if len(scores) == 1000:
                    break
                run = True
                print("Ready for a new game!")
                # reinitialize
                # initialize hint dictionary
                for p_name in players:
                    hint_cards = list() # the current information each player has about his hand
                    for _ in range(5):
                        hint_cards.append(MyCard(-1, None, None))
                    players_hints[p_name] = hint_cards
                status = statuses[1]
                current_player_index = 0
                showed = False
                t = Thread(target=manageInput, args=(cv,))
                t.start()
        if not dataOk:
            print("Unknown or unimplemented data type: " +  str(type(data)))
        print("[" + playerName + " - " + status + "]: ", end="")
        stdout.flush()