from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, cast
from time import sleep
import enum
import re

from .base import InvalidMove, MissingFigure, AccessError, Player, Table, Figure
from .figures import Pawn, Rook, Bishop, Knight, Queen, King
from .bot import Bot, EasyBot, NormalBot, HardBot


class Difficulty(enum.Enum):
    """ Available bot player difficulties. """
    easy = "easy"
    normal = "normal"
    hard = "hard"


@dataclass
class ChessSet:
    """ Dataclass object which contains a table and two players. """
    table: Optional[Table] = None
    player_1: Optional[Player] = None
    player_2: Optional[Player] = None

    def __post_init__(self) -> None:
        self.table = self.table or Table(8, 8)
        self.player_1 = self.player_1 or Player(self.table, True, "White")
        self.player_2 = self.player_2 or Player(self.table, False, "Black")


class Game(ABC):
    input_pattern = re.compile(r"\D*(?P<row>\d)\D*(?P<column>\d)\D*")
    promotions = {"1": Queen, "2": Rook, "3": Bishop, "4": Knight}

    def __init__(self, player_1: Optional[Player] = None, player_2: Optional[Player] = None):
        """
        Chess game between two players.
        :param player_1: First player.
        :param player_2: Second player.
        """

        self.table = Table(8, 8)
        self.player_1 = player_1 or Player(self.table, True, "White")
        self.player_2 = player_2 or Player(self.table, False, "Black")

    def fill_table(self) -> None:
        """ Refill the table with a new standard set of figures for both players. """
        self.table.delete_all_figures()

        for i in range(8):
            self.table.set_figure(Pawn(self.table, player=self.player_1), (6, i))
            self.table.set_figure(Pawn(self.table, player=self.player_2), (1, i))

        for c, f in enumerate([Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]):
            self.table.set_figure(f(self.table, self.player_2), (0, c))
            self.table.set_figure(f(self.table, self.player_1), (7, c))

    def cleanse_table(self) -> None:
        """ Change all figures from table to Nones. """
        self.table.delete_all_figures()

    def opposite_player(self, player: Player) -> Player:
        """ Returns player which opposite to the given one. """
        if player == self.player_1:
            return self.player_2
        if player == self.player_2:
            return self.player_1

    def get_coordinates_input(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """ Takes move coordinates from standard console user input and returns it as tuple. """
        try:
            _from = self.input_pattern.match(input("from: ")).groupdict()
            to = self.input_pattern.match(input("to: ")).groupdict()
            return (int(_from["row"]), int(_from["column"])), (int(to["row"]), int(to["column"]))
        except (ValueError, AttributeError):
            raise ValueError("Invalid move input.")

    def promotion(self, figure: Figure) -> None:
        """ Promotes given figure to some high-rank figure. """
        print(f"{figure.__class__.__name__} on position {figure.position} is ready to be promoted. "
              "Write one key from the dictionary of available variants to make choice.\n"
              "Available variants: {'1': Queen, '2': Rook, '3': Bishop, '4': Knight}.")

        repeat = True
        while repeat:
            inp = input(f"Promote {figure.__class__.__name__} on position {figure.position} to: ")
            if inp not in self.promotions.keys():
                print("Invalid input.")
            else:
                self.table.set_figure(self.promotions[inp](self.table, figure.player), figure.position)
                repeat = False

        print(f"{figure.__class__.__name__} was successfully promoted.")

    def check_for_promotions(self, current_player: Player) -> None:
        """ Check if any figure of given player needs promotion and then promote if yes. """
        target_row = 0 if current_player.goes_up else 7
        for figure in current_player.figures:
            if figure.__class__ is Pawn and figure.position[0] == target_row:
                self.promotion(figure)

    def play(self) -> None:
        """ Perform gameplay. """
        self.fill_table()
        print(self.table)
        current_player: Player = self.player_1

        while any(isinstance(i, King) for i in self.player_1.figures) \
                and any(isinstance(i, King) for i in self.player_2.figures):
            current_player = self._turn(current_player)
            self.table.reset()

        if not any(isinstance(i, King) for i in self.player_1.figures):
            print(f"Player {self.player_2} killed king of player {self.player_1} and won the game.")
        else:
            print(f"Player {self.player_1} killed king of player {self.player_2} and won the game.")

    @abstractmethod
    def _turn(self, player: Player) -> Player:
        """ Performs one turn of the game and then returns player, which will make move on the next turn. """
        try:
            player.move(*self.get_coordinates_input())
            self.check_for_promotions(player)
            print(" --- Next turn --- \n" + str(self.table))
            return self.opposite_player(player)

        except (MissingFigure, AccessError, InvalidMove, ValueError) as err:
            print(err)
            return player


class PvP(Game):
    """ Chess game where two players make moves by turns. Can be played through console. """

    def play(self) -> None:
        """ Performs gameplay. """
        print(" --- The PvP chess game has begun --- ")
        super().play()
        print(" --- The PvP chess game is over --- ")

    def _turn(self, player: Player) -> Player:
        """ Performs one turn of the game and then returns player, which will make move on the next turn. """
        print(f"{player}'s move:")
        return super()._turn(player)


class PvC(Game):
    def __init__(self, difficulty: str = "easy",
                 player: Optional[Player] = None, bot: Optional[Bot] = None):
        """
        Chess game mode, in which player fights against a computer. Can be played through console.
        Notice: game difficulty fully depends on bot algorithm, so,
        if 'bot' argument is provided - difficulty value will do nothing.
        :param difficulty: Available game difficulties are 'easy', 'normal' and 'hard' (see Difficulty class).
        :param player: Custom player instead of automatically created one. Not recommended to use.
        :param bot: Custom bot instead of automatically created one. Not recommended to use.
        """
        super().__init__(player, bot)
        self.difficulty = Difficulty(difficulty).value

        if not bot:
            if self.difficulty == "easy":
                bot = EasyBot(self.table, False, "Black(bot)")
            elif self.difficulty == "normal":
                bot = NormalBot(self.table, False, "Black(bot)")
            else:
                bot = HardBot(self.table, False, "Black(bot)")

            self.player_2 = bot

    def promotion(self, figure: Figure) -> None:
        if isinstance(figure.player, Bot):
            self.table.set_figure(Queen(self.table, figure.player), figure.position)
            print(f"Player '{figure.player.name}' promoted his figure on position {figure.position} "
                  f"from {figure.__class__.__name__} to Queen.")
        else:
            super().promotion(figure)

    def play(self) -> None:
        """ Perform gameplay. """
        print(f" --- The PvC chess game with difficulty '{self.difficulty}' has begun --- ")
        super().play()
        print(f" --- The PvC chess game with difficulty '{self.difficulty}' is over --- ")

    def _turn(self, player: Player) -> Player:
        """ Performs one turn of the game and then returns player, which will make move on the next turn. """
        print(f"{player}'s move:")

        if player == self.player_1:
            return super()._turn(player)

        else:
            move = cast(Bot, player).best_move
            print(f"from: {str(move[0].position)[1:-1]}\nto: {str(move[1])[1:-1]}")
            move[0].move(move[1])
            self.check_for_promotions(player)
            print(" --- Next turn --- \n" + str(self.table))
            return self.player_1


class CvC(Game):
    def __init__(self, difficulty_1: str = "hard", difficulty_2: str = "hard", delay: float = 0.0,
                 bot_1: Optional[Bot] = None, bot_2: Optional[Bot] = None):
        """
        Chess game mode, in which two bots fight against each other. Can be played through console.
        Available bot difficulties for both bots are 'easy', 'normal' and 'hard' (see Difficulty class).
        Notice: game difficulty fully depends on bot algorithm, so,
        if bot argument is provided - difficulty value will do nothing.
        :param difficulty_1: String 'easy'|'normal'|'hard'
        :param difficulty_2: String 'easy'|'normal'|'hard'
        :param delay: Delay between moves in seconds.
        :param bot_1: Custom first bot instead of automatically created one. Not recommended to use.
        :param bot_2: Custom second bot instead of automatically created one. Not recommended to use.
        """
        super().__init__(bot_1, bot_2)
        self.difficulty_1 = Difficulty(difficulty_1).value
        self.difficulty_2 = Difficulty(difficulty_2).value
        self.delay = delay

        if not bot_1:
            if self.difficulty_1 == "easy":
                bot_1 = EasyBot(self.table, True, "White(EasyBot_1)")
            elif self.difficulty_1 == "normal":
                bot_1 = NormalBot(self.table, True, "White(NormalBot_1)")
            else:
                bot_1 = HardBot(self.table, True, "White(HardBot_1)")
            self.player_1 = bot_1

        if not bot_2:
            if self.difficulty_2 == "easy":
                bot_2 = EasyBot(self.table, False, "Black(EasyBot_2)")
            elif self.difficulty_2 == "normal":
                bot_2 = NormalBot(self.table, False, "Black(NormalBot_2)")
            else:
                bot_2 = HardBot(self.table, False, "Black(HardBot_2)")
            self.player_2 = bot_2

    def opposite_player(self, player: Bot) -> Bot:
        return cast(Bot, super().opposite_player(player))

    def promotion(self, figure: Figure) -> None:
        self.table.set_figure(Queen(self.table, figure.player), figure.position)
        print(f"Player '{figure.player.name}' promoted his figure on position {figure.position} "
              f"from {figure.__class__.__name__} to Queen.")

    def play(self) -> None:
        print(f" --- The CvC chess game with difficulties "
              f"'{self.difficulty_1}' and '{self.difficulty_2}' has begun --- ")
        super().play()
        print(f" --- The CvC chess game with difficulties "
              f"'{self.difficulty_1}' and '{self.difficulty_2}' is over --- ")

    def _turn(self, player: Bot) -> Bot:
        print(f"{player}'s move:")

        move = player.best_move
        print(f"from: {str(move[0].position)[1:-1]}\nto: {str(move[1])[1:-1]}")
        move[0].move(move[1])

        self.check_for_promotions(player)
        print(" --- Next turn --- \n" + str(self.table))
        sleep(self.delay)

        return self.opposite_player(player)


class Menu:
    """ Chess game which can be played through console. """
    difficulties_dict = {"1": "easy", "e": "easy", "easy": "easy",
                         "2": "normal", "n": "normal", "normal": "normal",
                         "3": "hard", "h": "hard", "hard": "hard"}
    delay_pattern = re.compile(r"^\d+(\.\d*)?$")

    @classmethod
    def start(cls) -> None:
        """ Method, which starts a chess game menu.
        In this menu, player can choose game mode, its difficulty and then play it. """

        print(
            "\nThe game of chess.\nGiven table coordinates should looks like '2 3' or '2,3', "
            "which will be interpreted as square on row number 2 and column number 3. Both indexes starts from 0.\n\n"
            "To play PvP (Player versus players), where two players makes moves by turns, write '1' or 'pvp'.\n"
            "To play PvC (Player versus Computer), where player fight against bot, write '2' or 'pvc'.\n"
            "To play CvC (Computer versus Computer), where two bots fight against each other, write '3' or 'cvc'.\n"
            "To quit this menu, write anything else then suggested above, or press ctrl+c key combination.\n"
        )

        inp = input("new game? {'1': 'pvp', '2': 'pvc', '3': 'cvc'}: ")
        if inp == "1" or inp == "pvp":
            PvP().play()

        elif inp == "2" or inp == "pvc":
            try:
                PvC(cls.difficulties_dict[input(f"choose bot difficultly: ")]).play()
            except KeyError:
                print(f"Invalid difficulty alias. Valid difficulty aliases: '{cls.difficulties_dict}'.")

        elif inp == "3" or "cvc":
            try:
                CvC(cls.difficulties_dict[input(f"choose first bot difficultly: ")],
                    cls.difficulties_dict[input(f"choose second bot difficultly: ")],
                    float(re.match(cls.delay_pattern, input(f"Delay (in seconds) between every turn: ")).string)
                    ).play()
            except KeyError:
                print(f"Invalid difficulty alias. Valid difficulty aliases: '{cls.difficulties_dict}'.")
            except AttributeError:
                print(f"Invalid delay value. RE pattern for this input: '{cls.delay_pattern.pattern}'.")

        else:
            print(f"Not valid game name, so quitting...")
            quit()
