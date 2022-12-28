1. First, create a class for the node that will represent each node in the network.\
   ### attributes
    - ID,
    - rank,
    - preferred parent,
    - list of potential parents.\
   ### method
    - send data packets to the network sink
    - receive data packets from the network sink.
2. Next, create a class for the routing protocol that will be used to route data packets between nodes in the network.
   ### attributes
    - Trickle timer (timer that periodically expires and triggers the sending of gradient updates to the node's
      neighbors).
        - The period of the timer should be doubled each time it expires, up to a maximum value of 2 seconds. If the
          node's internal state changes, the timer should be reset to its minimum value (100 ms).
   ## methods
        - send_pdu method that takes a PDU (protocol data unit) as a parameter and forwards it towards the network sink using the preferred parent of the node. 
        - on_receive_pdu method that handles incoming PDUs, either by forwarding them towards the network sink or delivering them to the node's application layer if the node is the destination.
3. In the routing protocol class, implement the parent monitoring feature by keeping track of the last time a gradient
   update was received from each potential parent. If a gradient update is not received within two maximum Trickle
   periods, the parent should be removed from the list of potential parents. If the preferred parent is removed, the
   node should select the potential parent with the shortest distance as the new preferred parent. If there are no
   available parents, the node should set its rank to infinity.
5. In the node class, instantiate the routing protocol and set it as the MAC layer. Also, implement the run method that
   will be called periodically to perform the necessary activities of the node, such as sending data packets and
   updating the routing information. In this method, call the run method of the routing protocol to allow it to perform
   its periodic activities.
6. To create the network, instantiate the nodes and specify their neighbors. Then, set the network sink (node with ID 0)
   as the destination for all data packets.
7. To test the network application, you can send data packets from the nodes to the network sink and verify that the
   sink is receiving and printing the addresses of the sender nodes as expected. You can also verify that the gradient
   routing protocol is correctly forwarding the data packets towards the sink using the hop-count metric and that the
   Trickle timer is working as expected.