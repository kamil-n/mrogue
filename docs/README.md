# MRogue
A generic roguelike template in Python.

### Description
This is an exercise in coding a turn-based game with text representation.
A Python port of libTCOD by [HexDecimal](https://github.com/HexDecimal) is used. Besides that only Numpy is required.

##### Goal
The aim of this project is two-fold: to learn and apply Python techniques, and to create a Minimum Viable Product for a
Rogue-like game which can be later extended and turned into an original experience and full feature game.

##### History
I have started working on a roguelike engine several years ago in ANSI C using ncurses. As I was learning and trying
different languages, this work was ported to C++ then Java and finally Python. It can still feel ancient in places or have
non-pythonic solutions and paradigms implemented. The code is constantly being rewritten and development is slow
because of other hobbies and interests taking up my free time.

### Features
Flow of the game is organised into turns, with player taking 1 turn to perform an action, and monsters performing their
actions all at once immediately after. Player can use items to fight monsters and reach the last level of the dungeon.
Available keyboard shortcuts are listed in the game's interface - displayed by pressing Shift+H.

### Instructions
`git clone git@github.com:kamil-n/mrogue.git`

`cd rogue`

`python3 -m venv ./venv`

`. venv/bin/activate`

`pip install numpy tcod`

`python3 rogue.py`

Release builds should also be available.

### License
*This program uses HexDecimal's "python-tcod" licensed under Simplified 2-clause FreeBSD license.*

Copyright (C) 2018-2022 Kamil Nienałtowski

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
