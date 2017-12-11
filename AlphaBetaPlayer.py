from Player import Player
import sys
import time
import random
from pprint import pprint
from board import Board

INF = 1.0e100
CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
CENTERS = [(3, 3), (3, 4), (4, 3), (4, 4)]
DANGERS = [(0, 1), (0, 6), (1, 0), (1, 1), (1, 6), (1, 7), (6, 0), (6, 1),
           (6, 6), (6, 7), (7, 1), (7, 6)]

G_EDGES = [(0, 2), (0, 3), (0, 4), (0, 5), (2, 0), (3, 0), (4, 0), (5, 0),
           (2, 7), (3, 7), (4, 7), (5, 7), (7, 2), (7, 3), (7, 4), (7, 5)]

NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
             (1, 1)]

def print_futures(futures):
    for value_move in futures:
        print(value_move[1], ": ", value_move[0])

if sys.version_info.major == 2:
    range = xrange

    def iteritems_dict(x):
        return x.iteritems()
else:
    def iteritems_dict(x):
        return x.items()

def get_value(future):
    return future[0]


def printState(s):
    # INVERTS TO MATCH VISUAL
    pprint(s[::-1])


def compare(a, b):
    return (a > b) - (a < b)
class AlphaBetaPlayer(Player):

    def __init__(self, me, you, fprune=0.1, margin=0.0):
        super(AlphaBetaPlayer, self).__init__(me, you)

        # algorithm params
        self.margin = margin  # for more aggressive pruning
        self.fprune = fprune  # for unlikely random pruning

        self.overall_weight = 1.0
        self.corner_weight = 4.0
        self.g_weight = 2.0
        self.danger_weight = 2.0
        self.center_weight = 1.0
        self.move_weight = 1.1

        self.connected_weight = 1.5
        self.mobility_weight = 2.0
        self.frontiers_weight = 5.0

        self.modify_weights_at_round = 30
        self.seconds_cutoff = 9
        self.max_depth = 4

        self.t1, self.t2 = 0.0, 0.0
        self.round = -1
        self.timeLimit = time.time()

    def move(self, state):
        moves = self.get_valid_moves(state[0], state[1])
        self.time_limit = time.time() + self.seconds_cutoff

        if self.round < 4:
            return random.choice(moves)

        if self.round > self.modify_weights_at_round:
            self.overall_weight = 2.0
            self.mobility_weight = 1.0
            self.max_depth = 5

        return self.alpha_beta(moves)

    def alpha_beta(self, moves):
        def future(move):
            space = self.board.spaces[move]
            next_s = self.board.next_state_bits(space, self.mine, self.foe)
            return self.min_val(next_s, -INF, INF, depth=0)

        futures = [(future(move), move) for move in moves]
        print_futures(futures)
        best_value_move = max(futures, key=get_value)
        print("Best: ", best_value_move[1], ": ", best_value_move[0])
        return best_value_move[1]

    def stop(self, depth):
        if depth > self.max_depth:
            return True
        elif time.time() > self.time_limit:
            print("-" * depth, "Timeout")
            return True
        else:
            return False

    def min_val(self, s, alpha, beta, depth):
        if self.stop(depth):
            return self.evaluate(s, self.me)

        val = INF
        moves = self.get_valid_moves(s, self.you)

        for idx, move in enumerate(moves):
            # next_state_bits(self, space, mover, opponent):
            space = self.board.spaces[move]
            next_s = self.board.next_state_bits(space, s[1], s[0])
            val = min(val, self.max_val(next_s, alpha, beta, depth+1))
            if val - self.margin <= alpha:  # or fprune > random():
                return val
            beta = min(beta, val)

        return val

    def max_val(self, s, alpha, beta, depth):
        if self.stop(depth):
            return self.evaluate(s, self.me)

        val = -INF
        moves = self.get_valid_moves(s, self.me)

        for idx, move in enumerate(moves):
            space = self.board.spaces[move]
            next_s = self.board.next_state_bits(space, s[0], s[1])
            val = max(val, self.min_val(next_s, alpha, beta, depth+1))
            if val + self.margin >= beta:
                return val
            alpha = max(alpha, val)

        return val

    def enemy_index(self, player):
        return (player == 1) + 1

    def evaluate(self, s, player):
        enemy = self.enemy_index(player)

        # how many moves do I have vs how many moves they have
        player_moves = self.get_valid_moves(s, player)
        enemy_moves = self.get_valid_moves(s, enemy)

        mobility = len(player_moves)
        frontiers = len(enemy_moves)

        # overall = compare(score(s, player), score(s, enemy))
        my_score = self.board.score(s[0])
        foe_score = self.board.score(s[1])
        overall = (my_score - foe_score) / (my_score + foe_score)

        corners_bits = sum(self.board.spaces[i] for i in CORNERS)
        corners = (self.board.score(corners_bits & s[0]) -
                   self.board.score(corners_bits & s[1]))

        # edges_bits = sum(self.board.spaces[i] for i in G_EDGES)
        # edges = (self.board.score(edges_bits & s[0]) -
        #            self.board.score(edges_bits & s[1]))

        dangers_bits = sum(self.board.spaces[i] for i in DANGERS)
        dangers = (self.board.score(dangers_bits & s[0]) -
                   self.board.score(dangers_bits & s[1]))

        # centers_bits = sum(self.board.spaces[i] for i in CENTERS)
        # centers = (self.board.score(centers_bits & s[0]) -
        #            self.board.score(centers_bits & s[1]))

        return (self.overall_weight * overall +
                self.corner_weight * corners +
                self.danger_weight * dangers +
                self.mobility_weight * mobility -
                self.frontiers_weight * frontiers)
