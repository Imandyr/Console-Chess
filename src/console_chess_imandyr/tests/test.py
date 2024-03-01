from typing import cast
import pytest

from ..figures import Pawn, Rook, Bishop, Knight, Queen, King
from ..game import Game, Menu, PvP, PvC, ChessSet
from ..base import Player, Figure, Table, InvalidMove
from ..bot import Bot, EasyBot, get_all_items_with_highest_value, NormalBot, HardBot


class TestsOfGameRun:
    def test_menu(self):
        with pytest.raises(OSError):
            Menu.start()

    def test_pvp(self):
        with pytest.raises(OSError):
            PvP().play()

    def test_pvc(self):
        with pytest.raises(OSError):
            PvC().play()

    def test_game(self):
        with pytest.raises(TypeError):
            Game().play()


def test_chess_set() -> None:
    table = Table()
    chess_set = ChessSet(table)
    assert chess_set.table == table
    assert chess_set.player_1.table == table, chess_set.player_2.table == table


def test_pvc_promotion() -> None:
    pvc = PvC()
    pvc.table.set_figure(Pawn(pvc.table, pvc.player_2), (7, 0))
    pvc.check_for_promotions(pvc.player_2)
    f = pvc.table.get_figure((7, 0))
    assert isinstance(f, Queen)
    assert f.player == pvc.player_2


class DummyGame(Game):
    def _turn(self, player: Player) -> Player:
        return super()._turn(player)


@pytest.fixture
def filled_game() -> DummyGame:
    g = DummyGame()
    g.fill_table()
    return g


def test_player_available_figures(filled_game: DummyGame) -> None:
    assert filled_game.player_1.figures == [figure for figure in filled_game.table.figures
                                            if figure.player == filled_game.player_1]
    assert filled_game.player_1.figures != [figure for figure in filled_game.table.figures
                                            if figure.player == filled_game.player_2]


def test_figures_cost() -> None:
    assert Figure.cost == 0
    assert isinstance(Pawn.cost, int)
    assert isinstance(Rook.cost, int)
    assert isinstance(Knight.cost, int)
    assert isinstance(Bishop.cost, int)
    assert isinstance(Queen.cost, int)
    assert isinstance(King.cost, int)


@pytest.fixture
def table_player_easybot() -> tuple[Table, Player, Bot]:
    t = Table()
    p = Player(t, True, "White")
    b = EasyBot(t, False, "Black(bot)")
    return t, p, b


def test_easy_bot_auto_move(table_player_easybot) -> None:
    """ Bot should move his queen to player's queen on position (6, 1). """
    t, p, b = table_player_easybot
    t.set_figure(Queen(t, p), (6, 1))
    t.set_figure(Queen(t, p), (6, 2))
    t.set_figure(Queen(t, b), (4, 1))
    b.auto_move()
    assert t.get_figure((6, 1)).player == b


def test_easy_bot_auto_move_2(table_player_easybot) -> None:
    """ Bot should not move pawn 2 squares down if there is a player's figure, because its against the chess rules. """
    t, p, b = table_player_easybot
    p_b = Pawn(t, b)
    p_p = Pawn(t, p)
    t.set_figure(p_b, (1, 0))
    t.set_figure(p_p, (3, 0))
    b.auto_move()
    assert t.get_figure((1, 0)) is None
    assert t.get_figure((2, 0)) == p_b
    assert t.get_figure((3, 0)) == p_p


def test_get_all_items_with_highest_value():
    assert get_all_items_with_highest_value([("a", 1), ("b", 3), ("c", 2), ("d", 3)], 1) == [("b", 3), ("d", 3)]


class TestsEasyBotChoices:
    """ Tests for EasyBot which should check what choices he makes. """

    def test_1(self, table_player_easybot) -> None:
        """ Should choose to kill Bishop over Pawn, because Bishop is worth more. """
        t, p, b = table_player_easybot
        t.set_figure(Rook(t, b), (4, 4))
        t.set_figure(Pawn(t, p), (5, 4))
        t.set_figure(Bishop(t, p), (3, 4))
        b.auto_move()
        assert t.get_figure((3, 4)).player == b

    def test_2(self, table_player_easybot) -> None:
        """ Should choose to kill enemy pawn over None, because Pawn is worth more than None. """
        t, p, b = table_player_easybot
        t.set_figure(Pawn(t, b), (4, 4))
        t.set_figure(Pawn(t, p), (5, 3))
        b.auto_move()
        assert t.get_figure((5, 3)).player == b

    def test_3(self, table_player_easybot) -> None:
        """ Should choose to kill enemy queen over knight, because queen is worth more than knight. """
        t, p, b = table_player_easybot
        t.set_figure(Bishop(t, b), (4, 4))
        t.set_figure(Knight(t, p), (2, 2))
        t.set_figure(Queen(t, p), (1, 7))
        b.auto_move()
        assert t.get_figure((1, 7)).player == b

    def test_4(self, table_player_easybot) -> None:
        """ Should choose to kill enemy king over queen, because king is worth more than queen. """
        t, p, b = table_player_easybot
        t.set_figure(Queen(t, b), (2, 7))
        t.set_figure(King(t, p), (7, 7))
        t.set_figure(Queen(t, p), (2, 6))
        b.auto_move()
        assert t.get_figure((7, 7)).player == b


@pytest.fixture
def table_player_normal_bot() -> tuple[Table, Player, Bot]:
    t = Table()
    p = Player(t, True, "White")
    b = NormalBot(t, False, "Black(bot)")
    return t, p, b


class TestsNormalBotChoices:
    """ Tests of NormalBot behavior in different game situations. """

    def test_1(self, table_player_normal_bot) -> None:
        """ Bot shouldn't step on the enemy's pawn, because then he will lose rook, so it's not worth it. """
        t, p, b = table_player_normal_bot
        t.set_figure(Rook(t, b), (4, 4))
        t.set_figure(Pawn(t, p), (2, 4))
        t.set_figure((Bishop(t, p)), (1, 5))
        b.auto_move()
        assert t.get_figure((2, 4)).player != b

    def test_2(self, table_player_normal_bot) -> None:
        """ Bot should step on the enemy's queen, because it still wirth it,
        even if he loses his rook after this. """
        t, p, b = table_player_normal_bot
        t.set_figure(Rook(t, b), (4, 4))
        t.set_figure(Queen(t, p), (2, 4))
        t.set_figure((Bishop(t, p)), (1, 5))
        b.auto_move()
        assert t.get_figure((2, 4)).player == b


@pytest.fixture
def table_player_player() -> tuple[Table, Player, Player]:
    t = Table()
    p1 = Player(t, True, "White")
    p2 = Player(t, False, "Black")
    return t, p1, p2


@pytest.fixture
def table_player_player_pawn(table_player_player) -> tuple[Table, Player, Player, Pawn]:
    t, p1, p2 = table_player_player
    pa = Pawn(t, p1)
    t.set_figure(pa, (5, 2))
    t.set_figure(Rook(t, p1), (4, 2))
    t.set_figure(Rook(t, p2), (3, 2))
    t.set_figure(Rook(t, p1), (4, 3))
    t.set_figure(Rook(t, p2), (4, 1))
    return t, p1, p2, pa


class TestsOfPawn:
    def test_1(self, table_player_player_pawn) -> None:
        t, p1, p2, pa = table_player_player_pawn
        assert pa.available_moves == {(4, 1)}

    def test_2(self, table_player_player_pawn) -> None:
        t, p1, p2, pa = table_player_player_pawn
        assert pa.available_moves_ignore_ownership == {(4, 1), (4, 3)}

    def test_3(self, table_player_player) -> None:
        t, p1, p2 = table_player_player
        pa = Pawn(t, p2)
        t.set_figure(pa, (1, 2))
        t.set_figure(Queen(t, p1), (2, 2))
        print(t)
        print(pa.available_moves)

        assert len(pa.available_moves) == 0

    def test_4(self, table_player_player) -> None:
        t, p1, p2 = table_player_player
        pa = Pawn(t, p1)
        t.set_figure(pa, (1, 2))
        assert pa.available_moves == {(0, 2)}


@pytest.fixture
def fully_surrounded(table_player_player) -> tuple[Table, Player, Player, tuple[int, int]]:
    t, p1, p2 = table_player_player
    t.set_figure(Pawn(t, p1), (4, 2))
    t.set_figure(Pawn(t, p2), (6, 2))
    t.set_figure(Pawn(t, p1), (5, 3))
    t.set_figure(Pawn(t, p2), (5, 1))
    t.set_figure(Pawn(t, p1), (3, 2))
    t.set_figure(Pawn(t, p2), (4, 3))
    t.set_figure(Pawn(t, p1), (6, 3))
    t.set_figure(Pawn(t, p2), (4, 1))
    t.set_figure(Pawn(t, p1), (4, 3))
    return t, p1, p2, (5, 2)


@pytest.fixture
def table_player_player_rook(fully_surrounded) -> tuple[Table, Player, Player, Rook]:
    t, p1, p2, position = fully_surrounded
    r = Rook(t, p1)
    t.set_figure(r, position)
    return t, p1, p2, r


class TestsOfRook:
    def test_1(self, table_player_player_rook) -> None:
        t, p1, p2, r = table_player_player_rook
        assert r.available_moves == {(6, 2), (5, 1)}

    def test_2(self, table_player_player_rook) -> None:
        t, p1, p2, r = table_player_player_rook
        assert r.available_moves_ignore_ownership == {(6, 2), (5, 1), (4, 2), (5, 3)}


@pytest.fixture
def table_player_player_knight(table_player_player) -> tuple[Table, Player, Player, Knight]:
    t, p1, p2 = table_player_player
    f = Knight(t, p1)
    t.set_figure(f, (4, 4))
    t.set_figure(Pawn(t, p1), (2, 3))
    t.set_figure(Pawn(t, p2), (6, 3))
    t.set_figure(Pawn(t, p1), (3, 6))
    t.set_figure(Pawn(t, p2), (3, 2))
    t.set_figure(Pawn(t, p1), (5, 5))
    t.set_figure(Pawn(t, p2), (5, 4))
    return t, p1, p2, f


class TestsOfKnight:
    def test_1(self, table_player_player_knight) -> None:
        t, p1, p2, f = table_player_player_knight
        assert f.available_moves == {(6, 3), (6, 5), (2, 5), (5, 6), (3, 2), (5, 2)}

    def test_2(self, table_player_player_knight) -> None:
        t, p1, p2, f = table_player_player_knight
        assert f.available_moves_ignore_ownership == {(3, 6), (2, 3), (6, 3), (6, 5), (2, 5), (5, 6), (3, 2), (5, 2)}


@pytest.fixture
def table_player_player_pawns(table_player_player) -> tuple[Table, Player, Player]:
    t, p1, p2 = table_player_player
    t.set_figure(Pawn(t, p1), (2, 3))
    t.set_figure(Pawn(t, p2), (6, 3))
    t.set_figure(Pawn(t, p1), (3, 6))
    t.set_figure(Pawn(t, p2), (3, 2))
    t.set_figure(Pawn(t, p1), (5, 5))
    t.set_figure(Pawn(t, p2), (5, 4))
    t.set_figure(Pawn(t, p1), (7, 1))
    t.set_figure(Pawn(t, p2), (2, 2))
    return t, p1, p2


@pytest.fixture
def table_player_player_bishop(table_player_player_pawns) -> tuple[Table, Player, Player, Bishop]:
    t, p1, p2 = table_player_player_pawns
    f = Bishop(t, p1)
    t.set_figure(f, (4, 4))
    return t, p1, p2, f


class TestsOfBishop:
    def test_1(self, table_player_player_bishop) -> None:
        t, p1, p2, f = table_player_player_bishop
        assert f.available_moves == {(6, 2), (1, 7), (3, 3), (2, 6), (2, 2), (5, 3), (3, 5)}

    def test_2(self, table_player_player_bishop) -> None:
        t, p1, p2, f = table_player_player_bishop
        assert f.available_moves_ignore_ownership == {(7, 1), (5, 5), (6, 2), (1, 7),
                                                      (3, 3), (2, 6), (2, 2), (5, 3), (3, 5)}


@pytest.fixture
def table_player_player_queen(table_player_player_pawns) -> tuple[Table, Player, Player, Queen]:
    t, p1, p2 = table_player_player_pawns
    f = Queen(t, p1)
    t.set_figure(f, (4, 4))
    t.set_figure(Pawn(t, p1), (4, 7))
    return t, p1, p2, f


class TestsOfQueen:
    def test_1(self, table_player_player_queen) -> None:
        t, p1, p2, f = table_player_player_queen
        assert f.available_moves == {(0, 4), (1, 4), (1, 7), (2, 2), (2, 4), (2, 6), (3, 3), (3, 4), (3, 5), (4, 0),
                                     (4, 1), (4, 2), (4, 3), (4, 5), (4, 6), (5, 3), (5, 4), (6, 2)}

    def test_2(self, table_player_player_queen) -> None:
        t, p1, p2, f = table_player_player_queen
        assert f.available_moves_ignore_ownership == {(5, 5), (7, 1), (4, 7), (0, 4), (1, 4), (1, 7), (2, 2), (2, 4),
                                                      (2, 6), (3, 3), (3, 4), (3, 5), (4, 0), (4, 1), (4, 2), (4, 3),
                                                      (4, 5), (4, 6), (5, 3), (5, 4), (6, 2)}


@pytest.fixture
def table_player_player_king(table_player_player_pawns) -> tuple[Table, Player, Player, King]:
    t, p1, p2 = table_player_player_pawns
    f = King(t, p1)
    t.set_figure(f, (4, 4))
    t.set_figure(Pawn(t, p1), (4, 5))
    return t, p1, p2, f


class TestsOfKing:
    def test_1(self, table_player_player_king) -> None:
        t, p1, p2, f = table_player_player_king
        assert f.available_moves == {(3, 4), (4, 3), (5, 4), (3, 3), (5, 3), (3, 5)}

    def test_2(self, table_player_player_king) -> None:
        t, p1, p2, f = table_player_player_king
        assert f.available_moves_ignore_ownership == {(5, 5), (4, 5), (3, 4), (4, 3), (5, 4), (3, 3), (5, 3), (3, 5)}


class TestsOfTable:
    def test_of_players(self, table_player_player_king) -> None:
        t, p1, p2, k = table_player_player_king
        p = list({p1, p2})
        p.sort(key=lambda x: x.name)
        p1, p2 = p
        s_p = list(t.players)
        s_p.sort(key=lambda x: x.name)
        s_p1, s_p2 = s_p
        assert p1.name == s_p1.name
        assert p2.name == s_p2.name

    def test_of_table_full_copy_1(self, table_player_player_king) -> None:
        t, p1, p2, k = table_player_player_king
        p = list({p1, p2})
        p.sort(key=lambda x: x.name)
        p1, p2 = p

        c_t, c_p = t.full_copy()
        c_p = list(c_p)
        c_p.sort(key=lambda x: x.name)
        c_p1, c_p2 = c_p
        c_t = cast(Table, c_t)

        assert p1.name == c_p1.name and p1 is not c_p1 and p2.name == c_p2.name and p2 is not c_p2
        assert [f.available_moves for f in t.figures] == [f.available_moves for f in c_t.figures]
        assert t.figures != c_t.figures

    def test_of_table_full_copy_2(self) -> None:
        t = Table()
        n_t, p = t.full_copy()
        assert len(n_t.figures) == 0
        assert len(p) == 0


def test_of_player_find_copy(table_player_player_king) -> None:
    t, p1, p2, k = table_player_player_king
    n_t, n_p = t.full_copy()
    n_p1 = p1.find_copy_of_yourself(n_p)
    assert p1.name == n_p1.name


@pytest.fixture
def table_player_hard_bot() -> tuple[Table, Player, HardBot]:
    t = Table()
    return t, Player(t, False, "Black"), HardBot(t, True, "White(bot)")


@pytest.fixture
def table_player_hard_bot_filled_1(table_player_hard_bot) -> tuple[Table, Player, HardBot]:
    t, p, b = table_player_hard_bot
    t.set_figure(Pawn(t, p), (1, 2))
    t.set_figure(King(t, b), (2, 3))
    t.set_figure(Bishop(t, p), (5, 6))
    t.set_figure(Rook(t, b), (4, 6))
    return t, p, b


class TestsOfHardBot:
    def test_value_of_move(self, table_player_hard_bot_filled_1) -> None:
        t, p, b = table_player_hard_bot_filled_1
        assert b.value_of_move((4, 6), (5, 6)) == (Bishop.cost, -King.cost)

    def test_available_moves_costs(self, table_player_hard_bot_filled_1) -> None:
        """
        Bot can:
            1: Move his king from reach of enemy pawn and bishop, which will give him nothing.
            2: Kill an enemy pawn with his king and then lose his king to enemy's bishop.
            3: Move his king in reach of an enemy bishop, thus lose him.
            4: Kill an enemy bishop with his rook and then lose his king to enemy's pawn.

        So a set of costs should be equal to these four variants.
        """
        t, p, b = table_player_hard_bot_filled_1
        moves = b.available_moves_costs
        assert {move.cost for move in moves} == {Figure.cost, Pawn.cost - King.cost,
                                                 -King.cost, Bishop.cost - King.cost}

    def test_best_move(self, table_player_hard_bot_filled_1) -> None:
        """ The best you can do in this situation is to move your king from reach of all enemy's figures,
        so no one is loose anything. """
        t, p, b = table_player_hard_bot_filled_1
        assert b.best_move.cost == 0

    def test_best_move_auto_move(self, table_player_hard_bot_filled_1) -> None:
        t, p, b = table_player_hard_bot_filled_1
        b.auto_move()
        assert t.get_figure((1, 2)).player == p
        assert t.get_figure((5, 6)).player == p


class TestsOfResetOnMove:
    def test_of_reset_players_with_king_figure(self, table_player_player_king) -> None:
        t, p1, p2, k = table_player_player_king

        _, _, _, _, _ = k.available_moves_ignore_ownership, t.figures, t.players, p1.figures, p2.figures
        with pytest.raises(InvalidMove):
            k.move((-2, 2))

        assert (k._position is not None and k._available_moves is not None
                and k._available_moves_ignore_ownership is not None)
        assert t._figures is not None and t._players is not None
        assert p1._figures is not None and p2._figures is not None

        _, _, _, _, _ = k.available_moves_ignore_ownership, t.figures, t.players, p1.figures, p2.figures
        k.move((3, 3))

        assert k._position is None and k._available_moves is None and k._available_moves_ignore_ownership is None
        assert t._figures is None and t._players is None
        assert p1._figures is None and p2._figures is None

    def test_of_easy_bot(self, table_player_easybot) -> None:
        t, p, b = table_player_easybot
        r = Rook(t, b)
        t.set_figure(r, (2, 2))
        r.move((3, 2))
        assert b._available_moves_costs is None
        assert b._best_move is None

    def test_of_normal_bot(self, table_player_normal_bot) -> None:
        t, p, b = table_player_normal_bot
        q = Queen(t, b)
        t.set_figure(q, (2, 2))
        q.move((3, 2))
        assert b._available_moves_costs is None
        assert b._best_move is None

    def test_of_hard_bot(self, table_player_hard_bot) -> None:
        t, p, b = table_player_hard_bot
        k = Knight(t, b)
        t.set_figure(k, (2, 2))
        k.move((4, 3))
        assert b._available_moves_costs is None
        assert b._best_move is None


if __name__ == "__main__":
    pytest.main()
