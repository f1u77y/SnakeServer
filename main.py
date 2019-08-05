#! /usr/bin/env python3

import logging

from players_thread_pool import PlayersThreadPool
from game import Game


def set_logger():
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("server.log")
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info("logger initialized")


def main():
    set_logger()
    game = Game()
    players_thread_pool = PlayersThreadPool(game)
    try:
        players_thread_pool.start()
        game.start()
    except KeyboardInterrupt:
        players_thread_pool.stop()


if __name__ == '__main__':
    main()
