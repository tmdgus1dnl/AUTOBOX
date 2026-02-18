# 1. 기존 PyTorch 제거
pip uninstall torch torchvision torchaudio -y

# 2. CUDA 버전 PyTorch 먼저 설치
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. 나머지 패키지 설치
pip install -r requirements.txt