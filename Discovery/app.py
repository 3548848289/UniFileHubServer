"""UniFileHub 局域网服务发现。

监听 UDP 15000 端口，收到客户端的探测包后，单播应答本机局域网 IP
以及各微服务端口。客户端（Qt）启动时广播探测，即可自动配置服务端地址，
无需手动在设置里填写 IP。

协议：
    客户端 -> 广播  : "UniFileHub-DISCOVERY-v1" (UTF-8)
    服务端 -> 单播  : JSON {"magic": "UniFileHub-SERVER-v1", "ip": "...",
                            "ports": {"ip1": 5002, "ip2": 5000, "ip3": 5003,
                                      "ip4": 5001, "clipboard": 5006,
                                      "drive": 5005}}
"""

import json
import os
import socket
import threading

LISTEN_PORT = 15000
MAGIC_REQUEST = "UniFileHub-DISCOVERY-v1"
MAGIC_RESPONSE = "UniFileHub-SERVER-v1"

# Docker 部署时容器内只能探测到网桥地址（如 172.17.0.2），客户端无法访问。
# 此时通过环境变量 UNIFILEHUB_LAN_IP 显式指定宿主机局域网 IP，
# 例如: docker run -e UNIFILEHUB_LAN_IP=192.168.1.20 -p 15000:15000/udp ...
ENV_LAN_IP = "UNIFILEHUB_LAN_IP"

# 与客户端 SettingManager 中各配置键对应的服务端口
SERVICE_PORTS = {
    "ip1": 5002,       # ServerConfig/IP1  (FIleHistory)
    "ip2": 5000,       # ServerConfig/IP2  (SharedFile)
    "ip3": 5003,       # ServerConfig/IP3
    "ip4": 5001,       # ServerConfig/IP4  (UserInfo)
    "clipboard": 5006, # ClipboardSync/ServerIP
    "drive": 5005,     # PersonalDrive/ServerIP
}


def detect_lan_ip():
    """探测本机局域网出口 IP（不真正发包）。失败时回退为空。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.settimeout(0)
        # 向外网地址 connect 不会产生任何流量，仅让系统选择出口网卡
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return ""
    finally:
        sock.close()


DOCKER_BRIDGE_PREFIXES = ("172.17.", "172.18.", "172.19.", "172.2", "172.30.", "172.31.")


def is_docker_bridge_ip(ip):
    return ip.startswith(DOCKER_BRIDGE_PREFIXES)


def resolve_lan_ip():
    """确定应答给客户端的服务端 IP。

    优先级：环境变量 UNIFILEHUB_LAN_IP > 自动探测的出口 IP。
    Docker 容器内自动探测到的是网桥地址，会打警告提示设置环境变量。
    """
    env_ip = os.environ.get(ENV_LAN_IP, "").strip()
    if env_ip:
        return env_ip

    detected = detect_lan_ip()
    if detected and is_docker_bridge_ip(detected):
        print(f"[discovery] WARNING: detected docker bridge ip {detected}, "
              f"which is NOT reachable from LAN clients. "
              f"Set {ENV_LAN_IP} env to the host LAN ip.")
    return detected


def build_response():
    payload = {
        "magic": MAGIC_RESPONSE,
        "ip": resolve_lan_ip(),
        "ports": SERVICE_PORTS,
    }
    return json.dumps(payload).encode("utf-8")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", LISTEN_PORT))
    print(f"[discovery] listening on UDP {LISTEN_PORT}, "
          f"lan ip: {resolve_lan_ip() or 'unknown'}")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
        except OSError:
            continue

        try:
            message = data.decode("utf-8").strip()
        except UnicodeDecodeError:
            continue

        if message != MAGIC_REQUEST:
            continue

        response = build_response()
        sock.sendto(response, addr)
        print(f"[discovery] replied to {addr[0]}:{addr[1]}")


if __name__ == "__main__":
    threading.current_thread().name = "discovery"
    main()
