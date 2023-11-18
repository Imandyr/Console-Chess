from typing import List, Tuple, Optional, Set
from abc import ABC, abstractmethod


class InvalidMove(IndexError):
    """ Invalid figure move. """


class MissingFigure(IndexError):
    """ No figure is available. """


class AccessError(ValueError):
    """ First player can't move figures of second player. """


class Table(list):
    def __init__(self, rows: int = 8, columns: int = 8) -> None:
        """ Chess table object class. Used to contain chess Figures. """
        super().__init__()
        self.rows = rows
        self.columns = columns
        self[:] = [[None for column in range(self.rows)] for row in range(self.columns)]
        self._figures: Optional[List[Figure]] = None

    def __repr__(self) -> str:
        return "   " + "     ".join(str(i) for i in range(self.columns)) + \
            "\n" + "\n".join(f"{c} " + str(row) for c, row in enumerate(self))

    def get_figure_position(self, figure: "Figure") -> Tuple[int, int]:
        """ Get position of given figure on table. """
        for count, row in enumerate(self):
            for count_2, column in enumerate(row):
                if figure == column:
                    return count, count_2
        raise MissingFigure("Given figure is not located in this table.")

    def get_figure(self, position: Tuple[int, int]) -> Optional["Figure"]:
        """ Get figure from table by its position. if there is no figure, returns None. """
        return self[position[0]][position[1]]

    def set_figure(self, figure: Optional["Figure"], position: Tuple[int, int]) -> None:
        """ Set Figure object or None on given position. """
        self[position[0]][position[1]] = figure

    @property
    def figures(self) -> List["Figure"]:
        """ Returns list of all figures from table. """
        if self._figures is None:
            self._figures = [column for row in self for column in row if isinstance(column, Figure)]
        return self._figures

    def reset(self) -> None:
        """ Resets all cashed values of table. """
        self._figures = None

    def delete_all_figures(self) -> None:
        """ Change all figures on table to Nones. """
        for i in self.figures:
            self.set_figure(None, i.position)
        self.reset()


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
        """ Set this player as owner of figure. """
        figure.player = self

    def move(self, _from: Tuple[int, int], to: Tuple[int, int]) -> None:
        """ Moves some of owned figures from "_from" to "to" position on Table square.
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
            return [figure for figure in self.table.figures if figure.player == self]
        return self._figures

    def reset(self) -> None:
        """ Resets all cashed values of player and table. """
        self._figures = None
        self.table.reset()


class Figure(ABC):
    def __init__(self, table: Table, player: Player) -> None:
        """ Base abstract class for all chess Figures. """
        self.table = table
        self._player = player
        self._position: Optional[Tuple[int, int]] = None
        self._available_moves: Optional[Set[Tuple[int, int]]] = None

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
        """ Returns position of this figure on table. """
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
        self.reset()
        self.table.set_figure(self, to)
        self.player.reset()

    def move_validity(self, to: Tuple[int, int]) -> bool:
        """ Judges is move from current position to given is valid for this figure. """
        return to in self.available_moves

    @property
    @abstractmethod
    def available_moves(self) -> Set[Tuple[int, int]]:
        """ Return set of all table positions on which this figure is can be moved. """
        if self._available_moves is None:
            ...  # get available moves
        return self._available_moves

    def __repr__(self) -> str:
        return f"{self.__class__.__name__[:2]}-{self.player.name[0]}"

    def reset(self) -> None:
        """ Resets all cashed values of figure. """
        self._position = None
        self._available_moves = None
