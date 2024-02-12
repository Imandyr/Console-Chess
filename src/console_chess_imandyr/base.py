from typing import List, Tuple, Optional, Set, Iterable
from abc import ABC, abstractmethod


class InvalidMove(IndexError):
    """ Invalid figure move. """


class MissingFigure(IndexError):
    """ No figure is available. """


class AccessError(ValueError):
    """ The First player can't move figures of second player. """


class Table(list):
    def __init__(self, rows: int = 8, columns: int = 8) -> None:
        """ Chess table object class. Used to contain chess Figures. """
        super().__init__()
        self.rows = rows
        self.columns = columns
        self[:] = [[None for column in range(self.rows)] for row in range(self.columns)]
        self._figures: Optional[list[Figure]] = None
        self._players: Optional[set[Player]] = None

    def __repr__(self) -> str:
        return "   " + "     ".join(str(i) for i in range(self.columns)) + \
            "\n" + "\n".join(f"{c} " + str(row) for c, row in enumerate(self))

    def get_figure_position(self, figure: "Figure") -> Tuple[int, int]:
        """ Get the position of a given figure on the table. """
        for count, row in enumerate(self):
            for count_2, column in enumerate(row):
                if figure == column:
                    return count, count_2
        raise MissingFigure("Given figure is not located in this table.")

    def get_figure(self, position: Tuple[int, int]) -> Optional["Figure"]:
        """ Get a figure from the table by its position. If there is no figure, returns None. """
        return self[position[0]][position[1]]

    def set_figure(self, figure: Optional["Figure"], position: Tuple[int, int]) -> None:
        """ Set Figure object or None on given position. """
        self[position[0]][position[1]] = figure

    @property
    def figures(self) -> List["Figure"]:
        """ Returns list of all figures from the table. """
        if self._figures is None:
            self._figures = [column for row in self for column in row if isinstance(column, Figure)]
        return self._figures

    def delete_all_figures(self) -> None:
        """ Change all figures on table to Nones. """
        for i in self.figures:
            self.set_figure(None, i.position)
        self.reset()

    @property
    def players(self) -> set["Player"]:
        """ Returns set of all players whose figures are currently placed inside this table. """
        if self._players is None:
            self._players = {f.player for f in self.figures}
        return self._players

    def full_copy(self) -> tuple["Table", set["Player"]]:
        """ Returns new table with new players objects, but all their attribute values are the same
        and all figures placed in the same positions as at the original table. """
        n_table = Table(self.rows, self.columns)

        if len(self.players) > 0:
            players = list(self.players)
            n_players = [Player(n_table, player.goes_up, player.name) for player in players]

            for c, player in enumerate(players):
                n_curr = n_players[c]
                for figure in player.figures:
                    n_table.set_figure(figure.__class__(n_table, n_curr), figure.position)

            return n_table, set(n_players)

        else:
            return n_table, set()

    def reset(self) -> None:
        """ Resets all cashed values of the table, figures and players on it. """
        for i in self.figures:
            i.reset()
        for i in self.players:
            i.reset()
        self._figures = None
        self._players = None


class Player:
    def __init__(self, table: Table, goes_up: bool, name: Optional[str] = None) -> None:
        """ Player class which can make moves with owned Figures.
        All player's figures can either go up (white figures) or down (black figures)."""
        super().__init__()
        self.table = table
        self.goes_up = goes_up
        if name:
            self.name = name
        else:
            self.name = "White" if self.goes_up else "Black"
        self._figures: Optional[List[Figure]] = None

    def add_figure(self, figure: "Figure") -> None:
        """ Set this player as an owner of figure. """
        figure.player = self

    def move(self, _from: Tuple[int, int], to: Tuple[int, int]) -> None:
        """ Moves some of the owned figures from "_from" to "to" position on Table square.
        Raises InvalidMove exception if given move is invalid and MissingFigure if on given index is no figure to move,
        or if its other player's figure. """
        figure = self.table.get_figure(_from)
        if not figure:
            raise MissingFigure("Position, given in 'from', doesn't contain any figures. "
                                f"Available figures positions for player '{self}' is: "
                                f"{set(i.position for i in self.figures)}.")
        if not figure.player == self:
            raise AccessError(f"Player '{self.name}' can't move figures of player '{figure.player.name}'.")
        figure.move(to)

    def __repr__(self) -> str:
        return self.name

    @property
    def figures(self) -> List["Figure"]:
        """ Returns list of all owned figures. """
        if self._figures is None:
            self._figures = [figure for figure in self.table.figures if figure.player == self]
        return self._figures

    def find_copy_of_yourself(self, players: Iterable["Player"]) -> "Player":
        """ Finds and returns one player from iterable with bunch players
        if this player has all his figures on the same positions as at this player.
        Raises ValueError if it finds nothing. """
        positions = [figure.position for figure in self.figures]
        for player in players:
            if positions == [figure.position for figure in player.figures]:
                return player
        raise ValueError("There is no copy of this player.")

    @property
    def available_moves_of_enemy(self) -> set[tuple[int, int]]:
        """ Set with all locations in which enemy figures can currently step. """
        return {move for figure in self.table.figures if figure.player != self
                for move in figure.available_moves}

    @property
    def available_moves_of_enemy_ignore_ownership(self) -> set[tuple[int, int]]:
        """ Set with all locations in which enemy figures can currently step, but including their allies. """
        return {move for figure in self.table.figures if figure.player != self
                for move in figure.available_moves_ignore_ownership}

    def reset(self) -> None:
        """ Resets all cashed values of player. """
        self._figures = None


class Figure(ABC):
    cost: int = 0

    def __init__(self, table: Table, player: Player) -> None:
        """ Base abstract class for all chess Figures. """
        self.table = table
        self._player = player
        self._position: Optional[Tuple[int, int]] = None
        self._available_moves: Optional[Set[Tuple[int, int]]] = None
        self._available_moves_ignore_ownership: Optional[Set[Tuple[int, int]]] = None

    def __lt__(self, other: "Figure") -> bool:
        return self.cost < other.cost

    def __gt__(self, other: "Figure") -> bool:
        return self.cost > other.cost

    @property
    def player(self) -> Player:
        """ Returns player which owns this figure. """
        return self._player

    @player.setter
    def player(self, player: Player) -> None:
        """ Set player which owns this figure. """
        self.player = player

    @property
    def position(self) -> Tuple[int, int]:
        """ Returns position of this figure on the table. """
        if self._position is None:
            self._position = self.table.get_figure_position(self)
        return self._position

    def move(self, to: Tuple[int, int]) -> None:
        """ Moves this figure from current position to given Table square.
        Raises InvalidMove exception if given move is invalid. """
        if not self.move_validity(to):
            raise InvalidMove(f"This figure move is invalid. "
                              f"Available moves for figure on {self.position} is: {list(self.available_moves)}.")
        self.table.set_figure(None, self.position)
        self.table.reset()
        self.table.set_figure(self, to)

    def move_validity(self, to: Tuple[int, int]) -> bool:
        """ Judges is move from current position to given is valid for this figure. """
        return to in self.available_moves

    @property
    @abstractmethod
    def available_moves(self) -> Set[Tuple[int, int]]:
        """ Returns set of all table positions on which this figure is can be moved. """
        if self._available_moves is None:
            ...  # get available moves
        return self._available_moves

    @property
    @abstractmethod
    def available_moves_ignore_ownership(self) -> Set[Tuple[int, int]]:
        """ Returns set of all table positions on which this figure is can be moved,
        but all other figures are considered as an enemy, even if they owned by the same player. """
        if self._available_moves_ignore_ownership is None:
            ...  # get available moves
        return self._available_moves_ignore_ownership

    def __repr__(self) -> str:
        return f"{self.__class__.__name__[:2]}-{self.player.name[0]}"

    def reset(self) -> None:
        """ Resets all cashed values of a figure. """
        self._position = None
        self._available_moves = None
        self._available_moves_ignore_ownership = None
