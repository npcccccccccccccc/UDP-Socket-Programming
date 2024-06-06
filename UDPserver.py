import datetime
import random
import threading
from socket import *
import struct
import time

BUFSIZE = 1024
SERVER_IP = "192.168.161.128"  # 127.0.0.1本机测试/192.168.161.128 guest os
SERVER_PORT = 20000  # 20000测试端口
SERVER_ADDR = (SERVER_IP, SERVER_PORT)  # 绑定成元组
setdefaulttimeout(30)  # 设置全局超时时间30s
LOSS_RATE = 0.6  # 丢包率


# 封装报文
def pack(sequence_no, ver, flag, time, data):
    return struct.pack('!H B 50s 50s 100s', sequence_no, ver, flag, time, data)


# 解封装报文
def unpack(message):
    return struct.unpack('!H B 50s 50s 100s', message)


# 接收信息
def recv_mess():
    global data
    global client_addr
    global connect_flag
    global mess_flag
    while True:
        try:
            data, client_addr = server_socket.recvfrom(BUFSIZE)
            mess_flag = 1
            connect_flag = 1
        except timeout:
            print("长时间未收到信息，关闭连接")
            server_socket.close()
            break


# 处理信息
def handle_mess():
    global mess_flag
    while True:
        if connect_flag == 1:
            if mess_flag == 1:
                if unpack(data)[2].decode().strip(b'\x00'.decode()) == 'SYN1':  # 收到申请建立连接的SYN报文
                    times = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    server_socket.sendto(pack(1, 2, b'SYN+ACK1', times.encode(), b'x' * 100),client_addr)  # 发送SYN+ACK报文
                    mess_flag = 0
                elif unpack(data)[2].decode().strip(b'\x00'.decode()) == 'ACK1':  # 收到建立连接的ACK报文
                    print(f"correct connect from{client_addr}")
                    mess_flag = 0
                elif unpack(data)[2].decode().strip(b'\x00'.decode()) == 'REQUEST2':  # 收到带数据的REQUEST报文
                    seq_no = unpack(data)[0]
                    message = unpack(data)[3].decode().strip(b'\x00'.decode())
                    print(f"message:{message} from{client_addr}")
                    if random.random() > LOSS_RATE:  # 模拟丢包
                        times = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        server_socket.sendto(pack(seq_no, 2, b'RESPONSE2', times.encode(), b'x' * 100), client_addr)
                    else:
                        print("this packet loss")
                    mess_flag = 0
                elif unpack(data)[2].decode().strip(b'\x00'.decode()) == 'FIN+ACK3':  # 如果收到请求释放连接的请求
                    times = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    server_socket.sendto(pack(unpack(data)[0], 2, b'ACK3', times.encode(), b'x' * 100), client_addr)
                    server_socket.sendto(pack(unpack(data)[0] + 1, 2, b'FIN+PSH+ACK3', times.encode(), b'x' * 100), client_addr)
                    mess_flag = 0
                elif unpack(data)[2].decode().strip(b'\x00'.decode()) == 'ACK3':  # 收到释放连接的ACK报文
                    print(f"correct disconnect from{client_addr}")
                    mess_flag = 0


if __name__ == '__main__':
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(SERVER_ADDR)
    print("wait connect...")

    data = ""
    client_addr = tuple()
    connect_flag = 0
    mess_flag = 0
    threading.Thread(target=recv_mess).start()  # 接收信息
    threading.Thread(target=handle_mess, daemon=True).start()  # 处理信息
