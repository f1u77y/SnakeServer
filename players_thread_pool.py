import threading

class PlayersThreadPool(object):
    MAX_PLAYERS = 100

    def __init__(self, game):
        self._game = game
        self._players = dict()
        self._is_id_used = [False for _ in range(self.MAX_PLAYERS)]
        self._min_unused_id = 0
        self._connections_thread = threading.Thread(target=self.accept_connections)
        self._server = socket.socket(sock.AF_INET, socket.SOCK_STREAM)

    def add_player(self, conn):
        if self._min_unused_id >= MAX_PLAYERS:
            raise ValueError('Maximum players limit reached')
        cur_id = self._min_unused_id
        cur_player = Player(self._game, conn)
        self._players[cur_id] = cur_player
        self._game.add_player(cur_player)
        cur_player.start()
        while self._min_unused_id < MAX_PLAYERS and self._is_is_used[self._min_unused_id]:
            self._min_unused_id += 1

    def remove_player(self, player_id):
        del self._players[player_id]
        self._is_id_used[player_id] = False
        if self._min_unused_id > player_id:
            self._min_unused_id = player_id


    def accept_connections(self):
        self._server.bind((HOST, PORT))
        self._server.listen()
        while True:
            conn, _ = self._server.accept()
            self.add_player(conn)


    def start(self):
        self._connections_thread.start()
