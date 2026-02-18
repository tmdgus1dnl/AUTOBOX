# 기존 PyTorch 제거
pip uninstall torch torchvision torchaudio -y

# CUDA 12.1 지원 PyTorch 설치 (nvidia-smi에서 확인된 CUDA 버전에 맞게)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121