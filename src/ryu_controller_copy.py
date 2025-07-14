from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

class StaticTopologySlicing(app_manager.RyuApp):
    OFP_VERSION = [ofproto_v1_3.OFP_VERSION]


    def __init__(self, *args, **kwargs):
        super(StaticTopologySlicing, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.h1 = "00:00:00:00:00:01"
        self.h2 = "00:00:00:00:00:02"
        self.h3 = "00:00:00:00:00:03"
        self.h4 = "00:00:00:00:00:04"
        self.mac_list = ["00:00:00:00:00:01", "00:00:00:00:00:02", "00:00:00:00:00:03", "00:00:00:00:00:04"]


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id

        # Disable default flooding
        match = parser.OFPMatch()
        actions = []
        self.add_flow(datapath, 0, match, actions)

        # Enable ARP flooding (TODO: filter to allow only slice allowed reqs)
        for src in self.mac_list:
            match = parser.OFPMatch(eth_src=src, eth_dst="ff:ff:ff:ff:ff:ff", eth_type=0x0806)
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            self.add_flow(datapath, priority=20, match=match, actions=actions)
            
        # Proactive switches rule (TODO: add rules)
        if dpid == 1: #s1            
            # h1 -> s2
            self.add_mac_flow(datapath, self.h1, self.h2, 4)
            self.add_mac_flow(datapath, self.h2, self.h1, 1)


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

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        
        eth = pkt.get_protocol(icmp)

        src = eth.src
        dst = eth.dst

        self.logger.info("PacketIn: dpid=%s src=%s dst=%s in_port=%s", dpid, src, dst, in_port)

