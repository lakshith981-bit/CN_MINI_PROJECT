"""Manually install a priority rule for a client through Ryu REST."""
import sys
import requests
from health_monitoring.config import RYU_BASE_URL, SWITCH_DPID

if len(sys.argv) != 3:
    print('Usage: python3 priority_sender.py <client_ip> <health_priority:1|2>')
    raise SystemExit(1)
client_ip = sys.argv[1]
health_priority = int(sys.argv[2])
flow_priority = 200 if health_priority == 2 else 100
payload = {
    'dpid': int(SWITCH_DPID), 'priority': flow_priority,
    'match': {'eth_type': 2048, 'ipv4_src': f'{client_ip}/32'},
    'instructions': [{'type': 'APPLY_ACTIONS', 'actions': [{'type': 'OUTPUT', 'port': 'NORMAL'}]}]
}
response = requests.post(f'{RYU_BASE_URL}/stats/flowentry/add', json=payload, timeout=3)
print('Ryu response:', response.status_code, response.text)
response.raise_for_status()
print(f'Installed priority {flow_priority} for {client_ip}')
