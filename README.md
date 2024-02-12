# Console-Chess
My implementation of chess game which can be played through console.
Run main.py or Menu.start() to start application.


## Overview:
  - ### console_chess.base:
      Containing classes Table, Player, Figure and exception classes.
  - ### console_chess.figures:
      Containing figures classes Pawn, Rook, Bishop, Knight, Queen, king and some functions for them.
  - ### console_chess.bot:
      Containing Bot, EasyBot, NormalBot, HardBot and some functions for them.
  - ### console_chess.game:
      Containing Difficulty, ChessSet, Game, PvP, PvC, CvC and Menu.


## Instruction:
  - The Table contains Figure objects in certain positions inside. 
  - Figures are a Figure subclasses, which have their unique rules by which their moves are validated.
  - figures are owned by some Players, which can move their figures from one position on table to another using Player.move() method.
  - Player and Figure moves must be valid from chess rules perspective, or else it will raise exception.
  - Bots are subclasses of Player, which can make moves by themselves using Bot.auto_move() method.
  - PvP, PvC and CvC are subclasses of a Game, which performs turn-based gameplay of chess through console.  Use .play() method to start the game.
  - The Menu provides interface to choose game mode and difficulty. Run Menu.start() to start a menu.


## Requirements:
- ### OS:
  - No OS specific tools were used, so it should work anywhere Python runs.
- ### Python interpreter version:
  - 3.10
- ### Third party packages:
  - pytest==8.0.0 (Only for tests, so most of the code can be used without it.)
