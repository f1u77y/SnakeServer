import time

class Game(object):
    TICK_DURATION = 0.5

    def get_max_timeout(self):
        return max(0, self.TICK_DURATION - (time.perf_counter() - self._last_tick_time))

    def extract_tick_commands(self):
        commands = dict()
        for pid, player in self._players.items():
            commands[pid] = player.interactor.extract_command(timeout=self.get_max_timeout())
        return commands

    def start(self):
        while True:
            self._last_tick_time = time.perf_counter()
            self.process_tick(self.extract_tick_commands())
            time.sleep(self.get_max_timeout())

    def process_tick(self, commands):
        pass

    def add_player(self, interactor):
        pass
