from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import hub
from common import *

class RyuController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(RyuController, self).__init__(*args, **kwargs)
        self.cdn1 = MAC_CDNS[0]
        self.cdn2 = MAC_CDNS[1]
        
        self.h1 = MAC_HOSTS[0]
        self.h2 = MAC_HOSTS[1]
        self.h3 = MAC_HOSTS[2]
        self.h4 = MAC_HOSTS[3]
        
        # out_port_map [current switch] [ switch / host destination]
        self.out_port_map = OUT_PORT_MAP
        
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
    
    """
    base code
    """
    
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
            self.add_arp_flow(datapath, self.cdn1, port_out_s2)
            
            port_out_cdn1 = self.get_out_port(dpid, self.cdn1)  # reverse
            self.add_mac_flow(datapath, self.h1, self.cdn1, port_out_cdn1)
            self.add_mac_flow(datapath, self.h2, self.cdn1, port_out_cdn1)
            self.add_arp_flow(datapath, self.h1, port_out_cdn1)
            self.add_arp_flow(datapath, self.h2, port_out_cdn1)

            # --- bottom slice (cdn2 <-> h3, h4) ---
            port_out_s4 = self.get_out_port(dpid, 4)  # forward to s4
            self.add_mac_flow(datapath, self.cdn2, self.h3, port_out_s4)
            self.add_mac_flow(datapath, self.cdn2, self.h4, port_out_s4)
            self.add_arp_flow(datapath, self.cdn2, port_out_s4)
            
            port_out_cdn2 = self.get_out_port(dpid, self.cdn2)  # reverse
            self.add_mac_flow(datapath, self.h3, self.cdn2, port_out_cdn2)
            self.add_mac_flow(datapath, self.h4, self.cdn2, port_out_cdn2)
            self.add_arp_flow(datapath, self.h3, port_out_cdn2)
            self.add_arp_flow(datapath, self.h4, port_out_cdn2)

            
        elif dpid == 2:
            # Traffic between cdn1 and hosts h1/h2
            port_out_s3 = self.get_out_port(dpid, 3)
            self.add_mac_flow(datapath, self.cdn1, self.h1, port_out_s3)
            self.add_mac_flow(datapath, self.cdn1, self.h2, port_out_s3)
            self.add_arp_flow(datapath, self.cdn1, port_out_s3)
            # premium streaming link
            # port_out_s6 = self.get_out_port(dpid, 6)
            # self.add_video_flow(datapath, self.cdn1, self.h1, UDP_PORT_STREAMING, port_out_s6)
            
            port_out_s1 = self.get_out_port(dpid, 1) # reverse
            self.add_mac_flow(datapath, self.h1, self.cdn1, port_out_s1)
            self.add_mac_flow(datapath, self.h2, self.cdn1, port_out_s1)
            self.add_arp_flow(datapath, self.h1, port_out_s1)
            self.add_arp_flow(datapath, self.h2, port_out_s1)
        
        elif dpid == 3:
            # Traffic between cdn1 and hosts h1/h2
            port_out_s6 = self.get_out_port(dpid, 6)
            self.add_mac_flow(datapath, self.cdn1, self.h1, port_out_s6)
            self.add_mac_flow(datapath, self.cdn1, self.h2, port_out_s6)
            self.add_arp_flow(datapath, self.cdn1, port_out_s6)
            
            port_out_s2 = self.get_out_port(dpid, 2) # reverse
            self.add_mac_flow(datapath, self.h1, self.cdn1, port_out_s2)
            self.add_mac_flow(datapath, self.h2, self.cdn1, port_out_s2)
            self.add_arp_flow(datapath, self.h1, port_out_s2)
            self.add_arp_flow(datapath, self.h2, port_out_s2)

        elif dpid == 4:
            # Traffic between cdn2 and hosts h3/h4
            port_out_s5 = self.get_out_port(dpid, 5)
            self.add_mac_flow(datapath, self.cdn2, self.h3, port_out_s5)
            self.add_mac_flow(datapath, self.cdn2, self.h4, port_out_s5)
            self.add_arp_flow(datapath, self.cdn2, port_out_s5)
            # premium streaming link
            # port_out_s6 = self.get_out_port(dpid, 6)
            # self.add_video_flow(datapath, self.cdn2, self.h4, UDP_PORT_STREAMING, port_out_s6)
            
            port_out_s1 = self.get_out_port(dpid, 1) # reverse
            self.add_mac_flow(datapath, self.h3, self.cdn2, port_out_s1)
            self.add_mac_flow(datapath, self.h4, self.cdn2, port_out_s1)
            self.add_arp_flow(datapath, self.h3, port_out_s1)
            self.add_arp_flow(datapath, self.h4, port_out_s1)

        elif dpid == 5:
            # Traffic between cdn2 and hosts h3/h4
            port_out_s6 = self.get_out_port(dpid, 6)
            self.add_mac_flow(datapath, self.cdn2, self.h3, port_out_s6)
            self.add_mac_flow(datapath, self.cdn2, self.h4, port_out_s6)
            self.add_arp_flow(datapath, self.cdn2, port_out_s6)
            
            port_out_s4 = self.get_out_port(dpid, 4) # reverse
            self.add_mac_flow(datapath, self.h3, self.cdn2, port_out_s4)
            self.add_mac_flow(datapath, self.h4, self.cdn2, port_out_s4)
            self.add_arp_flow(datapath, self.h3, port_out_s4)
            self.add_arp_flow(datapath, self.h4, port_out_s4)

        elif dpid == 6:  # s6: the common host switch
            # --- Top slice handling (cdn1 <-> h1, h2) ---
            port_out_h1 = self.get_out_port(dpid, self.h1)
            port_out_h2 = self.get_out_port(dpid, self.h2)
            self.add_mac_flow(datapath, self.cdn1, self.h1, port_out_h1)
            self.add_mac_flow(datapath, self.cdn1, self.h2, port_out_h2)
            self.add_arp_flow(datapath, self.cdn1, [port_out_h1, port_out_h2])
            
            port_out_s3 = self.get_out_port(dpid, 3) # reverse
            self.add_mac_flow(datapath, self.h1, self.cdn1, port_out_s3)
            self.add_mac_flow(datapath, self.h2, self.cdn1, port_out_s3)
            self.add_arp_flow(datapath, self.h1, port_out_s3)
            self.add_arp_flow(datapath, self.h2, port_out_s3)
            
            # --- Bottom slice handling (cdn2 <-> h3, h4) ---
            port_out_h3 = self.get_out_port(dpid, self.h3)
            port_out_h4 = self.get_out_port(dpid, self.h4)
            self.add_mac_flow(datapath, self.cdn2, self.h3, port_out_h3)
            self.add_mac_flow(datapath, self.cdn2, self.h4, port_out_h4)
            self.add_arp_flow(datapath, self.cdn2, [port_out_h3, port_out_h4])
            
            port_out_s5 = self.get_out_port(dpid, 5) # reverse
            self.add_mac_flow(datapath, self.h3, self.cdn2, port_out_s5)
            self.add_mac_flow(datapath, self.h4, self.cdn2, port_out_s5)
            self.add_arp_flow(datapath, self.h3, port_out_s5)
            self.add_arp_flow(datapath, self.h4, port_out_s5)

    
    def add_mac_flow(self, datapath, src, dst, out_port, priority=10):
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(eth_src=src, eth_dst=dst)
        actions = [parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, priority, match, actions)
    
    
    def add_arp_flow(self, datapath, eth_src, out_port):
        parser = datapath.ofproto_parser
        
        match = parser.OFPMatch(eth_src=eth_src, eth_dst=MAC_BROADCAST, eth_type=ETH_TYPE_ARP)
        actions = []
        if not isinstance(out_port, list):
            out_port = [out_port]

        for port in out_port:
            actions.append(parser.OFPActionOutput(port))
        self.add_flow(datapath, priority=20, match=match, actions=actions)

    def add_video_flow(self, datapath, src_mac, dst_mac, udp_port, out_port, priority=50):
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(
            eth_type=ETH_TYPE_IPV4, 
            ip_proto=IP_PROTO_UDP,
            eth_src=src_mac,
            eth_dst=dst_mac,
            udp_dst=udp_port
        )
        actions = [parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, priority, match, actions)

    
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

    """
    stats code
    """
    
    def request_stats(self, datapath):
        self.logger.info('Sending stats request to switch %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        cookie = cookie_mask = 0
        match = parser.OFPMatch(in_port=1)
        req = parser.OFPFlowStatsRequest(datapath, 0,
                                            ofproto.OFPTT_ALL,
                                            ofproto.OFPP_ANY, ofproto.OFPG_ANY,
                                            cookie, cookie_mask,
                                            match)
        datapath.send_msg(req)
        
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self.request_stats(dp)
            hub.sleep(2) 

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, CONFIG_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info('Registering datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == ofproto_v1_3.OFPCR_ROLE_SLAVE:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]
    
    
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        flows = []
        self.logger.info("mammt")
        for stat in ev.msg.body:
            flows.append('table_id=%s '
                        'duration_sec=%d duration_nsec=%d '
                        'priority=%d '
                        'idle_timeout=%d hard_timeout=%d flags=0x%04x '
                        'cookie=%d packet_count=%d byte_count=%d '
                        'match=%s instructions=%s' %
                        (stat.table_id,
                        stat.duration_sec, stat.duration_nsec,
                        stat.priority,
                        stat.idle_timeout, stat.hard_timeout, stat.flags,
                        stat.cookie, stat.packet_count, stat.byte_count,
                        stat.match, stat.instructions))
        self.logger.debug('FlowStats: %s', flows)
        
    def redirect_premium_flow(self, datapath, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # Example: route to faster/lower-latency path
        out_port = self.get_out_port(datapath.id, 6)  # e.g., direct premium path
        actions = [parser.OFPActionOutput(out_port)]
        self.add_flow(datapath, priority=100, match=match, actions=actions)


            