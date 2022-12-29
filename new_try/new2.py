import random

import wsnsimpy.wsnsimpy as wsp

INFINITY = float('inf')
TRICKLE_MIN_PERIOD = 0.1
TRICKLE_MAX_PERIOD = 2.0


class RoutingProtocol:
    def __init__(self, node):
        self.node = node
        self.rank = INFINITY
        self.best_distance = INFINITY
        self.preferred_parent = None
        self.potential_parents = {}

        self.trickle_timer = self.node.create_event()
        self.trickle_timer.callbacks.append(self.send_gradient_update)
        self.trickle_timer.interval = TRICKLE_MIN_PERIOD
        self.trickle_timer.start()

        self.phy = wsp.DefaultPhyLayer(self)

    def run(self):
        while True:
            yield self.node.timeout(random.uniform(1, 5))
            pdu = {"type": "data", "sender": self.node.id, "data": f"Data packet from node {self.node.id}"}
            if self.send_pdu(pdu):
                self.node.log(f"Sent data packet to sink")
            else:
                self.node.log(f"Failed to send data packet to sink")

    def send_pdu(self, pdu):
        if self.preferred_parent is None:
            return False

        self.phy.send(self.preferred_parent.id, pdu)
        return True

    def send_gradient_update(self):
        if self.rank == INFINITY:
            return
        pdu = {"type": "gradient", "sender": self.node.id, "rank": self.rank,
               "best_distance": self.best_distance}
        self.node.send(wsp.BROADCAST_ADDR, pdu)

        self.trickle_timer.interval = min(self.trickle_timer.interval * 2, MAX_TRICKLE_PERIOD)
        self.trickle_timer.start()

    def on_receive_pdu(self, pdu):
        if pdu["type"] == "gradient":
            sender = self.node.sim.nodes[pdu["sender"]]
            self.update_parent(sender, pdu["rank"], pdu["best_distance"])
        elif pdu["type"] == "data":
            if self.node.id == 0:  # Network sink
                self.node.log(f"Received data packet from node {pdu['sender']}")
                self.node.on_receive_pdu(pdu)
            else:
                self.send_pdu(pdu)
