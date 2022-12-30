import wsnsimpy.wsnsimpy as wsp

from node_messages import NodeMessages

INFINITY = float('inf')
TRICKLE_MIN_PERIOD = 0.1
TRICKLE_MAX_PERIOD = 2.0


class RoutingProtocol:
    def __init__(self, node):
        # Store a reference to the node that this routing protocol instance is associated with
        self.node = node
        # Initialize variables for keeping track of the preferred parent, potential parents, and the
        # best distance and rank of the node
        self.best_distance = INFINITY
        self.rank = INFINITY
        self.preferred_parent = None
        self.potential_parents = {}
        # Create a timer for sending gradient updates using the TRICKLE algorithm
        self.trickle_timer = node.timeout(TRICKLE_MIN_PERIOD, self.send_gradient_update)
        # Store a reference to the physical layer of the node
        self.phy = node.phy
        # Set a flag for logging
        self.logging = True

    def run(self):
        # Continuously send gradient updates according to the TRICKLE algorithm
        while True:
            yield self.trickle_timer.interval
            self.trickle_timer.reset()
            self.send_gradient_update()

    def send_gradient_update(self):
        # Don't send a gradient update if the rank of the node is infinity
        if self.rank == INFINITY:
            return

        # Increase the interval between gradient updates according to the TRICKLE algorithm
        if self.trickle_timer.interval < TRICKLE_MAX_PERIOD:
            self.trickle_timer.interval *= 2

        # Create a PDU containing the gradient update message and send it to all nodes in the network
        pdu = wsp.PDU(
            None,
            len(NodeMessages.TYPE_GRADIENT) * 8,
            type=NodeMessages.TYPE_GRADIENT,
            sender=self.node.id,
            rank=self.rank,
            best_distance=self.best_distance
        )
        self.node.send(wsp.BROADCAST_ADDR, pdu)

    def update_parent(self, parent_id):
        # Update the preferred parent and the best distance and rank of the node based on the
        # information in the PDU
        if parent_id in self.potential_parents:
            self.preferred_parent = self.node.sim.get_node(parent_id)
            self.best_distance = self.preferred_parent.routing_protocol.best_distance + 1
            self.rank = self.best_distance
            # Reset the trickle timer to the minimum interval
            self.trickle_timer.interval = TRICKLE_MIN_PERIOD
            self.trickle_timer.reset()

    def remove_parent(self, parent_id):
        # Remove the specified parent from the potential parents list and update the preferred parent
        # and the best distance and rank of the node accordingly
        if parent_id in self.potential_parents:
            del self.potential_parents[parent_id]
            self.preferred_parent = None
            self.best_distance = INFINITY
            self.rank = INFINITY
            for _, parent in self.potential_parents.items():
                if parent["best_distance"] < self.best_distance:
                    self.preferred_parent = self.node.sim.get_node(parent["id"])
                    self.best_distance = parent["best_distance"]
                    self.rank = self.best_distance
            # If there are no more potential parents, set the trickle timer interval to the maximum value
            if not self.preferred_parent:
                self.trickle_timer.interval = TRICKLE_MAX_PERIOD
            # Otherwise, set the trickle timer interval to the minimum value and reset the timer
            else:
                self.trickle_timer.interval = TRICKLE_MIN_PERIOD
                self.trickle_timer.reset()

    def send_pdu(self, pdu):
        # Check if the node has a preferred parent
        if self.preferred_parent is None:
            return False
        # Set the type of the PDU to "data" and the sender ID to the ID of the node
        pdu.type = "data"
        pdu.sender_id = self.node.id

        # Create a new PDU containing the data message and send it to the preferred parent
        pdu = wsp.PDU(
            None,
            len(NodeMessages.TYPE_DATA) * 8,
            type=NodeMessages.TYPE_DATA,
            sender=self.node.id,
            rank=pdu.rank,
            best_distance=pdu.best_distance
        )
        self.phy.send(self.preferred_parent, pdu)
        return True

    def on_receive_pdu(self, pdu):
        # Handle a received PDU depending on its type
        if pdu.type == "gradient":
            # Update the preferred parent, best distance, and rank of the node based on the information
            # in the PDU
            if pdu.rank < self.rank:
                self.update_parent(pdu.sender_id)
            elif pdu.rank == self.rank:
                if pdu.best_distance < self.best_distance:
                    self.update_parent(pdu.sender_id)
                elif pdu.best_distance == self.best_distance:
                    if pdu.sender_id < self.node.id:
                        self.update_parent(pdu.sender_id)
            # Add the sender of the PDU to the list of potential parents
            self.potential_parents[pdu.sender_id] = {
                "id": pdu.sender_id,
                "rank": pdu.rank,
                "best_distance": pdu.best_distance,
            }
        elif pdu.type == "data":
            # Forward the data message to the preferred parent if the node has one, otherwise drop the message
            if self.node.id == 0:
                self.node.on_receive_pdu(pdu)
            else:
                self.send_pdu(pdu)
