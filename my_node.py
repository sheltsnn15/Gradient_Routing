# Shelton Ngwenya, R00203947

import wsnsimpy.wsnsimpy as wsp_nongui
import wsnsimpy.wsnsimpy_tk as wsp

from node_messages import NodeMessages
from routing_proto import GradientRouting

INFINITY = float('inf')
TRICKLE_MIN_PERIOD = .1
TRICKLE_MAX_PERIOD = .2


class Node(wsp.Node):
    def __init__(self, sim, id, pos):
        super().__init__(sim, id, pos)

        self.logging = True
        self.tx_range = 200

        self.rank = INFINITY  # rank of the node
        self.best_distance = INFINITY  # best distance from the sink
        self.potential_parents = {}  # list of potential parents (neighbors) and their distance, rank, and last update time
        self.preferred_parent = None  # current preferred parent (the one with lowest rank and distance)

        self.trickle_timer_min = TRICKLE_MIN_PERIOD  # minimum trickle timer period
        self.trickle_timer_max = TRICKLE_MAX_PERIOD  # maximum trickle timer period
        self.trickle_timer_period = self.trickle_timer_min  # current trickle timer period
        self.data = NodeMessages.HELLO  # data to send in the PDU

        self.routing = GradientRouting(sim, self)  # instantiate gradient routing protocol
        self.mac = self.routing  # set MAC layer to the routing protocol
        self.phy = self.routing.phy  # set PHY layer to the routing protocol's PHY layer

    def init(self):
        super().init()
        # set node color to red
        self.scene.nodecolor(self.id, 1, 0, 0)
        # if the node is the sink, set the color to purple and the distance and rank to 0
        if self.id == 0:
            self.scene.nodecolor(self.id, 0.5, 0, 0.5)
            self.best_distance = 0
            self.rank = 0
        # if the node is not the sink, set the best distance to the distance from the sink and the rank to the distance
        else:
            self.best_distance = wsp.wsnsimpy.distance(self.pos, (0, 0))
            self.rank = self.best_distance

    def send_pdu(self):
        # create PDU with type "data" and the node's data as payload
        pdu = wsp_nongui.PDU(None,
                             8,
                             type=NodeMessages.TYPE_DATA,
                             source=self.id,
                             data=self.data,
                             dest=None
                             )
        # send PDU through the routing protocol
        self.routing.send_pdu(pdu)

    def on_receive_pdu(self, pdu):
        # pass received PDU to the routing protocol
        self.routing.on_receive(pdu)

    def run(self):
        # run the routing protocol
        self.routing.run()
