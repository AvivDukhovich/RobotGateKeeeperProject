from scapy.all import (
    sniff, IP, TCP, UDP, ICMP, ARP,
    DNS, DNSRR
)
from scapy.layers.tls.handshake import TLSClientHello
from scapy.layers.tls.record import TLS
from datetime import datetime
from collections import defaultdict
import threading
import msvcrt
import sys

# =========================
# GLOBAL STATE
# =========================
stop_sniffing = False

# IP -> domain cache (DNS + TLS SNI)
name_cache = {}

# Flow table
flows = defaultdict(lambda: {
    "first_seen": None,
    "last_seen": None,
    "packets": 0,
    "bytes": 0,
    "protocol": ""
})

# =========================
# KEYBOARD LISTENER
# =========================


def keyboard_listener():
    global stop_sniffing
    print("\nPress 's' to stop capturing.\n")

    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch().lower()
            if key == b's':
                print("\n[*] Stop signal received. Exiting...")
                stop_sniffing = True
                break

# =========================
# FLOW IDENTIFICATION
# =========================


def get_flow_key(pkt):
    if IP in pkt:
        if TCP in pkt:
            return (pkt[IP].src, pkt[TCP].sport,
                    pkt[IP].dst, pkt[TCP].dport, "TCP")
        elif UDP in pkt:
            return (pkt[IP].src, pkt[UDP].sport,
                    pkt[IP].dst, pkt[UDP].dport, "UDP")
        elif ICMP in pkt:
            return (pkt[IP].src, 0,
                    pkt[IP].dst, 0, "ICMP")
    elif ARP in pkt:
        return (pkt[ARP].psrc, 0,
                pkt[ARP].pdst, 0, "ARP")
    return None

# =========================
# PACKET HANDLER
# =========================


def packet_callback(pkt):
    if stop_sniffing:
        sys.exit(0)

    now = datetime.now().strftime("%H:%M:%S")

    # -------- DNS RESPONSE PARSING --------
    if pkt.haslayer(DNS) and pkt.haslayer(DNSRR):
        dns = pkt[DNS]
        if dns.qr == 1:  # response
            for i in range(dns.ancount):
                rr = dns.an[i]
                if rr.type == 1:  # A record
                    domain = rr.rrname.decode().strip(".")
                    ip = rr.rdata
                    name_cache[ip] = domain

    # -------- TLS SNI PARSING (HTTPS DOMAINS) --------
    if pkt.haslayer(TLS) and pkt.haslayer(TLSClientHello):
        try:
            ch = pkt[TLSClientHello]
            for ext in ch.ext:
                if ext.name == "server_name":
                    for sni in ext.servernames:
                        domain = sni.servername.decode()
                        ip = pkt[IP].dst
                        name_cache[ip] = domain
        except:
            pass

    key = get_flow_key(pkt)
    if not key:
        return

    flow = flows[key]

    if flow["first_seen"] is None:
        flow["first_seen"] = now
        flow["protocol"] = key[4]

    flow["last_seen"] = now
    flow["packets"] += 1
    flow["bytes"] += len(pkt)

    src_ip, src_port, dst_ip, dst_port, proto = key

    src_name = name_cache.get(src_ip, "")
    dst_name = name_cache.get(dst_ip, "")

    def fmt(ip, name):
        return f"{ip} ({name})" if name else ip

    print(
        f"[{now}] {proto:<4} "
        f"{fmt(src_ip, src_name)}:{src_port} -> "
        f"{fmt(dst_ip, dst_name)}:{dst_port} | "
        f"pkts={flow['packets']} bytes={flow['bytes']}"
    )


# =========================
# MAIN
# =========================
print("=== RobotGateKeeper Flow Analyzer ===")
print("Capturing all traffic (DNS + TLS SNI enriched)...")

threading.Thread(target=keyboard_listener, daemon=True).start()

sniff(prn=packet_callback, store=False)
