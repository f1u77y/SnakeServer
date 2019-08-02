#! /usr/bin/env python3

from players_thread_pool import PlayersThreadPool
from game import Game

def main():
    game = Game()
    players_thread_pool = PlayersThreadPool(game)
    players_thread_pool.start()
    game.start()


if __name__ == '__main__':
    main()
