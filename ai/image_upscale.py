import cv2
import os
import argparse
import requests
import time
import shutil
from pathlib import Path
import numpy as np

# 모델 다운로드 정보
MODELS = {
    "fsrcnn_x2": "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x2.pb",
    "fsrcnn_x3": "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x3.pb",
    "fsrcnn_x4": "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x4.pb",
    "edsr_x2": "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x2.pb",
    "edsr_x3": "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x3.pb",
    "edsr_x4": "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x4.pb",
    "espcn_x2": "https://github.com/fannymonori/TF-ESPCN/raw/master/export/ESPCN_x2.pb",
    "espcn_x3": "https://github.com/fannymonori/TF-ESPCN/raw/master/export/ESPCN_x3.pb",
    "espcn_x4": "https://github.com/fannymonori/TF-ESPCN/raw/master/export/ESPCN_x4.pb",
}

def download_model(model_name, model_dir="models"):
    """모델 파일이 없으면 다운로드"""
    if model_name not in MODELS:
        print(f"❌ [Error] 지원하지 않는 모델입니다: {model_name}")
        return None
        
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, f"{model_name}.pb")
    
    if not os.path.exists(model_path):
        url = MODELS[model_name]
        print(f"📥 모델 다운로드 중... ({model_name})")
        print(f"   URL: {url}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(model_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            print("   ✅ 다운로드 완료!")
        except Exception as e:
            print(f"   ❌ 다운로드 실패: {e}")
            return None
            
    return model_path

def upscale_image(image_path, output_path=None, algorithm="fsrcnn", scale=2, use_gpu=True):
    """
    OpenCV DNN Super Resolution을 사용한 이미지 업스케일링
    algorithm: 'fsrcnn' (빠름), 'edsr' (고화질, 느림), 'espcn' (중간)
    scale: 2, 3, 4
    """
    if scale not in [2, 3, 4]:
        print(f"❌ [Error] 지원하지 않는 배율입니다: {scale}x (지원: 2, 3, 4)")
        return

    algo_lower = algorithm.lower()
    model_key = f"{algo_lower}_x{scale}"
    
    # 모델 준비
    model_path = download_model(model_key)
    if not model_path:
        return

    # OpenCV SuperRes 객체 생성
    sr = cv2.dnn_superres.DnnSuperResImpl_create()

    # 모델 읽기 & 설정
    try:
        sr.readModel(model_path)
        sr.setModel(algo_lower, scale)
    except Exception as e:
        print(f"❌ [Error] 모델 로드 실패: {e}")
        return

    # Backend 설정 (GPU 시도)
    if use_gpu:
        try:
            sr.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            sr.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            print("💻 GPU 모드 설정 (CUDA)")
        except Exception:
            print("⚠️ GPU 설정 실패, CPU로 동작합니다.")
            sr.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            sr.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    else:
        print("💻 CPU 모드 사용")

    # 이미지 로드 (한글 경로 지원)
    try:
        # np.fromfile로 읽어서 디코딩
        img_array = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise Exception("이미지 디코딩 실패")
    except Exception as e:
        print(f"❌ [Error] 이미지를 열 수 없습니다: {image_path}")
        print(f"   (오류: {e})")
        return
    
    print(f"📸 원본 크기: {img.shape[1]}x{img.shape[0]}")
    print(f"⏳ 업스케일링 시작 ({algo_lower.upper()} x{scale})...")
    
    start_time = time.time()
    
    # 추론
    result = sr.upsample(img)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✨ 완료! 소요 시간: {duration:.2f}초")
    print(f"📏 결과 크기: {result.shape[1]}x{result.shape[0]}")

    # 저장
    if output_path is None:
        name, ext = os.path.splitext(image_path)
        output_path = f"{name}_upscaled_x{scale}_{algo_lower}{ext}"
        
    try:
        # 한글 경로 지원 저장
        extension = os.path.splitext(output_path)[1]
        result_array = cv2.imencode(extension, result)[1]
        result_array.tofile(output_path)
        print(f"✅ 저장됨: {output_path}")
    except Exception as e:
        print(f"❌ [Error] 저장 실패: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="빠른 AI 이미지 업스케일러 (OpenCV DNN)")
    
    default_img = os.path.join("img", "test12.jpg")
    
    parser.add_argument("image_path", nargs="?", default=default_img, help=f"입력 이미지 경로 (기본값: {default_img})")
    parser.add_argument("--output", "-o", help="출력 파일 경로")
    parser.add_argument("--algo", "-a", default="fsrcnn", choices=["fsrcnn", "edsr", "espcn"], help="알고리즘: fsrcnn(빠름/기본값), edsr(고화질), espcn(균형)")
    parser.add_argument("--scale", "-s", type=int, default=2, choices=[2, 3, 4], help="확대 배율 (2, 3, 4)")
    parser.add_argument("--cpu", action="store_true", help="GPU 대신 CPU 사용 강제")

    args = parser.parse_args()
    
    upscale_image(
        args.image_path, 
        args.output, 
        algorithm=args.algo, 
        scale=args.scale, 
        use_gpu=not args.cpu
    )
