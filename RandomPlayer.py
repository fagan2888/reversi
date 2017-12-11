from Player import Player
import random


class RandomPlayer(Player):
    def __init__(self, me, you):
        super(RandomPlayer, self).__init__(me, you)

    def move(self, state):
        return random.choice(self.get_valid_moves(state))
