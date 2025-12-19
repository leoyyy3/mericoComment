
from redis import Redis
import socket

host = '192.168.20.17'
port = 6379

def test_raw_socket():
    print(f"Testing raw socket to {host}:{port}...")
    try:
        s = socket.create_connection((host, port), timeout=5)
        print("Socket connected!")
        s.sendall(b"*1\r\n$4\r\nPING\r\n")
        response = s.recv(1024)
        print(f"Raw response: {response}")
        s.close()
    except Exception as e:
        print(f"Raw socket error: {e}")

def test_redis_py():
    print(f"Testing redis-py...")
    try:
        r = Redis(host=host, port=port, socket_timeout=5)
        print(f"Ping: {r.ping()}")
    except Exception as e:
        print(f"redis-py error: {e}")

if __name__ == "__main__":
    test_raw_socket()
    print("-" * 20)
    test_redis_py()
