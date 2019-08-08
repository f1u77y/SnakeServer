import time
import random
import logging
import string
import threading

from collections import namedtuple, deque, defaultdict

DIRECTIONS = ('left', 'up', 'right', 'down')

Cell = namedtuple('Cell', ('x', 'y'))
Prize = namedtuple('Prize', ('cell', 'value'))


opposite_direction = {
    'left': 'right',
    'right': 'left',
    'up': 'down',
    'down': 'up',
}


def move_cell(c, direction):
    if direction == 'left':
        return Cell(c.x, c.y - 1)
    elif direction == 'right':
        return Cell(c.x, c.y + 1)
    elif direction == 'up':
        return Cell(c.x - 1, c.y)
    elif direction == 'down':
        return Cell(c.x + 1, c.y)
    else:
        return c


class NonZeroDefaultDict(defaultdict):
    def __init__(self, *args, **kwargs):
        zero = kwargs.pop('zero', 0)
        super().__init__(*args, **kwargs)
        self._zero = zero

    def __setitem__(self, key, value):
        # Allow creating item with value = zero but disallow changing existing item to zero
        # This code proves there is a bug in author's genetic code
        if value == self._zero and key in self:
            del self[key]
        else:
            super().__setitem__(key, value)


class Player(object):
    def __init__(self, game, cell, direction, interactor):
        self._game = game
        self.cells = deque((cell,))
        self.direction = direction
        self.interactor = interactor
        self.symbol = random.choice(string.ascii_lowercase)

    def set_direction(self, direction):
        if direction not in opposite_direction or direction == opposite_direction[self.direction]:
            return
        self.direction = direction

    def move(self):
        new_head = move_cell(self.cells[0], self.direction)
        cur_prize = self._game._prizes.pop(new_head, None)
        if cur_prize is None:
            old_tail = self.cells.pop()
            self._game.free_cells.add(old_tail)
            self._game.player_cells[old_tail] -= 1
        self.cells.appendleft(new_head)
        self._game.free_cells.discard(new_head)
        self._game.player_cells[new_head] += 1


class Game(object):
    TICK_DURATION = 0.5
    MAX_PRIZES = 300

    HEIGHT = 51
    WIDTH = 51

    SCREEN_HEIGHT = 51
    SCREEN_WIDTH = 51

    def __init__(self):
        self._last_tick_time = None
        self.players = dict()
        self._prizes = dict()
        self.free_cells = set(Cell(x, y) for x in range(self.HEIGHT) for y in range(self.WIDTH))
        self.player_cells = NonZeroDefaultDict(int, zero=0)
        self.send_cv = threading.Condition()

    def get_random_free_cell(self):
        return random.choice(tuple(self.free_cells))

    def get_max_timeout(self):
        return max(0, self.TICK_DURATION - (time.time() - self._last_tick_time))

    def extract_tick_commands(self):
        commands = dict()
        for pid, player in self.players.items():
            commands[pid] = player.interactor.extract_command()
        return commands

    def start(self):
        while True:
            self._last_tick_time = time.time()
            self.process_tick(self.extract_tick_commands())
            time.sleep(self.TICK_DURATION)

    def is_in_border(self, c):
        return c.x in (0, self.HEIGHT - 1) or c.y in (0, self.WIDTH - 1)

    def process_tick(self, commands):
        logging.info("%s", self.players)
        for pid, player in self.players.items():
            player.set_direction(commands[pid])

        self.spawn_prizes()
        for player in self.players.values():
            player.move()
        pids_to_remove = []
        for pid, player in self.players.items():
            if self.player_cells[player.cells[0]] > 1 or self.is_in_border(player.cells[0]):
                pids_to_remove.append(pid)
        with self.send_cv:
            self.send_cv.notify_all()
        for pid in pids_to_remove:
            for cell in self.players[pid].cells:
                self.free_cells.add(cell)
                self.player_cells[cell] -= 1
            self.players[pid].interactor.player_is_dead = True
        for pid in pids_to_remove:
            del self.players[pid]

    def spawn_prizes(self):
        if len(self._prizes) < self.MAX_PRIZES:
            cur_prize = self.get_random_free_cell()
            self._prizes[cur_prize] = +1
            self.free_cells.discard(cur_prize)

    def add_player(self, interactor):
        initial_cell = self.get_random_free_cell()
        direction = random.choice(DIRECTIONS)
        player = Player(self, initial_cell, direction, interactor)
        logging.info("Add player with pid %s", interactor._pid)
        self.players[interactor._pid] = player
        self.free_cells.discard(initial_cell)
        self.player_cells[initial_cell] += 1

    def _add_cell_to_result(self, c, lu, sym, result):
            x, y = c
            x -= lu.x
            y -= lu.y
            if x < 0 or self.SCREEN_WIDTH <= x or y < 0 or self.SCREEN_HEIGHT <= y:
                return
            result[x][y] = sym

    def get_visible_part(self, my_pid):
        center = self.players[my_pid].cells[0]
        lu = Cell(center.x - self.SCREEN_WIDTH // 2, center.y - self.SCREEN_HEIGHT // 2)
        result = [[' ' for y in range(self.SCREEN_HEIGHT)] for x in range(self.SCREEN_WIDTH)]
        for pid, player in self.players.items():
            sym = '*' if pid == my_pid else player.symbol
            for c in player.cells:
                self._add_cell_to_result(c, lu, sym, result)
        for c in self._prizes.keys():
            self._add_cell_to_result(c, lu, '$', result)
        result[self.SCREEN_WIDTH // 2][self.SCREEN_HEIGHT // 2] = '@'

        vertical_borders = [Cell(0, y) for y in range(1, self.HEIGHT - 1)]
        vertical_borders += [Cell(self.WIDTH - 1, y) for y in range(1, self.HEIGHT - 1)]
        for c in vertical_borders:
            self._add_cell_to_result(c, lu, '═', result)

        horizontal_borders = [Cell(x, 0) for x in range(1, self.WIDTH - 1)]
        horizontal_borders += [Cell(x, self.HEIGHT - 1) for x in range(1, self.WIDTH - 1)]
        for c in horizontal_borders:
            self._add_cell_to_result(c, lu, '║', result)


        corners = [Cell(0, 0), Cell(0, self.HEIGHT - 1), Cell(self.WIDTH - 1, 0), Cell(self.WIDTH - 1, self.HEIGHT - 1)]
        corner_chars = ['╔', '╗', '╚', '╝']
        for cell, char in zip(corners, corner_chars):
            self._add_cell_to_result(cell, lu, char, result)

        return result
