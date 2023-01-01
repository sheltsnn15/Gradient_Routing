# Shelton Ngwenya, R00203947

import random as random

import wsnsimpy.wsnsimpy as wsp_nongui
import wsnsimpy.wsnsimpy_tk as wsp

from node_messages import NodeMessages

INFINITY = float('inf')


class GradientRouting:

    def __init__(self, sim, node):
        # node instance this routing layer belongs to
        self.node = node
        # physical layer instance used to send and receive packets
        self.phy = wsp.DefaultPhyLayer(node)
        # simulation instance
        self.sim = sim

    def init(self):
        # enable logging for this node
        self.logging = True

    def check_trickle_parent(self):
        # Check if the preferred parent is in the potential parents dictionary
        if self.node.preferred_parent in self.node.potential_parents:
            # Get the last update time for the preferred parent
            _, _, last_update_time = self.node.potential_parents[self.node.preferred_parent]
            # If the time since the last update exceeds the maximum Trickle period, send a gradient update
            if self.node.sim.now - last_update_time > 2 * self.node.trickle_timer_max:
                self.send_gradient

    def send_gradient(self):
        # create gradient packet to be broadcasted
        pdu = wsp_nongui.PDU(
            None,
            len(NodeMessages.TYPE_GRADIENT) * 8,
            type=NodeMessages.TYPE_GRADIENT,
            src=self.node.id,
            best_dist=self.node.best_distance,
            rank=self.node.rank,
            dest=wsp.BROADCAST_ADDR)

        # double trickle timer period if it has not reached the maximum period
        if self.node.trickle_timer_period < self.node.trickle_timer_max:
            self.node.trickle_timer_period = 2 * self.node.trickle_timer_period

        # send gradient packet if trickle timer has reached the maximum period or has just been doubled
        if self.node.trickle_timer_period == self.node.trickle_timer_max or self.node.trickle_timer_period == 2 * self.node.trickle_timer_period:
            self.phy.send_pdu(pdu)

    def send_pdu(self, pdu):
        # send packet through the physical layer if a preferred parent has been set
        if self.node.preferred_parent is not None:
            pdu.dest = self.node.preferred_parent
            self.phy.send_pdu(pdu)
            return True
        return False

    def on_receive_pdu(self, pdu):
        # Update the node's state based on the received PDU
        self.update(pdu)

    def run(self):
        # Schedule the first gradient update with a random delay
        self.node.sim.delayed_exec(random.random() * 0.1, self.send_gradient)

    def update(self, pdu):
        # update routing state based on received gradient packet
        if pdu.type == NodeMessages.TYPE_GRADIENT:
            # if the sender of the gradient packet is the preferred parent of the node, schedule a check for trickle
            # timer expiration
            if pdu.src == self.node.preferred_parent:
                self.node.sim.delayed_exec(random.random() * 0.1, self.check_trickle_parent)

            # if the node is not the sink and the sender's rank is not infinity, update the list of potential parents
            # and the preferred parent
            if self.node.id != 0 and pdu.rank != INFINITY:
                self.update_potential_parents(pdu)
                self.update_preferred_parent(pdu)

        # if the received packet is a data packet
        elif pdu.type == NodeMessages.TYPE_DATA:
            # if the packet is intended for this node, pass it to the application layer
            if pdu.dst == self.node.id:
                self.node.on_receive_pdu(pdu)
            # otherwise, forward the packet to the preferred parent
            else:
                self.send_pdu(pdu)

    def print_node_status(self, status):
        self.node.log(f'{status}')

    def update_potential_parents(self, pdu):
        # update the list of potential parents with the new information from the received gradient packet
        self.node.potential_parents[pdu.src] = [round(pdu.rank), round(pdu.best_dist), round(self.node.sim.now, 2)]
        self.print_node_status(f'Potential parents: {self.node.potential_parents.items()}')

    def update_preferred_parent(self, pdu):
        # if the node is not the sink and the sender's rank is not infinity, update the preferred parent
        if self.node.id != 0 and pdu.rank != INFINITY:
            self.update_potential_parents(pdu)
            # if the node has no preferred parent or the sender's rank is lower than the node's rank,
            # set the sender as the preferred parent
            if self.node.preferred_parent is None or pdu.rank + 1 < self.node.rank:
                self.set_new_parent(pdu)

            # if the sender's rank is equal to the node's rank, compare the best distances
            elif pdu.rank + 1 == self.node.rank:
                if pdu.best_dist + 1 < self.node.best_distance:
                    self.set_new_parent(pdu)

            # if the sender's rank is equal to the node's rank, compare the best distances
            elif pdu.rank == self.node.rank:
                if pdu.best_dist < self.node.best_distance:
                    self.set_new_parent(pdu)

    def update_parent(self, old_parent, new_parent):
        # delete the link to the old preferred parent
        if old_parent is not None:
            self.node.scene.dellink(old_parent, self.node.id, "myline")

        # add a link to the new preferred parent
        self.node.scene.addlink(new_parent, self.node.id, "myline")

    def set_new_parent(self, pdu):
        self.node.rank = pdu.rank + 1
        self.print_node_status(f'STATUS UPDATE: New rank ({self.node.rank}), New parent\'s rank ({pdu.rank})')
        self.node.best_distance = pdu.best_dist + 1
        self.node.potential_parents = {}
        old_parent = self.node.preferred_parent
        self.node.preferred_parent = pdu.src
        self.update_parent(old_parent, self.node.preferred_parent)
