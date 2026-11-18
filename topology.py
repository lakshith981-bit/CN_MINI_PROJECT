"""Mininet topology: h1 server, h2/h3 clients, one OVS switch."""
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info


def run():
    net = Mininet(controller=None, switch=OVSSwitch, build=False)
    c0 = net.addController('c0', controller=RemoteController,
                           ip='127.0.0.1', port=6653)
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.build()
    c0.start()
    s1.start([c0])
    info('*** Starting Mininet CLI\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
