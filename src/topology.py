from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from common import *

class Environment(object):
    def __init__(self):
        self.net = Mininet(controller=RemoteController, switch=OVSKernelSwitch, link=TCLink)

        self.c0 = self.net.addController('c0', controller=RemoteController)
        self.c0.start()
        
        
        self.cdn1 = self.net.addHost('cdn1', ip='10.0.0.1', mac=MAC_CDNS[0])
        self.cdn2 = self.net.addHost('cdn2', ip='10.0.0.2', mac=MAC_CDNS[1])
        
        
        self.h1 = self.net.addHost('h1', ip='10.0.0.4', mac=MAC_HOSTS[0]) # premium user
        self.h2 = self.net.addHost('h2', ip='10.0.0.5', mac=MAC_HOSTS[1])
        self.h3 = self.net.addHost('h3', ip='10.0.0.6', mac=MAC_HOSTS[2])
        self.h4 = self.net.addHost('h4', ip='10.0.0.7', mac=MAC_HOSTS[3]) # premium user

        self.s1 = self.net.addSwitch('s1') # cdns common switch
        
        self.s2 = self.net.addSwitch('s2') # top slice switches
        self.s3 = self.net.addSwitch('s3')
        
        self.s4 = self.net.addSwitch('s4') # bottom slice switched
        self.s5 = self.net.addSwitch('s5')
        
        self.s6 = self.net.addSwitch('s6') # hosts common switch
        
        # top slice: cdn1, s1, s2, s3, s6, h1, h2
        self.net.addLink(self.cdn1, self.s1, bw=15, delay='1ms', port1=1, port2=1)
        self.net.addLink(self.s1, self.s2, bw=15, delay='5ms', port1=3, port2=1)
        self.net.addLink(self.s2, self.s3, bw=2, delay='50ms', port1=2, port2=1)
        self.net.addLink(self.s3, self.s6, bw=2, delay='50ms', port1=2, port2=1)
        self.net.addLink(self.s2, self.s6, bw=6, delay='3ms', port1=3, port2=2) # direct link for premium users
        self.net.addLink(self.s6, self.h1, bw=8, delay='5ms', port1=3, port2=1) # s6 to h1, h2 links 
        self.net.addLink(self.s6, self.h2, bw=8, delay='5ms', port1=4, port2=1) 

        # bottom slice: cdn2, s1, s4, s5, s6, h3, h4
        self.net.addLink(self.cdn2, self.s1, bw=15, delay='1ms', port1=1, port2=2)
        self.net.addLink(self.s1, self.s4, bw=15, delay='5ms', port1=4, port2=1)
        self.net.addLink(self.s4, self.s5, bw=2, delay='50ms', port1=2, port2=1)
        self.net.addLink(self.s5, self.s6, bw=2, delay='50ms', port1=2, port2=6)
        self.net.addLink(self.s4, self.s6, bw=5, delay='3ms', port1=3, port2=5) # direct link for premium users
        self.net.addLink(self.s6, self.h3, bw=8, delay='5ms', port1=7, port2=1) # s6 to h3, h4 links 
        self.net.addLink(self.s6, self.h4, bw=8, delay='5ms', port1=8, port2=1)

        self.net.build()
        self.net.start()

        print("Topology started")

if __name__ == '__main__':
    setLogLevel('info')
    info('starting the environment\n')
    env = Environment()

    info("*** Running CLI\n")
    CLI(env.net)