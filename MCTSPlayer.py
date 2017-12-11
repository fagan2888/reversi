import sys
import time
import random
import math
from board import Board
from Player import Player
import pickle

if sys.version_info.major == 2:
    range = xrange

    def iteritems(x):
        return x.iteritems()

    def itervalues(x):
        return x.itervalues()

    def iterkeys(x):
        return x.iterkeys()
else:
    def iteritems(x):
        return x.items()

    def itervalues(x):
        return x.values()

    def iterkeys(x):
        return x.keys()


class MCTSNode(object):
    board = Board()

    def __init__(self, parent, c=1.4):
        """
        Construct a node in a Markov Chain Tree Search tree.

        Parameters
        ----------
        parent: MCTSNode or NoneType
            The parent node in the tree. Used to do backpropogation of game
            outcomes

        c: float
            A hyperparameter used in trianing... TODO fill in once we use it
        """
        self.parent = parent
        self.children = {}  # dict mapping action => MCTSNode
        self.n_visits = 0
        self.value = 0
        self.c = c

    def expand(self, actions):
        """
        Expand the search tree to include all ``actions`` as children

        Parameters
        ----------
        actions:
            The list of actions that should be added as nodes in the tree
        """
        for action in actions:
            if action not in self.children:
                self.children[action] = MCTSNode(self)

    def select(self):
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
        # TODO: implement UTC or some more intelligent algo that encourages
        #       exploration
        if any(child.n_visits == 0 for child in itervalues(self.children)):
            action = random.choice(list(iterkeys(self.children)))
            node = self.children[action]
            return action, node

        # use UCB1
        ln_n_term = self.c * math.sqrt(2 * math.log(
            sum(child.n_visits for child in itervalues(self.children))
        ))
        val, action = max(
            (
                child.raw_value + ln_n_term / math.sqrt(child.n_visits or 1),
                action
            )
            for action, child in iteritems(self.children)
        )

        return action, self.children[action]

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
        pass

    def backprop(self, z):
        """
        Apply the backpropogation operator all the way up the tree.

        Recursively calls `_update` on all parent nodes and then calls
        `_update` on this node itself.
        """
        if self.parent:
            # propogate all the way back up the tree
            self.parent.backprop(z)
        self._update(z)

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def is_root(self):
        return self.parent is None

    @property
    def raw_value(self):
        return self.value / (self.n_visits or 1)


class MCTSPlayer(Player):
    def __init__(self, me, you, move_time_limit=1):
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
        # maps from (me_placed, foe_placed, turn) => MCTSNode
        self._current_node = MCTSNode(None)
        self.nodes = {(0, 0, 1): self._current_node}
        self.move_time_limit = move_time_limit

    def move(self, state):
        print("Moving with state: {}".format(state))
        # update current node
        if state in self.nodes:
            self._current_node = self.nodes[state]
        else:
            new_node = MCTSNode(self._current_node)
            self._current_node = new_node
            self.nodes[state] = new_node

        if self.round < 4:
            moves = self.get_valid_moves((state[0], state[1]), state[2])
            return random.choice(moves)

        # simulate as many times as we can from this node to the end of the
        # game. This function will be responsible for backprop
        end_time = time.time() + self.move_time_limit
        nsims = 0
        while time.time() < end_time:
            print("Running a simulation")
            nsims += 1
            self.run_simulation(state)

        print("\n\n\nJust did {} simulations in {} seconds\n\n\n".format(nsims, self.move_time_limit))

        return self._current_node.select()[0]

    def run_simulation(self, state, disp=False):
        # Set up the board with the current state
        print("Starting simulation with state {}".format(state))
        sim_board = Board(state[0], state[1], state[2])
        node = self._current_node
        new_state = state

        print("in the simulation with initial board:")
        print(sim_board)

        while True:
            if sim_board.is_over():
                break

            if node.is_leaf:
                # we don't have info for this node yet, need to expand. select
                valid_moves = sim_board.get_moves()
                if len(valid_moves) == 0:
                    # this player can't move, but game isn't over. Tell the
                    # board to have the player pass
                    sim_board.player_passes()
                    continue
                node.expand(valid_moves)
                action = random.choice(valid_moves)
            else:
                action, node = node.select()

            new_state = sim_board.do_action(sim_board.spaces[action])

            if disp:
                print(new_state)
                print(sim_board)

        print("finished simulation???")

        # TODO: because I did self play I should also backprop up the second
        #       player's tree.
        score1 = sim_board.score(new_state[0])
        score2 = sim_board.score(new_state[1])
        if score1 > score2:
            z1 = 1
        elif score1 == score2:
            z1 = 0
        else:
            z1 = -1

        if state[2] == 1:
            node.backprop(z1)
        else:
            node.backprop(-z1)

    def save_stuff(self):
        output = {"tree": self.nodes}
        with open("tree.pkl", "wb") as f:
            pickle.dump(output, f)
