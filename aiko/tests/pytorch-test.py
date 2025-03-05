# test pytorch installation
#
import torch

print(f"PyTorch version: {torch.__version__}")

# test pytorch with cuda
#
print(f"Is CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")

# test pytorch with cpu
#
print(f"CPU count: {torch.cuda.device_count()}")
print(f"CPU device name: {torch.cuda.get_device_name(0)}")

# test pytorch with tensor
#
x = torch.tensor([5.5, 3])
print(f"Tensor x: {x}")

# test pytorch with tensor on cuda
#

if torch.cuda.is_available():
    device = torch.device("cuda")
    y = torch.ones_like(x, device=device)
    x = x.to(device)
    z = x + y
    print(f"Tensor z: {z}")
    print(f"Tensor z on CPU: {z.to('cpu', torch.double)}")
    
# test some operations
A = torch.rand(128, 128)
B = torch.rand(128, 128)
C = A * B

if torch.cuda.is_available():
    device = torch.device("cuda")
    A_cuda = A.to(device)
    B_cuda = B.to(device)
    C_cuda = A_cuda * B_cuda
    
    is_equal = torch.allclose(C, C_cuda.to('cpu'))
    print(f"Are the results equal: {is_equal}")