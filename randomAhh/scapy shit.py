from scapy.layers.inet import IP, ICMP
from scapy.sendrecv import sr1, sniff

def test_scapy():
    print("--- Starting Scapy Test ---")

    # 1. Create and Display a Packet
    # We're stacking an IP layer on top of an ICMP layer
    packet = IP(dst="8.8.8.8")/ICMP()
    print(f"\n[+] Created packet: {packet.summary()}")

    # 2. Send and Receive (Ping)
    # sr1 sends a packet and waits for the first reply
    print("[+] Sending an ICMP Request to Google DNS (8.8.8.8)...")
    reply = sr1(packet, timeout=2, verbose=False)

    if reply:
        print(f"[+] Received reply from: {reply.src}")
        reply.show() # Detailed view of the response
    else:
        print("[-] No response received.")

    # 3. Sniffing
    # Capture 5 packets on your default interface
    print("\n[+] Sniffing 5 packets...")
    packets = sniff(count=5)
    packets.summary()

if __name__ == "__main__":
    test_scapy()