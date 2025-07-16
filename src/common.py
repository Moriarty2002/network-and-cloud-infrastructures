MAC_CDNS = ["00:00:00:00:00:01", "00:00:00:00:00:02"]
MAC_HOSTS = ["00:00:00:00:00:03", "00:00:00:00:00:04", "00:00:00:00:00:05", "00:00:00:00:00:06"]
OUT_PORT_MAP = {
            1:  {MAC_CDNS[0]: 1, MAC_CDNS[1]: 2, 2: 3, 4: 4},
            2:  {1: 1, 3: 2, 6: 3},
            3:  {2: 1, 6: 2},
            4:  {1: 1, 5: 2, 6: 3},
            5:  {4: 1, 6: 2},
            6:  {MAC_HOSTS[0]: 3, MAC_HOSTS[1]: 4, MAC_HOSTS[2]: 7, MAC_HOSTS[3]: 8, 3: 1, 2: 2, 5: 6, 4: 5}
        }
CDN_IPS = ['10.0.0.1', '10.0.0.2']
PREMIUM_HOSTS = ['10.0.0.4', '10.0.0.7']

MAC_BROADCAST = "ff:ff:ff:ff:ff:ff"
ETH_TYPE_ARP = 0x0806
ETH_TYPE_IPV4 = 0x0800
IP_PROTO_UDP = 17
UDP_PORT_STREAMING = 9999

PREMIUM_BANDWIDTH_THRESHOLD = 1_000_000  
PREMIUM_PACKET_RATE_THRESHOLD = 500 
