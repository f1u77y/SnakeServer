import threading
import queue
import nclib.netcat
import game

class PlayerInteractor(object):
    def __init__(self, g, conn, pid):
        self._game = g
        self._conn = nclib.netcat.Netcat(conn)
        self._pid = pid
        self._input_thread = threading.Thread(target=self.input_worker)
        self._output_thread = threading.Thread(target=self.output_worker)
        self._commands_queue = queue.Queue()

    def start(self):
        self._input_thread.start()
        self._output_thread.start()

    def recv_command(self):
        cmd = self._conn.recv_until('\n').decode('ascii')
        if cmd == 'none':
            cmd = None
        return cmd

    def send_game_state(self):
        field = self._game.get_visible_part(self._pid)
        field = ''.join(''.join(row) for row in field).encode('ascii')
        self._conn.send_line(field, ending='\n')

    def input_worker(self):
        while True:
            self._commands_queue.put(self.recv_command())

    def output_worker(self):
        while True:
            self.send_game_state()

    def extract_command(self, timeout=None):
        try:
            return self._commands_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None
