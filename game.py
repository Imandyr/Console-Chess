from typing import Tuple, Optional, cast
import re

from base import InvalidMove, MissingFigure, AccessError, Player, Table
from figures import Pawn, Rook, Bishop, Knight, Queen, King


class Game:
    def __init__(self, player_1: Optional[Player] = None, player_2: Optional[Player] = None):
        """ Base of the chess game. """
        self.table = Table(8, 8)
        self.player_1 = player_1 or Player(self.table, True, "White")
        self.player_2 = player_2 or Player(self.table, False, "Black")

    def fill_table(self) -> None:
        """ Refill table with new standard set of figures for both players. """
        self.table.delete_all_figures()

        for i in range(8):
            self.table.set_figure(Pawn(self.table, player=self.player_1), (6, i))
            self.table.set_figure(Pawn(self.table, player=self.player_2), (1, i))

        for c, f in enumerate([Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]):
            self.table.set_figure(f(self.table, self.player_1), (7, c))
            self.table.set_figure(f(self.table, self.player_2), (0, c))

    def cleanse_table(self) -> None:
        """ Change all figures from table to Nones. """
        self.table.delete_all_figures()


class ConsoleChess(Game):
    def __init__(self, player_1: Optional[Player] = None, player_2: Optional[Player] = None):
        """ Chess game which can be played through console. """
        super().__init__(player_1, player_2)

    def _play(self) -> None:
        """ Perform gameplay. """
        self.fill_table()
        current_player: Player = self.player_1

        print(" --- The chess game has begun --- \n" + str(self.table))

        while any(isinstance(i, King) for i in self.player_1.figures) \
                and any(isinstance(i, King) for i in self.player_2.figures):
            current_player = self._turn(current_player)

        if not any(isinstance(i, King) for i in self.player_1.figures):
            print(f"Player {self.player_2} killed king of player {self.player_1} and won the game.")
        else:
            print(f"Player {self.player_1} killed king of player {self.player_2} and won the game.")

        print(" --- The chess game is over --- ")

    def _turn(self, player: Player) -> Player:
        """ One turn of game. Return player which should make move on next turn. """
        print(f"{player}'s move:")

        try:
            player.move(
                cast(Tuple[int, int], tuple([int(i) for i in re.search(r"[.\D]*(\d*)[.\D]*(\d*)",
                                                                       input("from: ")).groups()[:2]])),
                cast(Tuple[int, int], tuple([int(i) for i in re.search(r"[.\D]*(\d*)[.\D]*(\d*)",
                                                                       input("to: ")).groups()[:2]]))
            )
            print(" --- Next turn --- \n" + str(self.table))

            if self.player_1 == player:
                return self.player_2
            else:
                return self.player_1

        except (MissingFigure, AccessError, InvalidMove) as err:
            print(err)
            return player

        except ValueError:
            print("Invalid move input.")
            return player

    def start(self) -> None:
        """ Method which starts game of chess. """

        print(f"Game of chess. Move input square position should looks like '2, 3', "
              f"which can be interpreted as second row and third column. Both indexes starts from 0.")

        if input("Start new game? ('y'/'n'): ") == "y":
            self._play()
        else:
            print(f"Not 'y', so quitting...")
            quit()
