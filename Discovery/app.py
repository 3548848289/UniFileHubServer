"""UniFileHub 局域网服务发现。

监听 UDP 15000 端口，收到客户端的探测包后，单播应答服务端 IP 以及各
微服务端口。客户端（Qt）启动时广播探测，即可自动配置服务端地址，无需
手动在设置里填写 IP。

应答中的服务端 IP 按客户端逐个解析：对 UDP 套接字 connect 客户端地址
（纯本地路由查询，不发包），取内核为该路由预选的本机源 IP。探测包能
到达本机即说明该路由存在，因此应答的 IP 与客户端必然互通；多网卡、
服务端换 IP / 换网段时无需任何配置或重启。

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

# 特殊需求（如多网卡下想固定只报某个地址）时，用环境变量手动覆盖
# 逐客户端的路由反查结果：
#   docker run -e UNIFILEHUB_LAN_IP=192.168.1.20 ...
# 注意：若以 bridge 网络 + -p 端口映射方式部署，客户端的 UDP 广播
# 进不了容器，发现服务本就无法工作，应改用 --network host。
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


def local_ip_for(client_ip):
    """查询本机与 client_ip 通信时会使用的源 IP（只查路由表，不发包）。

    对 UDP 套接字 connect 不会产生任何网络流量，仅让内核按路由表预选
    一次出口；getsockname() 返回的即该路由使用的本机源地址。
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((client_ip, 9))
        return sock.getsockname()[0]
    except OSError:
        return ""
    finally:
        sock.close()


def detect_lan_ip():
    """探测默认路由出口的局域网 IP（不真正发包）。失败时回退为空。"""
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


def resolve_lan_ip(client_ip):
    """确定应答给该客户端的服务端 IP。

    优先级：环境变量 UNIFILEHUB_LAN_IP（手动覆盖）>
            按客户端地址反查的路由源 IP（自动适配换 IP / 多网卡）>
            默认路由出口 IP（兜底）。
    """
    env_ip = os.environ.get(ENV_LAN_IP, "").strip()
    if env_ip:
        return env_ip

    routed = local_ip_for(client_ip)
    if routed:
        return routed

    detected = detect_lan_ip()
    if detected and is_docker_bridge_ip(detected):
        print(f"[discovery] WARNING: detected docker bridge ip {detected}, "
              f"which is NOT reachable from LAN clients. "
              f"Use --network host, or set {ENV_LAN_IP} to the host LAN ip.")
    return detected


def build_response(ip):
    payload = {
        "magic": MAGIC_RESPONSE,
        "ip": ip,
        "ports": SERVICE_PORTS,
    }
    return json.dumps(payload).encode("utf-8")


def warn_if_bridge_detected():
    """启动自检：未设置覆盖变量却探测到网桥地址时给出部署提示。"""
    if os.environ.get(ENV_LAN_IP, "").strip():
        return

    detected = detect_lan_ip()
    if detected and is_docker_bridge_ip(detected):
        print(f"[discovery] WARNING: detected docker bridge ip {detected}; "
              f"LAN clients cannot reach it. Use --network host (recommended) "
              f"or set {ENV_LAN_IP} to the host LAN ip.")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", LISTEN_PORT))

    warn_if_bridge_detected()
    print(f"[discovery] listening on UDP {LISTEN_PORT}, "
          f"detected ip: {detect_lan_ip() or 'unknown'} "
          f"(reply ip resolved per client)")

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

        ip = resolve_lan_ip(addr[0])
        sock.sendto(build_response(ip), addr)
        print(f"[discovery] replied to {addr[0]}:{addr[1]}, "
              f"announced ip: {ip or '(empty, client falls back to sender ip)'}")


if __name__ == "__main__":
    threading.current_thread().name = "discovery"
    main()
