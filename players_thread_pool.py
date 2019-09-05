import threading
import socket
import logging

from sockwrapper import SocketWrapper
import player_interactor


class PlayersThreadPool(object):
    MAX_PLAYERS = 20

    def __init__(self, game):
        self._game = game
        self._players = dict()
        self._is_id_used = [False for _ in range(self.MAX_PLAYERS)]
        self._min_unused_id = 1
        self._connections_thread = threading.Thread(target=self.accept_connections)
        self._server = SocketWrapper(socket.AF_INET, socket.SOCK_STREAM)
        self._is_running = True

    def add_player(self, conn):
        self.remove_dead_players()
        logging.info("Add player with id %s", self._min_unused_id)
        if self._min_unused_id >= self.MAX_PLAYERS:
            raise ValueError('Maximum players limit reached')
        cur_id = self._min_unused_id
        interactor = player_interactor.PlayerInteractor(self._game, conn, cur_id, self._game.send_cv)
        self._players[cur_id] = interactor
        self._game.add_player(interactor)
        interactor.start()
        self._min_unused_id += 1

    def remove_dead_players(self):
        pid_to_remove = []
        for pid in self._players:
            if self._players[pid].player_is_dead:
                pid_to_remove.append(pid)
        for pid in pid_to_remove:
            self.remove_player(pid)

    def remove_player(self, player_id):
        logging.info("Remove player with id %s", player_id)
        del self._players[player_id]
        self._is_id_used[player_id] = False
        if self._min_unused_id > player_id:
            self._min_unused_id = player_id

    def accept_connections(self):
        self._server.bind(('', 1488))
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
