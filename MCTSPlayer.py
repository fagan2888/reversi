from board import Board
from Player import Player

class MCTSNode(object):
    board = Board()

    def __init__(self, parent, s, c=1.4):
        self.parent = parent
        self.children = {}  # dict mapping action => MCTSNode
        # TODO: make sure starting at 0 doesn't screw things up
        self.n_visits = 0
        self.value = 0
        self.state = s
        self.c = c
        pass

    def expand(self):
        # TODO: fill me in -- add child nodes
        pass

    def select(self):
        # TODO: implement UTC or some more intelligent algo that encourages
        #       exploration
        # TODO: if all children nodes aren't in place, select a move randomly
        return max(iteritems_dict(self.children), key=lambda z: z.value)

    def _update(self, z):
        self.n_visits += 1

        # NOTE: only counting wins (positive z)!
        if z > 0:
            self.value += 1
        pass

    def backprop(self, z):
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
    def value(self):
        return self.value / self.n_visits


class MCTSPlayer(Player):
    def __init__(self, me, you):
        super(MCTS, self).__init__(me, you)
        # maps from (me_placed, foe_placed) => MCTSNode
        self.nodes = {(0, 0): MCTSNode(None, (0, 0))}

    def move(self, moves):
        pass
