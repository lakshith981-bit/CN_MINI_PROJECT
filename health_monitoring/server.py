"""UDP health server, timeout-based failure detection and Ryu flow updates."""
import json
import socket
import time
import requests
from config import (SERVER_HOST, SERVER_PORT, BUFFER_SIZE, TIMEOUT,
                    RYU_BASE_URL, SWITCH_DPID,
                    NORMAL_FLOW_PRIORITY, WARNING_FLOW_PRIORITY,
                    CRITICAL_FLOW_PRIORITY)

last_seen = {}          # node IP -> last report time
offline_nodes = set()   # node IPs currently considered offline
last_flow_priority = {} # node IP -> last installed OpenFlow priority


def install_priority_rule(node_ip, flow_priority):
    """Replace this node's IPv4-source flow rule through Ryu's REST API."""
    url = f"{RYU_BASE_URL}/stats/flowentry/add"
    payload = {
        "dpid": int(SWITCH_DPID),
        "priority": flow_priority,
        "cookie": 0,
        "cookie_mask": 0,
        "table_id": 0,
        "idle_timeout": 0,
        "hard_timeout": 0,
        "match": {"eth_type": 2048, "ipv4_src": f"{node_ip}/32"},
        "instructions": [{"type": "APPLY_ACTIONS", "actions": [
            {"type": "OUTPUT", "port": "NORMAL"}
        ]}],
    }
    # Remove an earlier exact match first so a stale priority does not remain.
    delete_url = f"{RYU_BASE_URL}/stats/flowentry/delete_strict"
    delete_payload = {
        "dpid": int(SWITCH_DPID), "table_id": 0,
        "priority": last_flow_priority.get(node_ip, flow_priority),
        "match": {"eth_type": 2048, "ipv4_src": f"{node_ip}/32"},
    }
    try:
        requests.post(delete_url, json=delete_payload, timeout=2)
        response = requests.post(url, json=payload, timeout=2)
        response.raise_for_status()
        last_flow_priority[node_ip] = flow_priority
        print(f"SDN RULE UPDATED: {node_ip} -> priority {flow_priority} (HTTP {response.status_code})", flush=True)
    except requests.RequestException as exc:
        print(f"SDN UPDATE FAILED for {node_ip}: {exc}", flush=True)


server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((SERVER_HOST, SERVER_PORT))
server.settimeout(1)
print(f"Health server listening on {SERVER_HOST}:{SERVER_PORT}/UDP", flush=True)

try:
    while True:
        now = time.time()
        try:
            data, address = server.recvfrom(BUFFER_SIZE)
            report = json.loads(data.decode("utf-8"))
            node_ip = address[0]
            node_id = report.get("node_id", node_ip)
            last_seen[node_ip] = time.time()
            if node_ip in offline_nodes:
                offline_nodes.remove(node_ip)
                print(f"RECOVERY: {node_id} ({node_ip}) is ONLINE again", flush=True)
            print(
                f"HEALTH REPORT | {node_id} {node_ip} | "
                f"CPU {report.get('cpu')}% | MEM {report.get('memory')}% | "
                f"Processes {report.get('processes')} | Status {report.get('status')}",
                flush=True,
            )
            status = report.get("status", "NORMAL")
            flow_priority = (CRITICAL_FLOW_PRIORITY if status == "CRITICAL" else
                             WARNING_FLOW_PRIORITY if status == "WARNING" else
                             NORMAL_FLOW_PRIORITY)
            if last_flow_priority.get(node_ip) != flow_priority:
                install_priority_rule(node_ip, flow_priority)
        except socket.timeout:
            pass
        except (ValueError, json.JSONDecodeError) as exc:
            print("Invalid health report:", exc, flush=True)

        now = time.time()
        for node_ip, last_time in list(last_seen.items()):
            if now - last_time > TIMEOUT and node_ip not in offline_nodes:
                offline_nodes.add(node_ip)
                print(f"ALERT: NODE OFFLINE: {node_ip}", flush=True)
finally:
    server.close()
