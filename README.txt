PROJECT 11: REMOTE SYSTEM HEALTH MONITORING USING SDN

Files:
  health_monitoring/client.py       Collects metrics and sends UDP reports
  health_monitoring/server.py       Receives reports, detects offline/recovery,
                                    and requests Ryu flow priority updates
  health_monitoring/config.py       Shared IP, port, timeout and priority settings
  controller.py                     Ryu OpenFlow 1.3 learning-switch app
  topology.py                       Mininet topology with h1, h2, h3 and s1
  priority_sender.py                Manual Ryu priority-rule test utility

IMPORTANT:
This is a consolidated reconstruction based on the project details and code
snippets available in the conversation and presentation. It is NOT a byte-for-
byte export of the exact files from your Ubuntu machine. Back up your existing
project before replacing anything. Verify Ryu REST and OpenFlow ports against
your installed setup; this package configures OpenFlow TCP 6653 and REST HTTP
8080, with UDP health reports on port 5000.

Topology addresses:
  h1/server: 10.0.0.1
  h2/client: 10.0.0.2
  h3/client: 10.0.0.3
  Ryu REST URL: http://10.0.0.254:8080 (adjust if your Mininet setup differs)

Install dependencies in the relevant Python environment:
  python3 -m pip install -r requirements.txt

Run order (separate terminals):
  1) cd ~/project11 && ryu-manager --ofp-tcp-listen-port 6653 controller.py ryu.app.ofctl_rest
  2) sudo mn -c
  3) sudo python3 topology.py
  4) At mininet> start server: h1 python3 /home/navnit/project11/health_monitoring/server.py &
  5) At mininet> start clients:
       h2 python3 /home/navnit/project11/health_monitoring/client.py --node-id h2 &
       h3 python3 /home/navnit/project11/health_monitoring/client.py --node-id h3 &

NOTE: The server's Ryu REST URL must be reachable from h1. In the Mininet
network, configure the switch/management address used in your actual setup.
This package is provided as a source bundle for review; test before demo.
