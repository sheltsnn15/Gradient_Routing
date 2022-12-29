from routing_proto import RoutingProtocol
import wsnsimpy.wsnsimpy as wsp

INFINITY = float('inf')
TRICKLE_MIN_PERIOD = 0.1
TRICKLE_MAX_PERIOD = 2.0


class Node(wsp.Node):
    def __init__(self, sim, id, pos):
        super().__init__(sim, id, pos)
        self.routing = RoutingProtocol(self)
        self.mac = self.routing
        self.phy = self.routing.phy

    def init(self):
        super().init()
        self.logging = True

    def run(self):
        self.init()
        self.routing.run()
        yield self.timeout(1)

    def send(self, dst, *args, **kwargs):
        if self.routing.send_pdu({"data": args[0]}):
            self.log(f"Sending packet to {dst}: {args[0]}")
        else:
            self.log(f"Could not send packet: {args[0]}")

    def on_receive(self, sender, *args, **kwargs):
        self.routing.on_receive_pdu({"sender": sender, "data": args[0]})

    def on_receive_pdu(self, pdu):
        self.log(f"Received packet from {pdu.sender_id}: {pdu['data']}")
