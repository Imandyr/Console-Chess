from typing import List, Tuple, Set, Callable, Iterable

from .base import Figure, Player, Table


def ignore_v_e(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        output = None
        try:
            output = func(*args, **kwargs)
        except ValueError:
            pass
        return output
    return wrapper


def cut_before(f: List[Tuple[int, int]], t: List[Figure], p: Player) -> list:
    for i in t:
        try:
            s = f.index(i.position)
        except ValueError:
            pass
        else:
            if p == i.player:
                f = f[s + 1:]
            else:
                f = f[s:]
    return f


def cut_after(f: List[Tuple[int, int]], t: List[Figure], p: Player) -> list:
    for i in t:
        try:
            s = f.index(i.position)
        except ValueError:
            pass
        else:
            if p == i.player:
                f = f[:s]
            else:
                f = f[:s + 1]
    return f


def cut_before_ignore_player(f: List[Tuple[int, int]], t: List[Figure], *args, **kwargs) -> list:
    for i in t:
        try:
            s = f.index(i.position)
            f = f[s:]
        except ValueError:
            pass
    return f


def cut_after_ignore_player(f: List[Tuple[int, int]], t: List[Figure], *args, **kwargs) -> list:
    for i in t:
        try:
            s = f.index(i.position)
            f = f[:s + 1]
        except ValueError:
            pass
    return f


class Pawn(Figure):
    cost = 1

    def __init__(self, table: Table, player: Player) -> None:
        super().__init__(table, player)
        self.first_move = True

    def _base_available_moves(self) -> tuple[list, list]:
        current_position = self.position
        other_figures = self.table.figures

        if self.player.goes_up:
            straight_moves = [(current_position[0] - 1, current_position[1])]
            if self.first_move:
                straight_moves.append((current_position[0] - 2, current_position[1]))
            oblique_moves = [(current_position[0] - 1, current_position[1] + 1),
                             (current_position[0] - 1, current_position[1] - 1)]
        else:
            straight_moves = [(current_position[0] + 1, current_position[1])]
            if self.first_move:
                straight_moves.append((current_position[0] + 2, current_position[1]))
            oblique_moves = [(current_position[0] + 1, current_position[1] + 1),
                             (current_position[0] + 1, current_position[1] - 1)]

        bound = lambda x: [i for i in x if self.table.rows > i[0] >= 0 and self.table.columns > i[1] >= 0]
        straight_moves = bound(straight_moves)
        oblique_moves = bound(oblique_moves)

        for f in other_figures:
            if straight_moves[0] == f.position:
                straight_moves = []
                break
            try:
                straight_moves.remove(f.position)
            except ValueError:
                pass

        return straight_moves, oblique_moves

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            straight_moves, oblique_moves = self._base_available_moves()

            oblique_moves = [i for i in oblique_moves if self.table.get_figure(i) is not None
                             and self.table.get_figure(i).player != self.player]

            self._available_moves = set()
            self._available_moves.update(straight_moves, oblique_moves)

        return self._available_moves

    @property
    def available_moves_ignore_ownership(self) -> Set[Tuple[int, int]]:
        """ Returns set of all table positions on which this figure is can be moved,
        but all other figures are considered as an enemy, even if they owned by the same player.
        Also returns oblique moves for pawns even if no figures are located on those positions. """
        if self._available_moves_ignore_ownership is None:
            self._available_moves_ignore_ownership = set()
            self._available_moves_ignore_ownership.update(*self._base_available_moves())

        return self._available_moves_ignore_ownership

    def move(self, to: Tuple[int, int]) -> None:
        super().move(to)
        self.first_move = False
        self.table.set_figure(self, to)


class Rook(Figure):
    cost = 4

    def _straight_moves(self, before: Callable = cut_before, after: Callable = cut_after) -> tuple:
        current_position = self.position
        other_figures = self.table.figures

        up = before([(r, current_position[1]) for r in range(0, current_position[0])],
                    other_figures, self.player)
        down = after([(r, current_position[1]) for r in range(current_position[0] + 1, self.table.rows)],
                     other_figures, self.player)
        left = before([(current_position[0], c) for c in range(0, current_position[1])],
                      other_figures, self.player)
        right = after([(current_position[0], c) for c in range(current_position[1] + 1, self.table.columns)],
                      other_figures, self.player)

        return up, down, left, right

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            self._available_moves = set()
            self._available_moves.update(*self._straight_moves())
        return self._available_moves

    @property
    def available_moves_ignore_ownership(self) -> Set[Tuple[int, int]]:
        if self._available_moves_ignore_ownership is None:
            self._available_moves_ignore_ownership = set()
            self._available_moves_ignore_ownership.update(*self._straight_moves(cut_before_ignore_player,
                                                                                cut_after_ignore_player))
        return self._available_moves_ignore_ownership


class Bishop(Figure):
    cost = 3

    def _oblique_moves(self, after: Callable = cut_after) -> tuple:
        current_position = self.position
        other_figures = self.table.figures

        left_up, n = [], 1
        while min(current_position[0] - n, current_position[1] - n) >= 0:
            left_up.append((current_position[0] - n, current_position[1] - n))
            n += 1
        left_up = after(left_up, other_figures, self.player)

        left_down, n = [], 1
        while current_position[0] + n < self.table.rows and current_position[1] - n >= 0:
            left_down.append((current_position[0] + n, current_position[1] - n))
            n += 1
        left_down = after(left_down, other_figures, self.player)

        right_up, n = [], 1
        while current_position[0] - n >= 0 and current_position[1] + n < self.table.columns:
            right_up.append((current_position[0] - n, current_position[1] + n))
            n += 1
        right_up = after(right_up, other_figures, self.player)

        right_down, n = [], 1
        while max(current_position[0] + n, current_position[1] + n) < min(self.table.rows, self.table.columns):
            right_down.append((current_position[0] + n, current_position[1] + n))
            n += 1
        right_down = after(right_down, other_figures, self.player)

        return left_up, left_down, right_up, right_down

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            self._available_moves = set()
            self._available_moves.update(*self._oblique_moves())

        return self._available_moves

    @property
    def available_moves_ignore_ownership(self) -> Set[Tuple[int, int]]:
        if self._available_moves_ignore_ownership is None:
            self._available_moves_ignore_ownership = set()
            self._available_moves_ignore_ownership.update(*self._oblique_moves(cut_after_ignore_player))
        return self._available_moves_ignore_ownership


class Queen(Rook, Bishop):
    cost = 7

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            self._available_moves = set()
            self._available_moves.update(*self._straight_moves(), *self._oblique_moves())

        return self._available_moves

    @property
    def available_moves_ignore_ownership(self) -> Set[Tuple[int, int]]:
        if self._available_moves_ignore_ownership is None:
            self._available_moves_ignore_ownership = set()
            self._available_moves_ignore_ownership.update(*self._straight_moves(cut_before_ignore_player,
                                                                                cut_after_ignore_player),
                                                          *self._oblique_moves(cut_after_ignore_player))
        return self._available_moves_ignore_ownership


class Knight(Figure):
    cost = 3

    def _validate_moves(self, moves: Iterable[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        current_position = self.position
        other_figures = self.table.figures
        other_positions = [i.position for i in self.table.figures]
        self._available_moves = set()

        for i in moves:
            move = (current_position[0] + i[0], current_position[1] + i[1])
            if 0 <= move[0] < self.table.rows and 0 <= move[1] < self.table.columns:
                if move not in other_positions or self.player != other_figures[other_positions.index(move)].player:
                    self._available_moves.add(move)

        return self._available_moves

    def _validate_moves_ignore_ownership(self, moves: Iterable[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        current_position = self.position
        self._available_moves = set()

        for i in moves:
            move = (current_position[0] + i[0], current_position[1] + i[1])
            if 0 <= move[0] < self.table.rows and 0 <= move[1] < self.table.columns:
                self._available_moves.add(move)

        return self._available_moves

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            self._available_moves = self._validate_moves([(2, 1), (2, -1), (-2, 1), (-2, -1),
                                                          (1, 2), (1, -2), (-1, 2), (-1, -2)])
        return self._available_moves

    @property
    def available_moves_ignore_ownership(self) -> Set[Tuple[int, int]]:
        if self._available_moves_ignore_ownership is None:
            self._available_moves_ignore_ownership = self._validate_moves_ignore_ownership(
                [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
            )
        return self._available_moves_ignore_ownership


class King(Knight):
    cost = 15

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            self._available_moves = self._validate_moves([(0, 1), (1, 0), (0, -1), (-1, 0),
                                                          (1, -1), (-1, 1), (1, 1), (-1, -1)])
        return self._available_moves

    @property
    def available_moves_ignore_ownership(self) -> Set[Tuple[int, int]]:
        if self._available_moves_ignore_ownership is None:
            self._available_moves_ignore_ownership = self._validate_moves_ignore_ownership(
                [(0, 1), (1, 0), (0, -1), (-1, 0), (1, -1), (-1, 1), (1, 1), (-1, -1)]
            )
        return self._available_moves_ignore_ownership
