import cv2
import torch
import numpy as np
import threading
import queue
import os
import socket
import struct
import io
import sys
from PIL import Image
from time import time, sleep
from torchvision.transforms import CenterCrop, Normalize, Compose, Lambda
from pytorchvideo.transforms import ApplyTransformToKey, ShortSideScale
from skimage.metrics import structural_similarity as ssim
from model import Model


from option import parse_args
args = parse_args()
SERVER_IP = args.server_ip
PORT = args.port
print(SERVER_IP)
print(PORT)


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")


feat_model_name = 'x3d_l'
feat_model = torch.hub.load('facebookresearch/pytorchvideo', feat_model_name, pretrained=True)
feat_model = feat_model.eval()
feat_model = feat_model.to(DEVICE)
del feat_model.blocks[-1]  


mean = [0.45, 0.45, 0.45]
std = [0.225, 0.225, 0.225]
model_transform_params = {
    "x3d_xs": {"side_size": 182, "crop_size": 182, "num_frames": 4, "sampling_rate": 12},
    "x3d_s": {"side_size": 182, "crop_size": 182, "num_frames": 13, "sampling_rate": 6},
    "x3d_m": {"side_size": 256, "crop_size": 256, "num_frames": 16, "sampling_rate": 5},
    "x3d_l": {"side_size": 320, "crop_size": 320, "num_frames": 16, "sampling_rate": 5},
}

transform_params = model_transform_params[feat_model_name]
transform = ApplyTransformToKey(
    key="video",
    transform=Compose(
        [
            Lambda(lambda x: x / 255.0),
            Normalize(mean, std),
            ShortSideScale(size=transform_params["side_size"]),
            CenterCrop((transform_params["crop_size"], transform_params["crop_size"])),
            Lambda(lambda x: x.permute((1, 0, 2, 3)))
        ]
    ),
)


CHECKPOINT_PATH = "saved_models/888tiny.pkl"  
THRESHOLD = 0.6934
FRAME_COUNT = 16  
SIMILARITY_THRESHOLD = 0.7


process_queue = queue.Queue(maxsize=FRAME_COUNT * 3)
result_queue = queue.Queue(maxsize=100)
pause_event = threading.Event()

#UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, PORT))
print(f"📡 Listening for UDP video at {SERVER_IP}:{PORT}...")

buffer = {}
expected_packets = {}
received_packets = {}

def load_checkpoint(model, checkpoint_path):
    checkpoint = torch.load(checkpoint_path, map_location=DEVICE, weights_only=True)
    model.load_state_dict(checkpoint, strict=False)
    print("Checkpoint loaded successfully!")

def draw_text_overlay(frame, text, org, font=cv2.FONT_HERSHEY_SIMPLEX, 
                      font_scale=2.0, text_color=(255, 255, 255), 
                      bg_color=(0, 0, 0), thickness=3, padding=5, alpha=0.6):
    overlay = frame.copy()
    (w, h), _ = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = org
    cv2.rectangle(overlay, (x - padding, y - h - padding), (x + w + padding, y + padding), bg_color, -1)
    cv2.putText(overlay, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def video_to_tensor(frames):
    frames = np.stack([frame for frame in frames], axis=0)  # Shape: (num_frames, H, W, 3)
    tensor = torch.from_numpy(frames).permute(0, 3, 1, 2).float()  # Shape: (num_frames, 3, H, W)
    return tensor

def receive_and_display_video():
    frame_index = 0
    batch_index = 0
    results_map = {} 
    window_initialized = False  

    print("Waiting for first UDP packet...")
    while True:
       
        packet, addr = sock.recvfrom(65535)
        print(f"Received packet from addr: {addr}")
        if not isinstance(addr, tuple) or len(addr) != 2:
            print(f"Invalid addr format: {addr}, skipping...")
            continue
        if len(packet) < 8:
            print(f"Invalid packet size: {len(packet)} bytes, skipping...")
            continue

       
        if not window_initialized:
            print("Received first UDP packet, initializing video window...")
            cv2.namedWindow("Anomaly Detection", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Anomaly Detection", 1024, 768)
            window_initialized = True

      
        i, total = struct.unpack('!II', packet[:8])
        data = packet[8:]

        buffer_key = addr 
        if buffer_key not in buffer:
            buffer[buffer_key] = {}
            expected_packets[buffer_key] = total
            received_packets[buffer_key] = 0

        if i not in buffer[buffer_key]:
            buffer[buffer_key][i] = data
            received_packets[buffer_key] += 1

       
        if received_packets[buffer_key] == expected_packets[buffer_key]:
            chunks = [buffer[buffer_key][j] for j in range(total)]
            image_data = b''.join(chunks)

         
            try:
                stream = io.BytesIO(image_data)
                image = Image.open(stream)
                frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"Error decoding image: {e}")
                if buffer_key in buffer:
                    del buffer[buffer_key]
                if buffer_key in expected_packets:
                    del expected_packets[buffer_key]
                if buffer_key in received_packets:
                    del received_packets[buffer_key]
                continue

          
            frame_added = False
            try:
                process_queue.put_nowait((frame, frame_index))
                frame_added = True
                print(f"Frame {frame_index} added to process_queue, queue size: {process_queue.qsize()}")
            except queue.Full:
                print(f"Queue full, skipping frame {frame_index}")

            while not result_queue.empty():
                try:
                    batch_idx, prob = result_queue.get_nowait()
                    results_map[batch_idx] = prob
                except queue.Empty:
                    break
            
          
            current_batch = frame_index // FRAME_COUNT
            current_result = None
            
            for i in range(current_batch, -1, -1):
                if i in results_map:
                    current_result = results_map[i]
                    break
            
      
            if current_result is not None:
                if current_result > THRESHOLD:
                    color = (0, 0, 255) 
                    status = "Khong binh thuong"
                else:
                    color = (0, 255, 0)  
                    status = "Binh thuong"
                anomaly_text = f"Batch: {current_batch} | Prob: {current_result:.4f} | {status}"
                cv2.rectangle(frame, (0, 0), (frame.shape[1]-2, frame.shape[0]-2), color, 2)
                draw_text_overlay(frame, anomaly_text, (10, 20), font_scale=0.4, thickness=1, alpha=0.6, text_color=color)
            else:
                draw_text_overlay(frame, f"Batch: {current_batch} | Calculating...", (10, 20), 
                                font_scale=0.4, thickness=1, alpha=0.6, text_color=(255, 255, 0))

       
            if frame_added:
                frame_index += 1
                if frame_index % FRAME_COUNT == 0:
                    batch_index += 1

          
            print(f"Displaying frame {frame_index}")
            cv2.imshow("Anomaly Detection", frame)
            key_pressed = cv2.waitKey(1) & 0xFF 
            if key_pressed == ord('q'):
                break
            elif key_pressed == ord('p'):
                pause_event.set()
                print("Paused")

            if buffer_key in buffer:
                del buffer[buffer_key]
            if buffer_key in expected_packets:
                del expected_packets[buffer_key]
            if buffer_key in received_packets:
                del received_packets[buffer_key]

    
        if pause_event.is_set():
            key_pressed = cv2.waitKey(30) & 0xFF
            if key_pressed == ord('p'):
                pause_event.clear()
                print("Resume")
            elif key_pressed == ord('q'):
                break

    process_queue.put((None, -1))  
    cv2.destroyAllWindows()
    sock.close()
    print("🛑 Connection closed.")

def process_inference(feat_model, model):
    batch_frames = []
    current_batch_index = 0
    
    while True:
        if pause_event.is_set():
            sleep(0.1)
            continue

        item = process_queue.get()
        if item[0] is None: 
            break

        frame, frame_index = item
        batch_frames.append(frame)
        
        if len(batch_frames) >= FRAME_COUNT:
            batch_idx = frame_index // FRAME_COUNT
            
            tensor = video_to_tensor(batch_frames).to(DEVICE)
            t_transform = transform({'video': tensor})['video']
            
            with torch.no_grad():
                start_time = time()          
                features = feat_model(t_transform.unsqueeze(0))              
                logits, _ = model(features)
                output = torch.sigmoid(logits).item()
                print(f"Batch {batch_idx}: Prob {output:.4f}, Processing time: {time() - start_time:.3f}s")
            
         
            result_queue.put((batch_idx, output))

            batch_frames.clear()
            current_batch_index += 1

if __name__ == '__main__':
  
    model = Model().to(DEVICE)
    if os.path.exists(CHECKPOINT_PATH):
        print("Loading checkpoint...")
        load_checkpoint(model, CHECKPOINT_PATH)
    else:
        print("Could not load checkpoint!")
    model.eval()

    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True

 
    thread_display = threading.Thread(target=receive_and_display_video)
    thread_inference = threading.Thread(target=process_inference, args=(feat_model, model))

    thread_display.start()
    thread_inference.start()

    thread_display.join()
    thread_inference.join()