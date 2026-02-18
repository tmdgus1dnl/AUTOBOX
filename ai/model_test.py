# model_test_vlm.py

from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from peft import PeftModel
import torch
from PIL import Image
import os

# =====================
# 설정
# =====================
# ADAPTER_PATH = "./model/qwen2_vl_finetuned"  # LoRA 어댑터 경로
ADAPTER_PATH = "./model/qwen2_vl_finetuned_ver2"
TEST_IMAGE = "./img/test9.jpg"  # 테스트할 이미지 경로 (jpg, png 모두 가능)

# =====================
# 모델 로드
# =====================
print("🤖 모델 로딩 중...")

base_model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-2B-Instruct",
    torch_dtype=torch.float16,
    device_map="auto"
)

model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model = model.merge_and_unload()
model.eval()

processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")

print("✅ 모델 로딩 완료!")

# 디바이스 정보 출력 (Mac/Windows 호환)
if torch.cuda.is_available():
    print(f"📍 Device: CUDA GPU - {torch.cuda.get_device_name(0)}")
elif torch.backends.mps.is_available():
    print(f"📍 Device: Apple Silicon (MPS)")
else:
    print(f"📍 Device: CPU")

# =====================
# 추론 함수
# =====================
def extract_info(image_path: str) -> str:
    """운송장 이미지에서 정보 추출"""
    
    # 이미지 로드 및 RGB 변환 (PNG 알파채널 처리)
    image = Image.open(image_path)
    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGB')
    
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
    
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=512)
    
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
# 실행
# =====================
if __name__ == "__main__":
    # 지원 확장자
    SUPPORTED_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
    
    # 이미지 경로 확인
    if not os.path.exists(TEST_IMAGE):
        print(f"❌ 이미지를 찾을 수 없습니다: {TEST_IMAGE}")
        print("TEST_IMAGE 경로를 수정해주세요.")
        exit()
    
    if not TEST_IMAGE.lower().endswith(SUPPORTED_EXT):
        print(f"❌ 지원하지 않는 형식입니다. 지원: {SUPPORTED_EXT}")
        exit()
    
    # 이미지 표시
    img = Image.open(TEST_IMAGE)
    print(f"\n📸 테스트 이미지: {TEST_IMAGE}")
    print(f"   크기: {img.size}")
    print(f"   모드: {img.mode}")
    
    # 추론
    print("\n⏳ 분석 중...")
    result = extract_info(TEST_IMAGE)
    
    print("\n" + "="*50)
    print("🎉 추출 결과:")
    print("="*50)
    print(result)