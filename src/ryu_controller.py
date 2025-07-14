from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

class RyuController(app_manager.RyuApp):
    OFP_VERSION = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(RyuController, self).__init__(*args, **kwargs)

        # MAC address dei 4 host
        self.h1 = "00:00:00:00:00:01"
        self.h2 = "00:00:00:00:00:02"
        self.h3 = "00:00:00:00:00:03"
        self.h4 = "00:00:00:00:00:04"

    # new switch connected event
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id

        # Rimuove il comportamento di default (flood)
        match = parser.OFPMatch()
        actions = []
        self.add_flow(datapath, 0, match, actions)

        # Regole statiche per ogni switch
        if dpid == 1:
            # s1
            # h1 -> s2
            self.add_mac_flow(datapath, self.h1, self.h3, 2)
            # h3 -> s1 -> h1
            self.add_mac_flow(datapath, self.h3, self.h1, 1)

            # h2 -> s3
            self.add_mac_flow(datapath, self.h2, self.h4, 3)
            # h4 -> s1 -> h2
            self.add_mac_flow(datapath, self.h4, self.h2, 4)

        elif dpid == 2:
            # s2
            self.add_mac_flow(datapath, self.h1, self.h3, 2)
            self.add_mac_flow(datapath, self.h3, self.h1, 1)

        elif dpid == 3:
            # s3
            self.add_mac_flow(datapath, self.h2, self.h4, 2)
            self.add_mac_flow(datapath, self.h4, self.h2, 1)

        elif dpid == 4:
            # s4
            # path alto
            self.add_mac_flow(datapath, self.h1, self.h3, 2)
            self.add_mac_flow(datapath, self.h3, self.h1, 1)
            # path basso
            self.add_mac_flow(datapath, self.h2, self.h4, 3)
            self.add_mac_flow(datapath, self.h4, self.h2, 4)

    def add_mac_flow(self, datapath, src, dst, out_port, priority=10):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(eth_src=src, eth_dst=dst)
        actions = [parser.OFPActionOutput(out_port)]

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst
        )
        datapath.send_msg(mod)
        