# udp_client_for_anomaly_detection.py
import io
import socket
import struct
import sys
import time
import threading
from picamera2 import Picamera2
from PIL import Image

# Constants
CHUNK_SIZE = 60000
TARGET_FPS = 20  # Lower FPS for better reliability
FRAME_INTERVAL = 1.0 / TARGET_FPS
RESOLUTION = (320, 240)  # Match the model's expected input resolution

if len(sys.argv) < 3:
    print("Usage: python3 udp_client_for_anomaly_detection.py <SERVER_IP> <PORT>")
    sys.exit(1)

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
addr = (server_ip, server_port)

# Setup UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Setup PiCamera
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration(main={"size": RESOLUTION}))
picam2.start()
time.sleep(2)  # Camera warm-up

print(f"📷 Starting to send video frames via UDP to {server_ip}:{server_port}...")

# Shared variable for the latest frame data
latest_frame_data = None
frame_ready = threading.Event()

# Stats variables
frames_captured = 0
frames_sent = 0
last_stats_time = time.time()

# Thread for capturing frames
def capture_thread():
    global latest_frame_data, frames_captured
    
    while True:
        try:
            # Capture frame
            frame = picam2.capture_array()
            
            # Convert to PIL Image for JPEG compression
            image = Image.fromarray(frame)
            
            # Compress to JPEG
            stream = io.BytesIO()
            image.save(stream, format='JPEG', quality=80)  # Adjust quality as needed
            
            # Update shared variable
            latest_frame_data = stream.getvalue()
            frames_captured += 1
            
            # Signal that a new frame is ready
            frame_ready.set()
            
            # Sleep to maintain target FPS
            time.sleep(0.01)  # Small sleep to prevent CPU hogging
            
        except Exception as e:
            print(f"Error in capture thread: {e}")
            time.sleep(0.1)

# Thread for sending frames
def sender_thread():
    global latest_frame_data, frames_sent, last_stats_time
    
    while True:
        # Wait for a new frame
        frame_ready.wait()
        frame_ready.clear()
        
        start_time = time.time()
        
        # Get current frame data
        data = latest_frame_data
        if data is None:
            continue
            
        try:
            # Split data into chunks
            total_packets = (len(data) + CHUNK_SIZE - 1) // CHUNK_SIZE
            
            # Send each chunk
            for i in range(total_packets):
                chunk = data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
                header = struct.pack('!II', i, total_packets)
                sock.sendto(header + chunk, addr)
            
            frames_sent += 1
            
            # Print stats every second
            now = time.time()
            if now - last_stats_time >= 1.0:
                elapsed = now - last_stats_time
                capture_fps = frames_captured / elapsed
                send_fps = frames_sent / elapsed
                print(f"Stats: {capture_fps:.1f} fps captured, {send_fps:.1f} fps sent")
                frames_captured = 0
                frames_sent = 0
                last_stats_time = now
            
            # Calculate time to next frame
            elapsed_time = time.time() - start_time
            sleep_time = FRAME_INTERVAL - elapsed_time
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        except Exception as e:
            print(f"Error in sender thread: {e}")
            time.sleep(0.1)

# Start threads
capture_thread = threading.Thread(target=capture_thread, daemon=True)
sender_thread = threading.Thread(target=sender_thread, daemon=True)

capture_thread.start()
sender_thread.start()

# Keep main thread running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down...")
    sys.exit(0)