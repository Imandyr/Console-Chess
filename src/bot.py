import random
from abc import abstractmethod
from typing import Any, cast, Sequence, Optional, NamedTuple

from .base import Player, Figure, Table


def cost_of_figure(figure: Any) -> int:
    try:
        figure = cast(Figure, figure)
        return figure.cost
    except (TypeError, ValueError, AttributeError):
        return 0


def get_all_items_with_highest_value(target_list: list[Sequence], value_index: int) -> list[Sequence]:
    """ Returns all sequences from target_list which have the highest value on value_index.
    Example: get_all_items_with_highest_value([(1), (3), (2), (3)]) == [(3), (3)] """
    target_list.sort(key=lambda x: x[value_index])
    threshold = -1
    for c, i in enumerate(target_list[::-1], 1):
        if i[value_index] == target_list[-1][value_index]:
            threshold = -c
        else:
            break
    return target_list[threshold:]


class Move(NamedTuple):
    """ Tuple with move data.
    Shape: tuple[figure: Figure, to: tuple[int, int], content: Optional[Figure] = None, cost: Optional[int] = None]
    """
    figure: Figure
    to: tuple[int, int]
    content: Optional[Figure] = None
    cost: Optional[int] = None


class Bot(Player):
    def __init__(self, table: Table, goes_up: bool, name: Optional[str] = None) -> None:
        super().__init__(table, goes_up, name)
        self._available_moves_costs: Optional[list[Move]] = None
        self._best_move: Optional[Move] = None

    @property
    @abstractmethod
    def available_moves_costs(self) -> list[Move]:
        """ Returns all available moves of owned figures and costs of figures on target position. """
        if self._available_moves_costs is None:
            ...  # get available moves costs
        return self._available_moves_costs

    @property
    def best_move(self) -> Move:
        """ Calculates and returns the best possible move. """
        if self._best_move is None:
            self._best_move = random.choice(get_all_items_with_highest_value(self.available_moves_costs, 3))
        return self._best_move

    @property
    def available_moves(self) -> list[Move]:
        """ Returns all available moves of owned figures. """
        return [Move(figure, move) for figure in self.figures for move in figure.available_moves]

    def auto_move(self) -> None:
        """ Automatically calculates and makes the best possible move. """
        best_move = self.best_move
        best_move[0].move(best_move[1])

    def reset(self) -> None:
        super().reset()
        self._available_moves_costs = None
        self._best_move = None


class EasyBot(Bot):
    @property
    def available_moves_costs(self) -> list[Move]:
        """ Returns all available moves of owned figures and costs of figures on target position.
        In other words, this bot does not think about his losses at all. """
        if self._available_moves_costs is None:
            self._available_moves_costs = [Move(figure, move, cost=cost_of_figure(self.table.get_figure(move)))
                                           for figure in self.figures for move in figure.available_moves]
        return self._available_moves_costs


class NormalBot(Bot):
    @property
    def available_moves_costs(self) -> list[Move]:
        """ Returns all available moves of owned figures and costs of figures on target position.
        Move value is based on the gain from killing a reachable enemy figure and on the cost
        of losing a moving figure, if figure move destination is in reach of other enemy figures. """
        if self._available_moves_costs is None:
            self._available_moves_costs = []
            enemy_moves = self.available_moves_of_enemy_ignore_ownership

            for move in self.available_moves:
                cost = cost_of_figure(self.table.get_figure(move[1]))
                if move[1] in enemy_moves:
                    cost -= cost_of_figure(move[0])
                self._available_moves_costs.append(Move(move[0], move[1], cost=cost))

        return self._available_moves_costs


class HardBot(Bot):
    def value_of_move(self, _from: tuple[int, int], to: tuple[int, int]) -> tuple[int, int]:
        """ Calculates value of given move and return it in the form of tuple[gain, loss].
        Gain - its cost of an enemy figure, which will be killed on this move (or 0 if there is no figure).
        Loss - its cost of the most valuable owned figure, which will be in the reach of an enemy figures
        after this move. """
        n_table, n_players = self.table.full_copy()
        n_self = cast(HardBot, self.find_copy_of_yourself(n_players))
        n_self.move(_from, to)
        e_moves = n_self.available_moves_of_enemy

        if len(e_moves) == 0:
            return cost_of_figure(self.table.get_figure(to)), 0
        else:
            return (cost_of_figure(self.table.get_figure(to)),
                    - max(cost_of_figure(n_table.get_figure(i)) for i in e_moves))

    @property
    def available_moves_costs(self) -> list[Move]:
        """
        Returns all available moves of owned figures and costs of figures on target position.

        Move cost is based on the cost of enemy's figure in move target position which will be subtracted from
        the cost of the most valuable HardBot's figure from the set of all owned figures that will be in reach of
        an enemy after this move.

        This should lead to the most efficient moves in the span of one round,
        because this algorithm can choose best from both attack and defense move option.

        :return: List of Move objects with their cost specified.
        """
        if self._available_moves_costs is None:
            self._available_moves_costs = []

            for move in self.available_moves:
                value = self.value_of_move(move.figure.position, move.to)
                self._available_moves_costs.append(Move(move.figure, move.to, cost=sum(value)))

        return self._available_moves_costs
