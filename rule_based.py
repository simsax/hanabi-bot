from sys import argv, stdout
from constants import *

class MyCard:
    def __init__(self, id, value, color):
        self.id = id
        self.value = value
        self.color = color
        self.recent = False
        self.save = False # this being true doesn't mean it's a sure save, it just means it probably is a save
        self.ptable = dict()
        self.reset_ptable()

    def reset_ptable(self):
        self.ptable['green'] = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
        self.ptable['white'] = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
        self.ptable['blue'] = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
        self.ptable['red'] = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
        self.ptable['yellow'] = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
        # update it if there are hints
        if self.color:
            for key in self.ptable.keys():
                if key != self.color:
                    self.ptable[key] = []
        if self.value:
            for key,vals in self.ptable.items():
                if self.ptable[key]:
                    new_vals = list()
                    for val in vals:
                        if val == self.value:
                            new_vals.append(val)
                    self.ptable[key] = new_vals

    def playable(self, table_cards):
        num_playable = 0
        num_possibilities = 0
        for color,vals in table_cards.items():
            for card_val in self.ptable[color]:
                num_possibilities += 1
                if (vals and card_val == vals[-1].value + 1) or (not vals and card_val == 1):
                    num_playable += 1
        return num_playable == num_possibilities
                        

def update_mycards(my_cards, i):
    '''Updates my card knowledge after playing or discarding a card'''
    my_cards.pop(i)
    my_cards.append(MyCard(-1,None,None))

 
def rule_based_IA(game, len_hand, players_hints, players, current_player_index, finesse_dict, last_player, last_card_played):
    my_cards = players_hints[players[current_player_index]] 
    next_player_index = (current_player_index+1) % len(players)
    next_player = game.players[next_player_index]
    next_next_player = game.players[(next_player_index+1) % len(players)]
    destinatary = players[next_player_index]
    his_cards = players_hints[destinatary]
    next_his_cards = players_hints[next_next_player.name]


    '''Update information according to the possibility table'''
    for i in range(len_hand):
        if my_cards[i].color is None or my_cards[i].value is None: # if I have not full info about my card
            flat_list = [el for vals in my_cards[i].ptable.values() for el in set(vals)]
            if len(flat_list) == 1: # a sure card
                for key, vals in my_cards[i].ptable.items():
                    if vals:
                        print("UPDATING CARD INFORMATION FROM PTABLE (RARE)")
                        my_cards[i].color = key
                        my_cards[i].value = vals[0]

    '''Check for a finesse or bluff'''
    if len(players) > 2 and finesse_dict['finesse']:
        b_ix = finesse_dict['b_index']
        c_ix = finesse_dict['c_index']
        pos = finesse_dict['pos']
        # if I am B
        if current_player_index == b_ix and ((next_player.hand[pos].value == 2 and not game.tableCards[next_player.hand[pos].color]) or (game.tableCards[next_player.hand[pos].color] and next_player.hand[pos].value == 2 + game.tableCards[next_player.hand[pos].color][-1].value)):
            print(f'play {len_hand-1} - myinfo: color:{my_cards[len_hand-1].color} value:{my_cards[len_hand-1].value} (finesse play B)')
            update_mycards(my_cards, len_hand-1)
            return f'play {len_hand-1}'
        # if I am C and it's a finesse
        elif current_player_index == c_ix and last_player == players[b_ix] and ((my_cards[pos].color is not None and last_card_played.color == my_cards[pos].color) or (my_cards[pos].color is None and my_cards[pos].value is not None and last_card_played.value == my_cards[pos].value - 1)):
            print(f'play {pos} - myinfo: color:{my_cards[pos].color} value:{my_cards[pos].value} (finesse play C)')
            update_mycards(my_cards, pos)
            return f'play {pos}'
        # if I am C and it's a bluff
        elif current_player_index == c_ix and last_player == players[b_ix] and my_cards[pos].color is not None and last_card_played.color != my_cards[pos].color:
            if game.tableCards[my_cards[pos].color]:
                my_cards[pos].value = game.tableCards[my_cards[pos].color][-1].value + 2
            else:
                my_cards[pos].value = 2
            print(f'Updating info of my card thanks to a bluff (card:{pos}, {my_cards[pos].value} - {my_cards[pos].color})')


    ''' Check if hint received for a chop card is actually a save based on my info (useful only for early game) '''
    for i in range(len_hand):
        if my_cards[i].save:
            if my_cards[i].value is not None and my_cards[i].value != 5:
                for discard_card in game.discardPile:
                    if my_cards[i].value == discard_card.value: # could be a save
                        break
                else: 
                    my_cards[i].save = False
            elif my_cards[i].color is not None:
                for discard_card in game.discardPile:
                    if my_cards[i].color == discard_card.color: # could be a save
                        break
                else: 
                    my_cards[i].save = False


    '''The 100% correct play'''   
    for i in range(len_hand):
        if my_cards[i].value is not None and my_cards[i].color is not None: # if I know my card color and value
            if not game.tableCards[my_cards[i].color]: # if table_cards for a certain color is emptyaq
                if my_cards[i].value == 1: # if I have a value 1 card
                    print(f'play {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (100% play)')
                    update_mycards(my_cards, i)
                    return f'play {i}'
            else: # if table_cards not empty for this color
                table_card = game.tableCards[my_cards[i].color][-1] # look at last card from the pile
                if table_card.value == my_cards[i].value - 1:
                    print(f'play {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (100% play)')
                    update_mycards(my_cards, i)
                    return f'play {i}'

    '''Rare case when there are multiple card possibility and are all playable'''
    for i in range(len_hand):
        if my_cards[i].playable(game.tableCards):
            print(f'play {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (ALL THE POSSIBILITIES ARE PLAYABLE (GIGA RARE))')
            update_mycards(my_cards, i)
            return f'play {i}'

    '''
    Risky play: play leftmost card with a hint if the hint is new
    '''
    if game.usedStormTokens < 2:
        for i in reversed(range(len_hand)): # reversed because the most recent card is the number 4 card (last card appended to my list of cards)
            if my_cards[i].recent and (not my_cards[i].save) and (my_cards[i].value is None or my_cards[i].color is None): # if I have complete info i should not be here, because the 100% play avoided it
                if my_cards[i].value is not None:
                    for table_cards in game.tableCards.values():
                        if (not table_cards and my_cards[i].value == 1) or (table_cards and table_cards[-1].value == my_cards[i].value - 1):
                            print(f'play {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (risky play)')
                            update_mycards(my_cards, i)
                            return f'play {i}'
                if my_cards[i].color is not None:
                    # handle special case when i receive a color hint when there are no table cards: it means i have no 1s and I should discard that card to advance in early game
                    for table_cards in game.tableCards.values():
                        if table_cards:
                            print(f'play {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (risky play)')
                            update_mycards(my_cards, i)
                            return f'play {i}'
                    if game.usedNoteTokens != 0:
                        print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (I know I have no 1s, discard)')
                        update_mycards(my_cards, i)
                        return f'discard {i}'



    ''' Hint next useful card to play '''
    if game.usedNoteTokens < 8:
        '''Advanced hints'''
        if len(players) > 2:
            # look for a finesse or a bluff
            # check if next player has a playable card in the most recent position
            if (game.tableCards[next_player.hand[-1].color] and game.tableCards[next_player.hand[-1].color][-1].value == next_player.hand[-1].value - 1) or (not game.tableCards[next_player.hand[-1].color] and next_player.hand[-1].value == 1):
                # check if the second next player has the next card of the same color in his hand
                for i, card in enumerate(next_next_player.hand):
                    if card.color == next_player.hand[-1].color and card.value == next_player.hand[-1].value + 1 and next_his_cards[i].value is None:
                        # check if hint his safe (it has to be the most recent card with this value)
                        if i != len(next_next_player.hand) - 1:
                            for j in range(i+1, len(next_next_player.hand)):
                                # check if there is a card on the left with same value
                                if next_next_player.hand[j].value == card.value:
                                    # check if there is a duplicated color on the left
                                    for k in range(i+1, len(next_next_player.hand)):
                                        if next_next_player.hand[k].color == card.color:
                                            break
                                    else: # unique color and he doesn't know
                                        if next_his_cards[i].color is None:
                                            print(f'hint color {next_next_player.name} {card.color} (finesse hint)')
                                            return f'hint color {next_next_player.name} {card.color}'
                                    break
                            else: # no duplicated values
                                print(f'hint value {next_next_player.name} {card.value} (finesse hint)')
                                return f'hint value {next_next_player.name} {card.value}'
                        else: # the card is the leftmost one
                            print(f'hint value {next_next_player.name} {card.value} (finesse hint)')
                            return f'hint value {next_next_player.name} {card.value}'

                for i, card in enumerate(next_next_player.hand):
                    # bluff (check if the second next player has a gap of one card)
                    if (not game.tableCards[card.color] and card.value == 2) or (game.tableCards[card.color] and game.tableCards[card.color][-1].value == card.value - 2) and next_his_cards[i].color is None:
                        # check if it is the most recent card with that color
                        if i != len(next_next_player.hand) - 1:
                            for k in range(i+1, len(next_next_player.hand)):
                                if next_next_player.hand[k].color == card.color:
                                    break
                            else:
                                print(f'hint color {next_next_player.name} {card.color} (bluff hint)')
                                return f'hint color {next_next_player.name} {card.color}'
                        else: 
                            print(f'hint color {next_next_player.name} {card.color} (bluff hint)')
                            return f'hint color {next_next_player.name} {card.color}'

        for i, player_card in enumerate(next_player.hand):
            if ((not game.tableCards[player_card.color] and player_card.value == 1) or (game.tableCards[player_card.color] and (game.tableCards[player_card.color][-1].value == player_card.value - 1))) and his_cards[i].value is None:
                # possible hint, but first check if there is a card on the left with the same value
                if i != len(next_player.hand) - 1:
                    for j in range(i+1, len(next_player.hand)):
                        # check if there is a card on the left with same value which is not playable and has incomplete information
                        if next_player.hand[j].value == player_card.value and his_cards[j].color is None and ((not game.tableCards[next_player.hand[j].color] and next_player.hand[j].value != 1) or (game.tableCards[next_player.hand[j].color] and (game.tableCards[next_player.hand[j].color][-1].value != next_player.hand[j].value - 1))):
                            # check if there is a duplicated color on the left
                            for k in range(i+1, len(next_player.hand)):
                                if next_player.hand[k].color == player_card.color and his_cards[k].value is None:
                                    break
                            else: # unique color and he doesn't know
                                if his_cards[i].color is None:
                                    print(f'hint color {destinatary} {player_card.color} (next best move 2)')
                                    return f'hint color {destinatary} {player_card.color}'
                            break
                    else: # no duplicated values
                        print(f'hint value {destinatary} {player_card.value} (next best move 3)')
                        return f'hint value {destinatary} {player_card.value}'
                else: # the card is the leftmost one
                    print(f'hint value {destinatary} {player_card.value} (next best move 4)')
                    return f'hint value {destinatary} {player_card.value}'
        
        chop_index = -1
        for i in range(len(next_player.hand)):
            if his_cards[i].value is None and his_cards[i].color is None:
                chop_index = i
                break

        # hint if other player has a 5 in the chop zone and he doesn't know
        if chop_index != -1 and next_player.hand[chop_index].value == 5: # chop zone
            for j in range(len(next_player.hand)):
                # check if there is a card with same value
                if chop_index != j and next_player.hand[j].value == next_player.hand[chop_index].value and his_cards[j].color is None:
                    break
            else:
                print(f'hint value {destinatary} 5 (chop zone)')
                return f'hint value {destinatary} 5'

        # for each card already discarded look if the player has a copy of it in the chop zone with no hints
        for card in game.discardPile:
            if chop_index != -1 and card.value != 1 and card.value == next_player.hand[chop_index].value and card.color == next_player.hand[chop_index].color:
                for j in range(len(next_player.hand)):
                    # check if there is a card with same value
                    if chop_index != j and next_player.hand[j].value == next_player.hand[chop_index].value and his_cards[j].color is None:
                        break
                else: 
                    print(f'hint value {destinatary} {next_player.hand[chop_index].value} (chop zone)')
                    return f'hint value {destinatary} {next_player.hand[chop_index].value}'

        # give info about any 5 not in the chop zone
        for i in range(len(next_player.hand)):
            if next_player.hand[i].value == 5 and his_cards[i].value is None:
                for j in range(len(next_player.hand)):
                    # check if there is a card with same value
                    if i != j and next_player.hand[j].value == next_player.hand[i].value and his_cards[j].color is None:
                        break
                else: 
                    print(f'hint value {destinatary} 5 (any)')
                    return f'hint value {destinatary} 5'

        ''' Complete the info about a card '''
        # if other player has a save cards give him complete information
        for i in range(len(next_player.hand)):
            if his_cards[i].save and his_cards[i].color is None:
                for j in range(len(next_player.hand)):
                    # check if there is a card with same color
                    if i != j and next_player.hand[j].color == next_player.hand[i].color and his_cards[j].value is None:
                        break
                else: 
                    print(f'hint color {destinatary} {next_player.hand[i].color} (complete save info)')
                    return f'hint color {destinatary} {next_player.hand[i].color}'
            elif his_cards[i].save and his_cards[i].value is None:
                for j in range(len(next_player.hand)):
                    # check if there is a card with same value
                    if i != j and next_player.hand[j].value == next_player.hand[i].value and his_cards[j].color is None:
                        break
                else: 
                    print(f'hint value {destinatary} {next_player.hand[i].value} (complete save info)')
                    return f'hint value {destinatary} {next_player.hand[i].value}'
        
        # dai precedenza agli 1 dato che sono i doppioni più probabili
        for i in range(len(next_player.hand)):
            if his_cards[i].value == 1 and his_cards[i].color is None:
                for j in range(len(next_player.hand)):
                    # check if there is a card with same color
                    if i != j and next_player.hand[j].color == next_player.hand[i].color and his_cards[j].value is None:
                        break
                else: 
                    print(f'hint color {destinatary} {next_player.hand[i].color} (comp info)')
                    return f'hint color {destinatary} {next_player.hand[i].color}'

        # complete the info about a random card
        for i in range(len(next_player.hand)):
            if his_cards[i].value is not None and his_cards[i].color is None:
                for j in range(len(next_player.hand)):
                    # check if there is a card with same color
                    if i != j and next_player.hand[j].color == next_player.hand[i].color and his_cards[j].value is None:
                        break
                else: 
                    print(f'hint color {destinatary} {next_player.hand[i].color} (comp info)')
                    return f'hint color {destinatary} {next_player.hand[i].color}'
            elif his_cards[i].color is not None and his_cards[i].value is None:
                for j in range(len(next_player.hand)):
                    # check if there is a card with same value
                    if i != j and next_player.hand[j].value == next_player.hand[i].value and his_cards[j].color is None:
                        break
                else: 
                    print(f'hint value {destinatary} {next_player.hand[i].value} (comp info)')
                    return f'hint value {destinatary} {next_player.hand[i].value}'
    
    '''Discard righmost card with no hints (card in chop zone)'''
    '''The 100% correct discard'''
    if game.usedNoteTokens != 0:
        for i in range(len_hand):
            if my_cards[i].value is not None and my_cards[i].color is not None and my_cards[i].value != 5: # if I know my card color and value
                if game.tableCards[my_cards[i].color] and game.tableCards[my_cards[i].color][-1].value >= my_cards[i].value:
                    print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (100% discard)')
                    update_mycards(my_cards, i)
                    return f'discard {i}'
                for card in game.discardPile:
                    if card.value != 1 and card.value == my_cards[i].value and card.color == my_cards[i].color:
                        break
                else: # not useful rn and not game breaking to discard it
                    print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (100% discard)')
                    update_mycards(my_cards, i)
                    return f'discard {i}'
        '''If I get the hint of a color that is already completed or a value smaller than every table card, then I should discard it'''
        for i in range(len_hand):
            if my_cards[i].color is not None:
                if game.tableCards[my_cards[i].color] and game.tableCards[my_cards[i].color][-1].value == 5:
                    print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (100% discard)')
                    update_mycards(my_cards, i)
                    return f'discard {i}'
                elif my_cards[i].value is not None:
                    if game.tableCards[my_cards[i].color] and game.tableCards[my_cards[i].color][-1].value >= my_cards[i].value:
                        print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (100% discard)')
                        update_mycards(my_cards, i)
                        return f'discard {i}'
            if my_cards[i].value is not None:
                for table_cards in game.tableCards.values():
                    if my_cards[i].value > len(table_cards):
                        # safe card, don't discard
                        break
                else: # useless card, discard
                    print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (100% discard)')
                    update_mycards(my_cards, i)
                    return f'discard {i}'

        for i in range(len_hand):
            if not my_cards[i].save and my_cards[i].color is None and my_cards[i].value is None:
                print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (rightmost discard 1)')
                update_mycards(my_cards, i)
                return f'discard {i}'
        for i in range(len_hand):
            if not my_cards[i].save and (my_cards[i].color is None or my_cards[i].value is None) and my_cards[i].value != 5:
                print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (rightmost discard 2)')
                update_mycards(my_cards, i)
                return f'discard {i}'
        # every card has a hint (rare case, still discard the oldest card not equal to 5)
        for i in range(len_hand):
            if not my_cards[i].save and my_cards[i].value != 5:
                print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (rightmost discard 3)')
                update_mycards(my_cards, i)
                return f'discard {i}'
        # every card is a save
        for i in range(len_hand):
            if not my_cards[i].recent and my_cards[i].value != 5:
                print(f'discard {i} - myinfo: color:{my_cards[i].color} value:{my_cards[i].value} (rightmost discard 4)')
                update_mycards(my_cards, i)
                return f'discard {i}'

    '''The forced hints'''
    if game.usedNoteTokens < 8:
        print("SORRY I HAVE TO")
        for table_cards in game.tableCards.values():
            if table_cards:
                break
        else: 
            print(f'hint color {destinatary} {next_player.hand[0].color} (forced controlled hint)')
            return f'hint color {destinatary} {next_player.hand[0].color}'

        # look for a repeating non damaging hint
        for i in range(len(next_player.hand)):
            if his_cards[i].value is not None:
                for j in range(len(next_player.hand)):
                    if i != j and next_player.hand[j].value == next_player.hand[i].value and his_cards[j].value is None and his_cards[j].color is None:
                        break
                else: 
                    print(f'hint value {destinatary} {next_player.hand[i].value} (forced non damaging hint)')
                    return f'hint value {destinatary} {next_player.hand[i].value}'
            elif his_cards[i].color is not None:
                for j in range(len(next_player.hand)):
                    if i != j and next_player.hand[j].color == next_player.hand[i].color and his_cards[j].value is None and his_cards[j].color is None:
                        break
                else: 
                    print(f'hint color {destinatary} {next_player.hand[i].color} (forced non damaging hint)')
                    return f'hint color {destinatary} {next_player.hand[i].color}'

        if chop_index != -1:
            if his_cards[chop_index].value is None:
                for i in range(len(next_player.hand)):
                    if i != chop_index and next_player.hand[chop_index].value == next_player.hand[i].value and his_cards[i].color is None:
                        break
                else: 
                    print(f'hint value {destinatary} {next_player.hand[chop_index].value} (forced controlled hint)')
                    return f'hint value {destinatary} {next_player.hand[chop_index].value}'

        for i in range(len(next_player.hand)):
            if his_cards[i].color is None:
                print(f'hint color {destinatary} {next_player.hand[i].color} (forced dangerous hint)')
                return f'hint color {destinatary} {next_player.hand[i].color}'
            elif his_cards[i].value is None:
                print(f'hint value {destinatary} {next_player.hand[i].value} (forced dangerous hint)')
                return f'hint value {destinatary} {next_player.hand[i].value}'
    
    # every card is a 5, game lost
    print(f'discard 0 - myinfo: color:{my_cards[0].color} value:{my_cards[0].value} save:{my_cards[0].save} (very last forced discard)')
    update_mycards(my_cards, 0)
    return f'discard 0'

