import threading
import queue

class PlayerInteractor(object):
    def __init__(self, game, conn):
        self._game = game
        self._conn = conn
        self._thread = threading.Thread(target=self.interact)
        self._commands_queue = queue.Queue()

    def start(self):
        self._thread.start()

    def send_game_state(self):
        pass

    def recv_command(self):
        pass

    def interact(self):
        while True:
            self.send_game_state()
            self._commands_queue.put(self.recv_command())

    def extract_command(self, timeout=None):
        try:
            return self._commands_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None
