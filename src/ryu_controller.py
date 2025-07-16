from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from common import *

class RyuController(app_manager.RyuApp):
    OFP_VERSION = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(RyuController, self).__init__(*args, **kwargs)
        self.cdn1 = mac_cdns[0]
        self.cdn2 = mac_cdns[1]
        
        self.h1 = mac_hosts[0]
        self.h2 = mac_hosts[1]
        self.h3 = mac_hosts[2]
        self.h4 = mac_hosts[3]
        
        # out_port_map [current switch] [ switch / host destination]
        self.out_port_map = {
            1:  {self.cdn1: 1, self.cdn2: 2, 2: 3, 4: 4},
            2:  {1: 1, 3: 2, 6: 3},
            3:  {2: 1, 6: 2},
            4:  {1: 1, 5: 2, 6: 3},
            5:  {4: 1, 6: 2},
            6:  {self.h1: 3, self.h2: 4, self.h3: 7, self.h4: 8, 3: 1, 2: 2, 5: 6, 4: 5}
        }
    
    # new switch connected event
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

        if dpid == 1:
            # --- top slice (cdn1 <-> h1, h2) ---
            port_out_s2 = self.get_out_port(dpid, 2)  # forward to s2
            self.add_mac_flow(datapath, self.cdn1, self.h1, port_out_s2)
            self.add_mac_flow(datapath, self.cdn1, self.h2, port_out_s2)
            self.add_arp(datapath, self.cdn1, port_out_s2)
            
            port_out_cdn1 = self.get_out_port(dpid, self.cdn1)  # reverse
            self.add_mac_flow(datapath, self.h1, self.cdn1, port_out_cdn1)
            self.add_mac_flow(datapath, self.h2, self.cdn1, port_out_cdn1)
            self.add_arp(datapath, self.h1, port_out_cdn1)
            self.add_arp(datapath, self.h2, port_out_cdn1)

            # --- bottom slice (cdn2 <-> h3, h4) ---
            port_out_s4 = self.get_out_port(dpid, 4)  # forward to s4
            self.add_mac_flow(datapath, self.cdn2, self.h3, port_out_s4)
            self.add_mac_flow(datapath, self.cdn2, self.h4, port_out_s4)
            self.add_arp(datapath, self.cdn2, port_out_s4)
            
            port_out_cdn2 = self.get_out_port(dpid, self.cdn2)  # reverse
            self.add_mac_flow(datapath, self.h3, self.cdn2, port_out_cdn2)
            self.add_mac_flow(datapath, self.h4, self.cdn2, port_out_cdn2)
            self.add_arp(datapath, self.h3, port_out_cdn2)
            self.add_arp(datapath, self.h4, port_out_cdn2)

            
        elif dpid == 2:
            # Traffic between cdn1 and hosts h1/h2
            port_out_s3 = self.get_out_port(dpid, 3)
            self.add_mac_flow(datapath, self.cdn1, self.h1, port_out_s3)
            self.add_mac_flow(datapath, self.cdn1, self.h2, port_out_s3)
            self.add_arp(datapath, self.cdn1, port_out_s3)
            
            port_out_s1 = self.get_out_port(dpid, 1) # reverse
            self.add_mac_flow(datapath, self.h1, self.cdn1, port_out_s1)
            self.add_mac_flow(datapath, self.h2, self.cdn1, port_out_s1)
            self.add_arp(datapath, self.h1, port_out_s1)
            self.add_arp(datapath, self.h2, port_out_s1)
        
        elif dpid == 3:
            # Traffic between cdn1 and hosts h1/h2
            port_out_s6 = self.get_out_port(dpid, 6)
            self.add_mac_flow(datapath, self.cdn1, self.h1, port_out_s6)
            self.add_mac_flow(datapath, self.cdn1, self.h2, port_out_s6)
            self.add_arp(datapath, self.cdn1, port_out_s6)
            
            port_out_s2 = self.get_out_port(dpid, 2) # reverse
            self.add_mac_flow(datapath, self.h1, self.cdn1, port_out_s2)
            self.add_mac_flow(datapath, self.h2, self.cdn1, port_out_s2)
            self.add_arp(datapath, self.h1, port_out_s2)
            self.add_arp(datapath, self.h2, port_out_s2)

        elif dpid == 4:
            # Traffic between cdn2 and hosts h3/h4
            port_out_s5 = self.get_out_port(dpid, 5)
            self.add_mac_flow(datapath, self.cdn2, self.h3, port_out_s5)
            self.add_mac_flow(datapath, self.cdn2, self.h4, port_out_s5)
            self.add_arp(datapath, self.cdn2, port_out_s5)
            
            port_out_s1 = self.get_out_port(dpid, 1) # reverse
            self.add_mac_flow(datapath, self.h3, self.cdn2, port_out_s1)
            self.add_mac_flow(datapath, self.h4, self.cdn2, port_out_s1)
            self.add_arp(datapath, self.h3, port_out_s1)
            self.add_arp(datapath, self.h4, port_out_s1)

        elif dpid == 5:
            # Traffic between cdn2 and hosts h3/h4
            port_out_s6 = self.get_out_port(dpid, 6)
            self.add_mac_flow(datapath, self.cdn2, self.h3, port_out_s6)
            self.add_mac_flow(datapath, self.cdn2, self.h4, port_out_s6)
            self.add_arp(datapath, self.cdn2, port_out_s6)
            
            port_out_s4 = self.get_out_port(dpid, 4) # reverse
            self.add_mac_flow(datapath, self.h3, self.cdn2, port_out_s4)
            self.add_mac_flow(datapath, self.h4, self.cdn2, port_out_s4)
            self.add_arp(datapath, self.h3, port_out_s4)
            self.add_arp(datapath, self.h4, port_out_s4)

        elif dpid == 6:  # s6: the common host switch
            # --- Top slice handling (cdn1 <-> h1, h2) ---
            port_out_h1 = self.get_out_port(dpid, self.h1)
            port_out_h2 = self.get_out_port(dpid, self.h2)
            self.add_mac_flow(datapath, self.cdn1, self.h1, port_out_h1)
            self.add_mac_flow(datapath, self.cdn1, self.h2, port_out_h2)
            self.add_arp(datapath, self.cdn1, [port_out_h1, port_out_h2])
            
            port_out_s3 = self.get_out_port(dpid, 3) # reverse
            self.add_mac_flow(datapath, self.h1, self.cdn1, port_out_s3)
            self.add_mac_flow(datapath, self.h2, self.cdn1, port_out_s3)
            self.add_arp(datapath, self.h1, port_out_s3)
            self.add_arp(datapath, self.h2, port_out_s3)
            
            # --- Bottom slice handling (cdn2 <-> h3, h4) ---
            port_out_h3 = self.get_out_port(dpid, self.h3)
            port_out_h4 = self.get_out_port(dpid, self.h4)
            self.add_mac_flow(datapath, self.cdn2, self.h3, port_out_h3)
            self.add_mac_flow(datapath, self.cdn2, self.h4, port_out_h4)
            self.add_arp(datapath, self.cdn2, [port_out_h3, port_out_h4])
            
            port_out_s5 = self.get_out_port(dpid, 5) # reverse
            self.add_mac_flow(datapath, self.h3, self.cdn2, port_out_s5)
            self.add_mac_flow(datapath, self.h4, self.cdn2, port_out_s5)
            self.add_arp(datapath, self.h3, port_out_s5)
            self.add_arp(datapath, self.h4, port_out_s5)

    
    def add_mac_flow(self, datapath, src, dst, out_port, priority=10):
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(eth_src=src, eth_dst=dst)
        actions = [parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, priority, match, actions)
    
    
    def add_arp(self, datapath, eth_src, out_port):
        parser = datapath.ofproto_parser
        
        match = parser.OFPMatch(eth_src=eth_src, eth_dst=mac_broadcast, eth_type=eth_type_arp)
        actions = []
        if not isinstance(out_port, list):
            out_port = [out_port]

        for port in out_port:
            actions.append(parser.OFPActionOutput(port))
        self.add_flow(datapath, priority=20, match=match, actions=actions)

    
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst
        )
        datapath.send_msg(mod)
    
    
    def get_out_port(self, dpid_src, dest) -> int:
        return self.out_port_map[dpid_src][dest]
    
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        raise NotImplementedError
        # msg = ev.msg
        # datapath = msg.datapath
        # dpid = datapath.id
        # in_port = msg.match['in_port']
        
        # pkt = packet.Packet(msg.data)
        # eth = pkt.get_protocol(ethernet.ethernet)
        
        # src = eth.src
        # dst = eth.dst
        
        # self.logger.info("PacketIn: dpid=%s src=%s dst=%s in_port=%s", dpid, src, dst, in_port)
        