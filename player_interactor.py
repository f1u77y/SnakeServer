import threading
import json
from sockwrapper import SocketWrapper


class PlayerInteractor(object):
    def __init__(self, g, conn: SocketWrapper, pid, cv):
        self._game = g
        self._conn = conn
        self._pid = pid
        self._input_thread = threading.Thread(target=self.input_worker)
        self._output_thread = threading.Thread(target=self.output_worker)
        self._last_command = 0
        self._is_running = True
        self._send_cv = cv
        self.player_is_dead = False

    def start(self):
        self._input_thread.start()
        self._output_thread.start()

    def stop(self):
        self._is_running = False
        self._conn.shutdown()
        self._conn.close()
        self._input_thread.join()
        self._output_thread.join()

    def recv_command(self):
        data = self._conn.recv_until(b'\n')
        try:
            cmd = json.loads(data.decode())["direction"]
        except Exception:
            cmd = None
        finally:
            return cmd

    def send_game_state(self):
        with self._send_cv:
            self._send_cv.wait()

        if self.player_is_dead:
            data = json.dumps({"type": "end_game"})
        else:
            field = self._game.get_visible_part(self._pid)
            field = ''.join(''.join(row) for row in field)
            data = json.dumps({
                "type": "tick",
                "width": self._game.SCREEN_WIDTH,
                "height": self._game.SCREEN_HEIGHT,
                "raw_map": field,
            })
        self._conn.send_line(data.encode(), end=b'\n')

    def input_worker(self):
        while self._is_running:
            self._last_command = self.recv_command()

    def output_worker(self):
        while self._is_running:
            self.send_game_state()

    def extract_command(self):
        return self._last_command
