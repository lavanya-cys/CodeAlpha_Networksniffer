from flask import Flask, render_template, jsonify
from scapy.all import sniff
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.dns import DNS
import threading
import socket

app = Flask(__name__)

packets = []
capture_running = False


def packet_callback(packet):
    global capture_running, packets

    if not capture_running:
        return

    if packet.haslayer(IP):

        protocol = "OTHER"

        if packet.haslayer(DNS):
            protocol = "DNS"
        elif packet.haslayer(ICMP):
            protocol = "ICMP"
        elif packet.haslayer(TCP):
            if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                protocol = "HTTP"
            elif packet[TCP].dport == 443 or packet[TCP].sport == 443:
                protocol = "HTTPS"
            else:
                protocol = "TCP"
        elif packet.haslayer(UDP):
            protocol = "UDP"

        try:
            domain = socket.gethostbyaddr(packet[IP].dst)[0]
        except:
            domain = "Unknown"

        packets.append({
            "source": packet[IP].src,
            "destination": packet[IP].dst,
            "domain": domain,
            "protocol": protocol
        })

        if len(packets) > 100:
            packets.pop(0)


def start_sniffer():
    sniff(prn=packet_callback, store=False, stop_filter=lambda x: not capture_running)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start")
def start_capture():
    global capture_running

    if not capture_running:
        capture_running = True
        threading.Thread(target=start_sniffer, daemon=True).start()

    return jsonify({"status": "Capture Started"})


@app.route("/stop")
def stop_capture():
    global capture_running
    capture_running = False
    return jsonify({"status": "Capture Stopped"})


@app.route("/packets")
def get_packets():
    return jsonify(packets)


if __name__ == "__main__":
    app.run(debug=True)