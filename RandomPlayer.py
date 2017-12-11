from Player import Player
import random

class RandomPlayer(Player):
    def __init__(self, me, you):
        super(RandomPlayer, self).__init__(me, you)

    def move(self, state):
        moves = self.get_valid_moves(state[0], state[1])
        return random.choice(moves)
