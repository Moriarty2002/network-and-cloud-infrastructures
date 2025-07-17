from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, udp
from ryu.lib import hub
from common import *
from prometheus_client import start_http_server, Gauge

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
        self.premium_flows = set()  # store flow identifiers
        
        # Give metrics for prometheus scraper
        self.flow_bitrate_gauge = Gauge('flow_bitrate_mbps', 'Bitrate of flows in Mbps',
                                ['src_ip', 'dst_ip', 'udp_src', 'udp_dst', 'switch_id'])
        self.flow_duration_gauge = Gauge('flow_duration_s', 'Duration of flows in s',
                                ['src_ip', 'dst_ip', 'udp_src', 'udp_dst', 'switch_id'])
        self.flow_avg_pkt_size_gauge = Gauge('flow_avg_pkt_size', 'Average packet size of flows',
                                ['src_ip', 'dst_ip', 'udp_src', 'udp_dst', 'switch_id'])
        start_http_server(9200)  

    
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
            # premium streaming link management
            self.add_to_controller_flow(datapath, CDNS_IP[0], PREMIUM_HOSTS[0])

            
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
            # premium streaming link management
            self.add_to_controller_flow(datapath, CDNS_IP[1], PREMIUM_HOSTS[1])
            
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

    def add_video_flow(self, datapath, src_ip, dst_ip, udp_src, udp_dst, out_port, priority=50):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        
        match = parser.OFPMatch(
            eth_type=ETH_TYPE_IPV4, 
            ip_proto=IP_PROTO_UDP,
            ipv4_src=src_ip,
            ipv4_dst=dst_ip,
            udp_src=udp_src,
            udp_dst=udp_dst
        )
        actions = [parser.OFPActionOutput(out_port)]
        self.logger.info(f"Installed reroute for video stream on switch {datapath.id} → port {out_port}")
        # 10s idle timeout + enable flow remove event
        self.add_flow(datapath, priority, match, actions, 10, ofproto.OFPFF_SEND_FLOW_REM)

    def add_to_controller_flow(self, datapath, ipv4_src, ipv4_dst):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        
        match = parser.OFPMatch(eth_type=ETH_TYPE_IPV4, ip_proto=IP_PROTO_UDP, ipv4_src=ipv4_src, ipv4_dst=ipv4_dst)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 30, match, actions)
        
    def add_flow(self, datapath, priority, match, actions, idle_timeout=0, flag=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst,
            idle_timeout = idle_timeout, flags=flag
        )
        datapath.send_msg(mod)
    
    
    def get_out_port(self, dpid_src, dest) -> int:
        return self.out_port_map[dpid_src][dest]
    
    
    """
    stats code
    """
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        dpid = dp.id

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        udp_pkt = pkt.get_protocol(udp.udp)

        if not ip or not udp_pkt:
            return  # only handle IPv4 UDP

        src_ip = ip.src
        dst_ip = ip.dst
        udp_src = udp_pkt.src_port
        udp_dst = udp_pkt.dst_port

        self.logger.debug(f"New UDP flow: {src_ip}:{udp_src} → {dst_ip}:{udp_dst}")

        # we need this rules in order to manage udp ports dinamically in flow_stats_reply_handle
        # because the match field are the only ones that we can view in the flow stats,
        # withouth this match we could not check udp ports dinamically
        
        match = parser.OFPMatch(
            eth_type=0x0800,
            ip_proto=17,
            ipv4_src=src_ip,
            ipv4_dst=dst_ip,
            udp_src=udp_src,
            udp_dst=udp_dst
        )

        if dpid == 2:
            port_out_s3 = self.get_out_port(dpid, 3)
            actions = [parser.OFPActionOutput(port_out_s3)]
        else:
            port_out_s5 = self.get_out_port(dpid, 5)
            actions = [parser.OFPActionOutput(port_out_s5)]
        
        self.add_flow(dp, 50, match, actions)

    
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_flow_stats(dp)
            hub.sleep(5)

    def _request_flow_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER])
    def state_change_handler(self, ev):
        dp = ev.datapath
        if dp.id not in self.datapaths:
            self.datapaths[dp.id] = dp


    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        dp = ev.msg.datapath
        for stat in ev.msg.body:
            match_fields = dict(stat.match.items())

            src_ip = match_fields.get('ipv4_src')
            dst_ip = match_fields.get('ipv4_dst')
            proto = match_fields.get('ip_proto')
            udp_src = match_fields.get('udp_src')
            udp_dst = match_fields.get('udp_dst')

            # Only consider complete flows that matched with rules from s2 and s4
            if not all([src_ip, dst_ip, proto, udp_src, udp_dst]):
                continue

            if src_ip in CDNS_IP and dst_ip in PREMIUM_HOSTS:
                duration = stat.duration_sec + stat.duration_nsec / 1e9
                bytes_transferred = stat.byte_count
                bitrate = (bytes_transferred * 8) / duration if duration > 0 else 0
                avg_pkt_size = stat.byte_count / stat.packet_count if stat.packet_count > 0 else 0
                
                # prometheus metrics
                bitrate_mbps = bitrate / 1e6
                self.flow_bitrate_gauge.labels(src_ip, dst_ip, str(udp_src), str(udp_dst), str(dp.id)).set(bitrate_mbps)
                self.flow_duration_gauge.labels(src_ip, dst_ip, str(udp_src), str(udp_dst), str(dp.id)).set(duration)
                self.flow_avg_pkt_size_gauge.labels(src_ip, dst_ip, str(udp_src), str(udp_dst), dp.id).set(avg_pkt_size)


                # 3 Mbps threshold, 6s duration, more than 1000 pckt sent, medium packet size
                if bitrate > 3_000_000 and duration > 6 and stat.packet_count > 1000 and 900 < avg_pkt_size < 1500:  
                    self.logger.info(f"Video flow identified: {src_ip}:{udp_src} → {dst_ip}:{udp_dst}")
                    flow_id = (src_ip, dst_ip, udp_src, udp_dst) 
                    if flow_id not in self.premium_flows:
                        self.logger.info(f"Installing premium route for new video flow: {flow_id}")
                        port_out_s6 = self.get_out_port(dp.id, 6)
                        self.add_video_flow(dp, src_ip, dst_ip, udp_src, udp_dst, port_out_s6)
                        self.premium_flows.add(flow_id)

    
    # Flow remove event
    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, ev):
        dpid = ev.msg.datapath.id
        match = ev.msg.match
        src_ip = match.get('ipv4_src')
        dst_ip = match.get('ipv4_dst')
        udp_src = match.get('udp_src')
        udp_dst = match.get('udp_dst')

        flow_id = (src_ip, dst_ip, udp_src, udp_dst)
        if flow_id in self.premium_flows:
            self.premium_flows.remove(flow_id)
            self.logger.info(f"Flow removed by switch and ryu controller state: {flow_id}")
            
            # prometheus metrics reset
            self.flow_bitrate_gauge.labels(src_ip, dst_ip, str(udp_src), str(udp_dst), str(dpid)).set(0)
            self.flow_duration_gauge.labels(src_ip, dst_ip, str(udp_src), str(udp_dst), str(dpid)).set(0)
            self.flow_avg_pkt_size_gauge.labels(src_ip, dst_ip, str(udp_src), str(udp_dst), str(dpid)).set(0)
    