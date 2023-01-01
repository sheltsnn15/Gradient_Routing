# Shelton Ngwenya, R00203947

import random as random

import wsnsimpy.wsnsimpy_tk as wsp

from my_node import Node


def main():
    sim = wsp.Simulator(
        until=20,
        timescale=1,
        visual=True,
        terrain_size=(500, 500))

    sim.scene.linestyle("myline", color=(0, .8, 0), arrow="tail", width=2)
    sim.scene.fillstyle("myfill", color=(0.8, 0.6, 0.2))

    for _ in range(0, 15):
        node = sim.add_node(
            Node,
            (random.random() * 500, random.random() * 500))

    sim.run()


if __name__ == '__main__':
    main()
