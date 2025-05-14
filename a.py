import torch
import torchvision
import pytorchvideo

print(torch.__version__)
print(torchvision.__version__)
print(pytorchvideo.__version__)
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU detected")
