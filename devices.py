import wsnsimpy.wsnsimpy as wsp

from routing_proto import GradientRoutingProtocol


class Node:
    def __init__(self,
                 env,  # (simpy.Environment): the simulation environment
                 id,  # (int): the ID of the node
                 network,  # (Network): the network object
                 # (Application, optional): the application object for the node
                 application=None
                 ):
        self.env = env
        self.id = id
        self.nwk = network
        self.phy = wsp.DefaultPhyLayer(self)  # create physical layer object
        # (Application): the application object for the node
        self.application = application
        self.routing_protocol = GradientRoutingProtocol(
            self, network.sink)  # create gradient routing protocol object

    # Starts the periodic activity of the routing protocol and the application.
    def run(self):
        # start periodic activity of routing protocol
        self.env.process(self.routing_protocol.run())
        if self.application is not None:  # start application if provided
            self.env.process(self.application.run())

    def on_receive_pdu(self,
                       pdu  # (PDU): the received PDU
                       ):  # Processes received PDUs by forwarding them to the routing protocol or the application layer.

        if self.id == 0:  # sink node
            if pdu.type == "data":
                print(f"Received data packet from node {pdu.src} at sink node")
        else:  # non-sink node
            self.routing_protocol.on_receive_pdu(
                pdu)  # forward PDU to routing protocol
