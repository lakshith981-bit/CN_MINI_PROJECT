"""Collect system metrics and send periodic UDP health reports."""
import json
import socket
import time
import argparse
import psutil
from config import SERVER_HOST, SERVER_PORT, MONITOR_INTERVAL

parser = argparse.ArgumentParser()
parser.add_argument("--node-id", default=socket.gethostname())
args = parser.parse_args()
node_id = args.node_id
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        net = psutil.net_io_counters()
        if cpu >= 90 or memory >= 90:
            status, priority, dscp = "CRITICAL", 2, 0xB8
        elif cpu >= 70 or memory >= 75:
            status, priority, dscp = "WARNING", 1, 0x48
        else:
            status, priority, dscp = "NORMAL", 1, 0x00

        # DSCP/TOS marking is a packet hint; actual QoS depends on switch policy.
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, dscp)
        report = {
            "node_id": node_id,
            "cpu": cpu,
            "memory": memory,
            "processes": len(psutil.pids()),
            "network_sent": net.bytes_sent,
            "network_received": net.bytes_recv,
            "status": status,
            "priority": priority,
        }
        sock.sendto(json.dumps(report).encode("utf-8"), (SERVER_HOST, SERVER_PORT))
        print("SENT:", report, flush=True)
        time.sleep(MONITOR_INTERVAL)
except KeyboardInterrupt:
    print("Client stopped")
finally:
    sock.close()
