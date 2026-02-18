# api.py - FastAPI 서버로 운송장 정보 추출

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64
from io import BytesIO
from PIL import Image
import os
from dotenv import load_dotenv

from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from peft import PeftModel
import torch

# =====================
# 환경 변수 로드
# =====================
load_dotenv()

# =====================
# 설정
# =====================
ADAPTER_PATH = os.getenv("ADAPTER_PATH", "./model/qwen2_vl_finetuned_ver2")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8082"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") != "*" else ["*"]

# =====================
# FastAPI 앱 생성
# =====================
app = FastAPI(
    title="운송장 정보 추출 API",
    description="운송장 이미지에서 정보를 추출하는 API",
    version="1.0.0"
)

# CORS 설정 (외부 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# 전역 변수 (모델 저장)
# =====================
model = None
processor = None

# =====================
# Request/Response 모델
# =====================
class ImagePathRequest(BaseModel):
    image_path: str

class ImageBase64Request(BaseModel):
    image_base64: str

class PredictionResponse(BaseModel):
    result: str
    success: bool
    message: Optional[str] = None

# =====================
# 디바이스 설정
# =====================
def get_device():
    """최적의 디바이스 반환"""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")

def get_dtype(device):
    """디바이스에 맞는 최적의 dtype 반환"""
    if device.type == "cuda":
        return torch.float16
    elif device.type == "mps":
        # MPS는 float32가 더 안정적이고 빠름
        return torch.float32
    else:
        return torch.float32

# =====================
# 모델 로드 (서버 시작시)
# =====================
@app.on_event("startup")
async def load_model():
    global model, processor
    
    print("🤖 모델 로딩 중...")
    
    device = get_device()
    dtype = get_dtype(device)
    
    print(f"📍 Target Device: {device}")
    print(f"📍 Data Type: {dtype}")
    
    try:
        # device_map을 명시적으로 설정
        if device.type == "mps":
            # MPS: 명시적으로 MPS 디바이스 사용
            base_model = Qwen2VLForConditionalGeneration.from_pretrained(
                "Qwen/Qwen2-VL-2B-Instruct",
                torch_dtype=dtype,
                device_map={"": device}
            )
        elif device.type == "cuda":
            base_model = Qwen2VLForConditionalGeneration.from_pretrained(
                "Qwen/Qwen2-VL-2B-Instruct",
                torch_dtype=dtype,
                device_map="auto"
            )
        else:
            base_model = Qwen2VLForConditionalGeneration.from_pretrained(
                "Qwen/Qwen2-VL-2B-Instruct",
                torch_dtype=dtype
            )
        
        model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
        model = model.merge_and_unload()
        
        # MPS로 명시적 이동 (필요한 경우)
        if device.type == "mps":
            model = model.to(device)
        
        model.eval()
        
        # torch.compile 사용 (PyTorch 2.0+, 속도 향상)
        try:
            if hasattr(torch, 'compile') and device.type in ["cuda", "mps"]:
                model = torch.compile(model, mode="reduce-overhead")
                print("⚡ torch.compile 적용됨 (속도 향상)")
        except Exception as e:
            print(f"⚠️ torch.compile 스킵: {e}")
        
        processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")
        
        print("✅ 모델 로딩 완료!")
        
        # 디바이스 정보 출력
        if device.type == "cuda":
            print(f"� Device: CUDA GPU - {torch.cuda.get_device_name(0)}")
        elif device.type == "mps":
            print(f"� Device: Apple Silicon (MPS) - GPU 가속 활성화!")
        else:
            print(f"📍 Device: CPU")
            
    except Exception as e:
        print(f"❌ 모델 로딩 실패: {str(e)}")
        raise

# =====================
# 추론 함수
# =====================
def extract_info(image: Image.Image) -> str:
    """운송장 이미지에서 정보 추출"""
    
    # 이미지 RGB 변환
    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGB')
    
    # model_test.py와 동일한 프롬프트 사용
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": "이 운송장 이미지에서 정보를 추출하여 JSON 형식으로 출력해줘."},
            ],
        }
    ]
    
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)
    
    # 최적화된 추론 (inference_mode > no_grad)
    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs, 
            max_new_tokens=512,
            do_sample=False,  # 결정적 출력 (더 빠름)
        )
    
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    
    output = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    return output

# =====================
# API 엔드포인트
# =====================
@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "service": "운송장 정보 추출 API",
        "status": "running",
        "model_loaded": model is not None
    }

@app.post("/predict/path", response_model=PredictionResponse)
async def predict_from_path(request: ImagePathRequest):
    """파일 경로로 이미지 추론"""
    
    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="모델이 로드되지 않았습니다.")
    
    try:
        # 이미지 경로 확인
        if not os.path.exists(request.image_path):
            raise HTTPException(status_code=404, detail=f"이미지를 찾을 수 없습니다: {request.image_path}")
        
        # 이미지 로드
        image = Image.open(request.image_path)
        
        # 추론
        result = extract_info(image)
        
        return PredictionResponse(
            result=result,
            success=True,
            message="추출 성공"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추론 중 오류 발생: {str(e)}")

@app.post("/predict/base64", response_model=PredictionResponse)
async def predict_from_base64(request: ImageBase64Request):
    """Base64 인코딩된 이미지로 추론"""
    
    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="모델이 로드되지 않았습니다.")
    
    try:
        # Base64 디코딩
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(BytesIO(image_data))
        
        # 추론
        result = extract_info(image)
        
        return PredictionResponse(
            result=result,
            success=True,
            message="추출 성공"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추론 중 오류 발생: {str(e)}")

@app.post("/predict/upload", response_model=PredictionResponse)
async def predict_from_upload(file: UploadFile = File(...)):
    """업로드된 이미지 파일로 추론"""
    
    if model is None or processor is None:
        raise HTTPException(status_code=503, detail="모델이 로드되지 않았습니다.")
    
    try:
        # 파일 확장자 확인
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
            raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
        
        # 이미지 읽기
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        
        # 추론
        result = extract_info(image)
        
        return PredictionResponse(
            result=result,
            success=True,
            message="추출 성공"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추론 중 오류 발생: {str(e)}")

# =====================
# 서버 실행
# =====================
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 서버 시작: http://{HOST}:{PORT}")
    print(f"📝 API 문서: http://{HOST}:{PORT}/docs")
    print(f"🔧 모델 경로: {ADAPTER_PATH}")
    uvicorn.run(app, host=HOST, port=PORT)
