import time
import random
from collections import namedtuple, deque

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
        return Cell(c.x - 1, c.y)
    elif direction == 'right':
        return Cell(c.x + 1, c.y)
    elif direction == 'up':
        return Cell(c.x, c.y - 1)
    elif direction == 'down':
        return Cell(c.x, c.y + 1)
    else:
        return c


class Player(object):
    def __init__(self, game, cell, direction, interactor):
        self._game = game
        self.cells = deque((cell,))
        self.direction = direction
        self.interactor = interactor

    def set_direction(self, direction):
        if direction == opposite_direction(self.direction):
            return
        self.direction = direction

    def move_tail(self):
        new_head = move_cell(self.cells[0], self.direction)
        if new_head not in self._game.prizes:
            self.cells.pop()

    def move_head(self):
        new_head = move_cell(self.cells[0], self.direction)
        self._game.prizes.pop(new_head, None)
        self.cells.appendleft(new_head)


class Game(object):
    TICK_DURATION = 0.5
    MAX_PRIZES = 300

    HEIGHT = 300
    WIDTH = 300

    SCREEN_HEIGHT = 51
    SCREEN_WIDTH = 51

    def __init__(self):
        self._last_tick_time = None
        self.players = dict()
        self._prizes = dict()


    def get_player_free_cells(self, exclude=None):
        all_cells = set((x, y) for x in range(self.WIDTH) for y in range(self.HEIGHT))
        player_cells = set(cell for pid, player in self.players.items() for cell in player.cells
                           if pid != exclude)
        return all_cells - player_cells

    def get_random_free_cell(self):
        player_free_cells = self.get_player_free_cells()
        prize_cells = set(self._prizes.keys())
        free_cells = player_free_cells - prize_cells
        return random.choice(tuple(free_cells))

    def get_max_timeout(self):
        return max(0, self.TICK_DURATION - (time.perf_counter() - self._last_tick_time))

    def extract_tick_commands(self):
        commands = dict()
        for pid, player in self.players.items():
            commands[pid] = player.interactor.extract_command(timeout=self.get_max_timeout())
        return commands

    def start(self):
        while True:
            self._last_tick_time = time.perf_counter()
            self.process_tick(self.extract_tick_commands())
            time.sleep(self.get_max_timeout())

    def process_tick(self, commands):
        for pid, player in self.players.items():
            player.set_direction(commands[pid])

        self.spawn_prizes()

        for player in self.players.values():
            player.move_tail()
        for player in self.players.values():
            player.move_head()
        pids_to_remove = []
        for pid, player in self.players.values():
            player_free_cells = self.get_player_free_cells(exclude=pid)
            if player.cells[0] not in player_free_cells:
                player.annouce_remove_self()
                pids_to_remove.append(pid)
        for pid in pids_to_remove:
            del self.players[pid]

    def spawn_prizes(self):
        while len(self._prizes) < self.MAX_PRIZES:
            self._prizes[self.get_random_free_cell()] = +1

    def add_player(self, interactor):
        initial_cell = self.get_random_free_cell()
        direction = random.choice(DIRECTIONS)
        player = Player(self, initial_cell, direction, interactor)

    def _add_cell_to_result(self, c, lu, sym, result):
            x, y = c
            x -= lu.x
            y -= lu.y
            if x < 0 or self.SCREEN_WIDTH <= x or y < 0 or self.SCREEN_HEIGHT <= y:
                return
            result[x][y] = sym


    def get_visible_part(self, my_pid):
        center = player.cells[0]
        lu = Cell(center.x - self.SCREEN_WIDTH // 2, center.y - self.SCREEN_HEIGHT // 2)
        result = [['.' for y in range(self.SCREEN_HEIGHT)] for x in range(self.SCREEN_WIDTH)]
        for pid, player in self.players.items():
            sym = '*' if pid == my_pid else random.choice(string.ascii_lowercase)
            for c in player.cells:
                self._add_cell_to_result(c, lu, sym, result)
        for c in self._prizes.keys():
            self._add_cell_to_result(c, lu, '$', result)
        result[self.SCREEN_WIDTH // 2][self.SCREEN_HEIGHT // 2] = '@'

        vertical_borders = [Cell(0, y) for y in range(1, self.HEIGHT - 1)]
        vertical_borders += [Cell(self.WIDTH - 1, y) for y in range(1, self.HEIGHT - 1)]
        for c in vertical_borders:
            self._add_cell_to_result(c, lu, '|', result)

        horizontal_borders = [Cell(x, 0) for x in range(1, self.WIDTH - 1)]
        horizontal_borders += [Cell(x, self.HEIGHT - 1) for x in range(1, self.WIDTH - 1)]
        for c in horizontal_borders:
            self._add_cell_to_result(c, lu, '-', result)

        corners = [Cell(0, 0), Cell(0, self.HEIGHT - 1), Cell(self.WIDTH - 1, 0), Cell(self.WIDTH - 1, self.HEIGHT - 1)]
        for c in corners:
            self._add_cell_to_result(c, lu, '+', result)

        return result
