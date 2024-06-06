import datetime
from socket import *
import struct
import time
from statistics import mean, stdev


BUFSIZE = 1024
SERVER_IP = "127.0.0.1"  # 127.0.0.1本机测试
SERVER_PORT = 20000  # 20000测试端口
SERVER_ADDR = (SERVER_IP, SERVER_PORT)  # 绑定成元组
PACKET_NUM = 12  # 发送的数据包数量
setdefaulttimeout(0.1)  # 设置全局超时时间100ms
CONNECT_FLAG = 0  # 连接是否建立成功


# 封装报文
def pack(sequence_no, ver, flag, realdata, non_data):
    return struct.pack('!H B 50s 50s 100s', sequence_no, ver, flag, realdata, non_data)


# 解封装报文
def unpack(message):
    return struct.unpack('!H B 50s 50s 100s', message)


# 模拟tcp建立连接
def connect():
    re_cnt = 0  # 重传次数
    while True:
        try:
            client_socket.sendto(pack(0, 2, b'SYN1', b'x' * 50, b'x' * 100), SERVER_ADDR)  # 发送SYN报文请求建立连接
            data, addr = client_socket.recvfrom(BUFSIZE)
            if unpack(data)[2].decode().strip(b'\x00'.decode()) == 'SYN+ACK1':  # 收到建立连接的SYN+ACK报文
                client_socket.sendto(pack(1, 2, b'ACK1', b'x' * 50, b'x' * 100), SERVER_ADDR)  # 发送ACK报文进行第三次握手
                print("correct connect")
                global CONNECT_FLAG
                CONNECT_FLAG = 1
            else:
                print("incorrect connect")
            break
        except timeout:  # 超时，没有收到响应报文
            re_cnt += 1
            if re_cnt > 2:
                print("fail connect")
                break


# 通信
def communicate():
    all_rtt = []
    packet_num = 0
    first_response = 0
    last_response = 0
    for seq_no in range(1, PACKET_NUM + 1):
        re_cnt = 0  # 重传次数
        realdata = input("请输入要发送的信息：")
        while True:
            try:
                client_socket.sendto(pack(seq_no, 2, b'REQUEST2', realdata.encode(),  b'x' * 100), SERVER_ADDR)  # 发送REQUEST报文
                start_time = time.time()
                data, addr = client_socket.recvfrom(BUFSIZE)  # 接收RESPONSE报文
                end_time = time.time()
                rtt = (end_time - start_time) * 1000  # 计算往返时延RTT
                all_rtt.append(rtt)
                packet_num += 1  # 收到的包数量+1
                times = unpack(data)[3].decode().strip(b'\x00'.decode())
                if first_response == 0:
                    first_response = times  # 第一次响应时间
                last_response = times  # 最后一次响应时间
                print(f"sequence no: {unpack(data)[0]}, serverIP: {addr[0]}, serverPort: {addr[1]}, Time: {times}, RTT: {round(rtt, 4)} ms")
                break
            except timeout:  # 超时，没有收到响应报文
                re_cnt += 1
                if re_cnt > 2:  # 最多重传2次
                    print(f"sequence no: {seq_no}, request time out!")
                    break
    if all_rtt:  # 计算相关数据
        print("\n")
        print(f"Received {packet_num} udp packets")
        print(f"Loss rate: {((PACKET_NUM - packet_num) / PACKET_NUM) * 100:.2f}%")
        std_rtt = all_rtt[0]
        if len(all_rtt) > 1:
            std_rtt = stdev(all_rtt)
        print(f"RTT max: {max(all_rtt):.2f} ms, RTT min: {min(all_rtt):.2f} ms, RTT average: {mean(all_rtt):.2f} ms, RTT std dev: {std_rtt:.2f} ms")
        print(f"Total response time: {(datetime.datetime.strptime(last_response, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(first_response, '%Y-%m-%d %H:%M:%S')).total_seconds()} seconds")
    else:
        print("Received no packets")


# 模拟tcp释放连接
def disconnect():
    client_socket.sendto(pack(PACKET_NUM + 1, 2, b'FIN+ACK3', b'disconnect', b'x' * 100), SERVER_ADDR)  # 发送FIN+ACK报文请求释放连接
    data, addr = client_socket.recvfrom(BUFSIZE)
    if unpack(data)[2].decode().strip(b'\x00'.decode()) == 'ACK3':  # 收到释放连接的ACK的报文
        data, addr = client_socket.recvfrom(BUFSIZE)
        if unpack(data)[2].decode().strip(b'\x00'.decode()) == 'FIN+PSH+ACK3':  # 收到释放连接的FIN+PSH+ACK的报文
            client_socket.sendto(pack(PACKET_NUM + 2, 2, b'ACK3', b'x' * 50, b'x' * 100), SERVER_ADDR)  # 发送ACK报文请求释放连接
            client_socket.close()
            print("correct disconnect")
        else:
            print("incorrect disconnect")
    else:
        print("incorrect disconnect")


if __name__ == '__main__':
    SERVER_IP = input("请输入连接的serverIP：")
    SERVER_PORT = int(input("请输入连接的serverPort："))
    PACKET_NUM = int(input("请输入要发送的数据包数量："))
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)
    client_socket = socket(AF_INET, SOCK_DGRAM)
    connect()
    if CONNECT_FLAG:
        communicate()
        disconnect()
