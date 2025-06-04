import socket
import cv2
import struct
import time


SERVER_IP = 'localhost' 
SERVER_PORT = 9999

# Thiết lập socket UDP
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Mở webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Không thể mở webcam")
    exit()

print("Đang gửi ảnh từ webcam đến server... Nhấn Ctrl+C để dừng.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không đọc được frame")
            break

       
        frame = cv2.resize(frame, (320, 240))

    
        encoded, buffer = cv2.imencode('.jpg', frame)
        if not encoded:
            continue
        data = buffer.tobytes()

       
        MAX_PACKET_SIZE = 60000  #
        total_packets = (len(data) - 1) // MAX_PACKET_SIZE + 1

        for i in range(total_packets):
            start = i * MAX_PACKET_SIZE
            end = start + MAX_PACKET_SIZE
            chunk = data[start:end]

            header = struct.pack('!II', i, total_packets)
            packet = header + chunk

            client_socket.sendto(packet, (SERVER_IP, SERVER_PORT))

        time.sleep(0.03)  

except KeyboardInterrupt:
    print("Đã dừng gửi")

finally:
    cap.release()
    client_socket.close()
