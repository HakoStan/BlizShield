import socket
import threading

from .main import PortScanner


def test_tcp_port_scan_false():
    port_scanner = PortScanner("127.0.0.1", 8080, 8081)
    result = port_scanner.execute()

    assert result[0]["protocol"] == "TCP"
    assert result[0]["port_open"] == False


def test_tcp_port_scan_true():
    port_scanner = PortScanner("127.0.0.1", 8080, 8081)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 8080))
    s.listen(1)
    result = port_scanner.execute()
    s.close()

    assert result[0]["protocol"] == "TCP"
    assert result[0]["port_open"] == True


def udp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 8080))
    while True:
        bytes_and_addr = s.recvfrom(1024)
        s.sendto(bytes(0), bytes_and_addr[1])
        break
    s.close()


def test_udp_port_scan_false():
    port_scanner = PortScanner("127.0.0.1", 8080, 8081)
    result = port_scanner.execute()

    assert result[1]["protocol"] == "UDP"
    assert result[1]["port_open"] == False


def test_udp_port_scan_true():
    port_scanner = PortScanner("127.0.0.1", 8080, 8081)
    th = threading.Thread(target=udp_server)
    th.start()
    result = port_scanner.execute()
    th.join()

    assert result[1]["protocol"] == "UDP"
    assert result[1]["port_open"] == True