from typing import List, Tuple, Set, Callable, Iterable

from base import Figure, Player, Table


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


class Pawn(Figure):
    def __init__(self, table: Table, player: Player) -> None:
        super().__init__(table, player)
        self.first_move = True

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
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

            straight_moves = [i for i in straight_moves if i[0] < self.table.rows and i[1] < self.table.columns]
            oblique_moves = [i for i in oblique_moves if i[0] < self.table.rows and i[1] < self.table.columns]

            for f in other_figures:
                try:
                    straight_moves.remove(f.position)
                except ValueError:
                    pass

            oblique_moves = [i for i in oblique_moves if self.table.get_figure(i) is not None
                             and self.table.get_figure(i).player != self.player]

            self._available_moves = set()
            self._available_moves.update(straight_moves, oblique_moves)

        return self._available_moves

    def move(self, to: Tuple[int, int]) -> None:
        super().move(to)
        self.first_move = False
        self.table.set_figure(self, to)


class Rook(Figure):
    def _straight_moves(self) -> tuple:
        current_position = self.position
        other_figures = self.table.figures

        up = cut_before([(r, current_position[1]) for r in range(0, current_position[0])],
                        other_figures, self.player)
        down = cut_after([(r, current_position[1]) for r in range(current_position[0] + 1, self.table.rows)],
                         other_figures, self.player)
        left = cut_before([(current_position[0], c) for c in range(0, current_position[1])],
                          other_figures, self.player)
        right = cut_after([(current_position[0], c) for c in range(current_position[1] + 1, self.table.columns)],
                          other_figures, self.player)

        return up, down, left, right

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            self._available_moves = set()
            self._available_moves.update(*self._straight_moves())
        return self._available_moves


class Bishop(Figure):
    def _oblique_moves(self) -> tuple:
        current_position = self.position
        other_figures = self.table.figures

        left_up, n = [], 1
        while min(current_position[0] - n, current_position[1] - n) >= 0:
            left_up.append((current_position[0] - n, current_position[1] - n))
            n += 1
        left_up = cut_after(left_up, other_figures, self.player)

        left_down, n = [], 1
        while current_position[0] + n < self.table.rows and current_position[1] - n >= 0:
            left_down.append((current_position[0] + n, current_position[1] - n))
            n += 1
        left_down = cut_after(left_down, other_figures, self.player)

        right_up, n = [], 1
        while current_position[0] - n >= 0 and current_position[1] + n < self.table.columns:
            right_up.append((current_position[0] - n, current_position[1] + n))
            n += 1
        right_up = cut_after(right_up, other_figures, self.player)

        right_down, n = [], 1
        while max(current_position[0] + n, current_position[1] + n) < min(self.table.rows, self.table.columns):
            right_down.append((current_position[0] + n, current_position[1] + n))
            n += 1
        right_down = cut_after(right_down, other_figures, self.player)

        return left_up, left_down, right_up, right_down

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            self._available_moves = set()
            self._available_moves.update(*self._oblique_moves())

        return self._available_moves


class Queen(Rook, Bishop):
    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        """Return set of all positions on which this queen can move. """
        if self._available_moves is None:
            self._available_moves = set()
            self._available_moves.update(*self._straight_moves(), *self._oblique_moves())

        return self._available_moves


class Knight(Figure):
    def _validate_moves(self, moves: Iterable[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        if self._available_moves is None:
            current_position = self.position
            other_figures = self.table.figures
            other_positions = [i.position for i in self.table.figures]
            self._available_moves = set()

            for i in moves:
                move = (current_position[0] + i[0], current_position[1] + i[1])
                if 0 <= move[0] <= self.table.rows and 0 <= move[1] <= self.table.columns:
                    if move not in other_positions or self.player != other_figures[other_positions.index(move)].player:
                        self._available_moves.add(move)

        return self._available_moves

    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        self._validate_moves([(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)])
        return self._available_moves


class King(Knight):
    @property
    def available_moves(self) -> Set[Tuple[int, int]]:
        self._validate_moves([(0, 1), (1, 0), (0, -1), (-1, 0), (1, -1), (-1, 1), (1, 1), (-1, -1)])
        return self._available_moves
