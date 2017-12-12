import os
import sys
import time
import random
import math
from board import Board
from Player import Player
import pickle


if sys.version_info.major == 2:
    range = xrange


def first(x):
    return x[0]


class MCTSTree(object):
    def __init__(self, c=1.4):
        self.nodes = {(0, 0, 1): MCTSNode2()}
        self.board = Board()
        self.expand((0, 0, 1))
        self.c = c

    def expand(self, state):
        if state[2] == 1:
            actions = self.board.legal_actions(state[0], state[1])
        else:
            actions = self.board.legal_actions(state[1], state[0])

        for action in actions:
            # Generate new state for action
            action_bits = self.board.spaces[action]
            if state[2] == 1:
                new_positions = self.board.next_state_bits(
                    action_bits, state[0], state[1]
                )
                new_state = (new_positions[0], new_positions[1], 2)
            else:
                new_positions = self.board.next_state_bits(
                    action_bits, state[1], state[0]
                )

                # NOTE: this assumes that the state is always (p1, p2, turn)
                # -- hence using `new_positions[1]` as first element here
                new_state = (new_positions[1], new_positions[0], 1)

            if new_state in self.nodes:
                if (action, new_state) not in self.nodes[state].children:
                    self.nodes[state].children.append((action, new_state))
                continue

            self.nodes[new_state] = MCTSNode2()

            # add (action, new_state) to current_node.children
            self.nodes[state].children.append((action, new_state))

    def select(self, state):
        """
        Select an action from self.children

        If all child nodes have been visited, select an action using the UCB1
        algorithm.

        Otherwise return a randomly selected action

        Returns
        -------
        action
            The selected action
        """
        node = self.nodes[state]

        if any(self.nodes[child_state].n_visits == 0 for (a, child_state) in node.children):
            action, c_s = random.choice(node.children)
            return action, c_s

        total_visits = sum(
            self.nodes[c_s].n_visits for (a, c_s) in node.children
        )
        term = self.c * math.sqrt(2*math.log(total_visits or 1))

        value, action, child_state = max(
            (((self.nodes[c_s].win_percent + term / math.sqrt(self.nodes[c_s].n_visits or 1)), action, c_s)
            for (action, c_s) in node.children),
            key=first
        )

        return action, child_state

    def backprop(self, payoffs, history):
        """
        Apply backprop operation given payoffs for each player (``payoffs``)
        and a history of states.

        Parameters
        ----------
        payoffs: iterable, len(2)
            The payoff for each player. This must be a length 2 iterable

        history: list(state)
            A list of states recording a history of the game

        """
        # [::-1] to traverse in reverse
        for state in history[::-1]:
            self.nodes[state]._update(payoffs[state[2] - 1])


class MCTSNode2(object):
    # define slots to make object creation more efficent
    __slots__ = ["value", "n_visits", "children"]

    def __init__(self):
        self.value = 0
        self.n_visits = 0
        self.children = []

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def win_percent(self):
        return self.value / (self.n_visits or 1)

    def _update(self, z):
        """
        Update this node's ``n_visits`` and ``value`` properties

        Parameters
        ----------
        z
            The terminal value that was recieved after visiting this node
        """
        self.n_visits += 1

        # NOTE: only counting wins (positive z)!
        if z > 0:
            self.value += 1


class MCTSPlayer(Player):
    def __init__(self, me, you, move_time_limit=1, max_rollouts=100000):
        """
        Create an AI player that uses Monte Carlo Tree Search (MCTS) to
        select moves.

        Parameters
        ----------
        me, you: int
            Integers specifying the player ID for this player (``me``) and
            the opponent (``you``). Must be 1 and 2

        move_time_limit: number, optional(default=3)
            The time limit on the maximum number of seconds each the
            calculation of each move can take
        """
        super(MCTSPlayer, self).__init__(me, you)
        self.board = Board()
        # Load existing nodes
        self.tree = MCTSTree()
        self.move_time_limit = move_time_limit
        self.max_rollouts = max_rollouts


    def move(self, state):
        if state not in self.tree.nodes:
            node = MCTSNode2()
            self.tree.nodes[state] = node
            self.tree.expand(state)
        else:
            node = self.tree.nodes[state]

        if self.round < 4:
            # node won't have children yet, so we need to expand.
            print("Expanding before round 4 with state:", state)
            self.tree.expand(state)
            if len(node.children) == 0:
                print("Houston, we have a problem")
            return random.choice(node.children)[0]

        # simulate as many times as we can from this node to the end of the
        # game. This function will be responsible for backprop
        start_time = time.time()
        end_time = start_time + self.move_time_limit
        nsims = 0
        while time.time() < end_time and nsims < self.max_rollouts:
            nsims += 1
            self.run_simulation(state)

        msg = "\n\n\nJust did {} simulations in {} seconds\n\n\n"
        print(msg.format(nsims, time.time() - start_time))

        action, s = self.tree.select(state)
        return action

    def run_simulation(self, state, disp=False):
        # print("Starting simulation with state {}".format(state))
        history = [state]

        while not self.board.is_over():
            self.board.set_state(state)
            if disp:
                print(state)
                print(Board(state[0], state[1]))

            if state not in self.tree.nodes:
                # could get here if a player has to pass
                self.tree.nodes[state] = MCTSNode2()

            node = self.tree.nodes[state]

            if node.is_leaf:
                # we don't have info for this node yet, need to expand
                self.tree.expand(state)
                if len(node.children) == 0:
                    # this player doesn't have any moves available to him
                    # need to let the other player go...
                    state = (state[0], state[1], (state[2] == 1) + 1)
                    continue
                action, state = random.choice(node.children)
            else:
                action, state = self.tree.select(state) # -> (action, child_state)

            history.append(state)

        score1 = self.board.score(state[0])
        score2 = self.board.score(state[1])
        self.tree.backprop((score1, score2), history)

    def load_tree(self):
        my_file = "tree.pkl"
        if os.path.exists(my_file):
            print("Loading tree...")
            with open(my_file, "rb") as f:
                data = pickle.load(f)
            self.tree = data["tree"]
        else:
            self.tree = MCTSTree()
        print("Loaded tree with {} elements".format(len(self.tree.nodes)))

    def save_tree(self):
        print("Saving tree...")
        output = {"tree": self.tree}
        with open("tree.pkl", "wb") as f:
            pickle.dump(output, f)
