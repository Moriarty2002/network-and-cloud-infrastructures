# Marcello gay

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

class Environment(object):
    def __init__(self):
        self.net = Mininet(controller=RemoteController, switch=OVSKernelSwitch, link=TCLink)

        self.c0 = self.net.addController('c0', controller=RemoteController)
        self.c0.start()
        
        
        self.h1 = self.net.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
        self.h2 = self.net.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')
        self.h3 = self.net.addHost('h3', ip='10.0.0.3', mac='00:00:00:00:00:03')
        self.h4 = self.net.addHost('h4', ip='10.0.0.4', mac='00:00:00:00:00:04')

        self.s1 = self.net.addSwitch('s1')
        self.s2 = self.net.addSwitch('s2')
        self.s3 = self.net.addSwitch('s3')
        self.s4 = self.net.addSwitch('s4')
        
        self.s5 = self.net.addSwitch('s5')
        self.s6 = self.net.addSwitch('s6')
        
        
        # TODO: check ports on new switches (could not work currently)
        # top path: h1 - s1 - s2 - s4 - h3
        self.net.addLink(self.h1, self.s1, bw=10, delay='1ms', port1=1, port2=1)
        self.net.addLink(self.s1, self.s2, bw=10, delay='5ms', port1=2, port2=1)
        self.net.addLink(self.s2, self.s4, bw=5, delay='5ms', port1=2, port2=1)
        self.net.addLink(self.s2, self.s5, bw=10, delay='5ms', port1=3, port2=1) # new
        self.net.addLink(self.s4, self.s5, bw=5, delay='1ms', port1=2, port2=1) # updates
        self.net.addLink(self.s5, self.h3, bw=10, delay='1ms', port1=2, port2=2) # new

        # bottom path: h2 - s1 - s3 - s4 - h4
        self.net.addLink(self.h2, self.s1, bw=8, delay='1ms', port1=1, port2=4)
        self.net.addLink(self.s1, self.s3, bw=8, delay='5ms', port1=3, port2=1)
        self.net.addLink(self.s3, self.s4, bw=3, delay='5ms', port1=2, port2=4)
        self.net.addLink(self.s3, self.s6, bw=5, delay='5ms', port1=2, port2=4) # new
        self.net.addLink(self.s4, self.s6, bw=3, delay='1ms', port1=3, port2=1) # updates
        self.net.addLink(self.s6, self.h4, bw=5, delay='1ms', port1=3, port2=1) # new

        self.net.build()
        self.net.start()

        print("Topology started")

if __name__ == '__main__':
    setLogLevel('info')
    info('starting the environment\n')
    env = Environment()

    info("*** Running CLI\n")
    CLI(env.net)