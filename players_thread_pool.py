import threading
import socket

from game import Player
import player_interactor


class PlayersThreadPool(object):
    MAX_PLAYERS = 10

    def __init__(self, game):
        self._game = game
        self._players = dict()
        self._is_id_used = [False for _ in range(self.MAX_PLAYERS)]
        self._min_unused_id = 1
        self._connections_thread = threading.Thread(target=self.accept_connections)
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._is_running = True

    def add_player(self, conn):
        if self._min_unused_id >= self.MAX_PLAYERS:
            raise ValueError('Maximum players limit reached')
        cur_id = self._min_unused_id
        interactor = player_interactor.PlayerInteractor(self._game, conn, cur_id)
        self._players[cur_id] = interactor
        self._game.add_player(interactor)
        interactor.start()
        self._min_unused_id += 1

    def remove_player(self, player_id):
        del self._players[player_id]
        self._is_id_used[player_id] = False
        if self._min_unused_id > player_id:
            self._min_unused_id = player_id

    def accept_connections(self):
        self._server.bind(('127.0.0.1', 1488))
        self._server.listen(self.MAX_PLAYERS)
        while self._is_running:
            conn, _ = self._server.accept()
            self.add_player(conn)

    def start(self):
        self._connections_thread.start()

    def stop(self):
        self._is_running = False
        for player in self._game.players.values():
            player.interactor.stop()
        self._server.shutdown(socket.SHUT_RDWR)
        self._server.close()
        self._connections_thread.join()


