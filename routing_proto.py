import wsnsimpy.wsnsimpy as wsp

# Constant to represent infinity in the rank attribute
INFINITY = float('inf')
# Constants for the Trickle timer
TRICKLE_MIN_PERIOD = 0.1
TRICKLE_MAX_PERIOD = 2.0


class GradientRoutingProtocol:
    def __init__(self,
                 node,  # the node that the protocol will be running on
                 sink,  # the network sink node
                 hop_count_metric=False  # flag to indicate whether the hop-count metric should be used (default: False)
                 ):
        self.node = node
        self.sink = sink
        self.env = node.env
        self.hop_count_metric = hop_count_metric
        self.rank = INFINITY  # initial rank is infinity
        self.best_distance = INFINITY  # initial best distance is infinity
        self.preferred_parent = None  # initial preferred parent is None
        self.trickle_min_period = TRICKLE_MIN_PERIOD  # minimum Trickle period in ms
        self.trickle_max_period = TRICKLE_MAX_PERIOD  # maximum Trickle period in ms
        self.trickle_expired = False  # flag to indicate whether the Trickle timer has expired
        self.potential_parents = {}  # dictionary to store potential parents

    def run(self):  # Runs the periodic activity of the gradient routing protocol.
        # send gradient updates to neighbors every Trickle period
        while True:
            if self.trickle_expired:
                self.send_gradient_update()
                self.trickle_min_period = min(self.trickle_min_period * 2, self.trickle_max_period)
                self.trickle_expired = False
            self.monitor_potential_parents()
            yield self.env.timeout(self.trickle_min_period)

    def send_gradient_update(self):  # Sends a gradient update to the node's neighbors.
        # send gradient update to neighbors
        if self.rank == INFINITY:
            return  # don't send updates if rank is infinity
        pdu = wsp.PDU(
            src=self.node.id,
            dst=None,
            type="gradient",
            payload=(self.rank, self.best_distance)
        )
        self.node.phy.send_pdu(pdu)

    def on_receive_pdu(self,
                       pdu  # pdu: the received PDU
                       ):  # Processes a received PDU.
        # process received PDUs
        if pdu.type == "gradient":
            # process gradient update
            rank, distance = pdu.payload
            if pdu.src not in self.potential_parents:
                # add new potential parent
                self.potential_parents[pdu.src] = {"rank": rank, "distance": distance, "timestamp": self.env.now}
            else:
                # update existing potential parent
                self.potential_parents[pdu.src]["rank"] = rank
                self.potential_parents[pdu.src]["distance"] = distance
                self.potential_parents[pdu.src]["timestamp"] = self.env.now
            self.update_preferred_parent()
        elif pdu.type == "data":
            # forward data packet to preferred parent
            if self.preferred_parent is not None:
                self.node.phy.send_pdu(pdu, dst=self.preferred_parent)
            else:
                return False  # don't allow sending packets if there is no parent towards the sink

    def monitor_potential_parents(
            self):  # Removes potential parents that haven't sent a gradient update in the last 2 Trickle max periods
        # and updates the preferred parent if it was removed.

        # remove potential parents that haven't sent a gradient update in the last 2 Trickle max periods
        for parent, info in self.potential_parents.items():
            if self.env.now - info["timestamp"] > 2 * self.trickle_max_period:
                del self.potential_parents[parent]
        # update preferred parent if it was removed
        if self.preferred_parent not in self.potential_parents:
            self.update_preferred_parent()

    def update_preferred_parent(self):  # Updates the preferred parent and rank based on the potential parents.
        # update preferred parent and rank based on potential parents
        min_distance = float("inf")
        best_parent = None
        for parent, info in self.potential_parents.items():
            if info["rank"] + 1 < self.rank or (info["rank"] + 1 == self.rank and info["distance"] < min_distance):
                self.rank = info["rank"] + 1
                min_distance = info["distance"]
                best_parent = parent
        if best_parent is None:
            self.rank = INFINITY  # set rank to infinity if there are no available parents
        self.best_distance = min_distance
        self.preferred_parent = best_parent
        self.trickle_expired = True  # reset Trickle timer
