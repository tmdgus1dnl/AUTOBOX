# app.py

from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from peft import PeftModel
import torch
from PIL import Image
import gradio as gr
import os
import json
import re

# =====================
# 설정
# =====================
ADAPTER_PATH = "./model/qwen2_vl_finetuned"
SUPPORTED_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

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
# JSON 파싱 함수
# =====================
def parse_to_json(raw_output: str) -> dict:
    """모델 출력을 JSON으로 변환"""
    
    result = {
        "tracking_number": "",
        "region_code": "",
        "recipient_name": "",
        "recipient_address": "",
        "sender_name": "",
        "sender_address": ""
    }
    
    # 이미 JSON 형태면 파싱 시도
    try:
        parsed = json.loads(raw_output)
        key_map = {
            "운송장번호": "tracking_number",
            "분류코드": "region_code",
            "받는분": "recipient_name",
            "받는분이름": "recipient_name",
            "받는주소": "recipient_address",
            "받는분주소": "recipient_address",
            "보내는분": "sender_name",
            "보내는분이름": "sender_name",
            "보내는주소": "sender_address",
            "보내는분주소": "sender_address",
        }
        for k, v in parsed.items():
            if k in key_map:
                result[key_map[k]] = v
            elif k in result:
                result[k] = v
        return result
    except:
        pass
    
    # 정규식으로 추출
    patterns = [
        (r"운송장\s*번호[:\s\"]*([^\"\n,}]+)", "tracking_number"),
        (r"tracking_number[:\s\"]*([^\"\n,}]+)", "tracking_number"),
        (r"분류\s*코드[:\s\"]*([^\"\n,}]+)", "region_code"),
        (r"region_code[:\s\"]*([^\"\n,}]+)", "region_code"),
        (r"받는\s*분[:\s\"]*([^\"\n,}]+)", "recipient_name"),
        (r"recipient_name[:\s\"]*([^\"\n,}]+)", "recipient_name"),
        (r"받는\s*주소[:\s\"]*([^\"\n,}]+)", "recipient_address"),
        (r"recipient_address[:\s\"]*([^\"\n,}]+)", "recipient_address"),
        (r"보내는\s*분[:\s\"]*([^\"\n,}]+)", "sender_name"),
        (r"sender_name[:\s\"]*([^\"\n,}]+)", "sender_name"),
        (r"보내는\s*주소[:\s\"]*([^\"\n,}]+)", "sender_address"),
        (r"sender_address[:\s\"]*([^\"\n,}]+)", "sender_address"),
    ]
    
    for pattern, key in patterns:
        match = re.search(pattern, raw_output, re.IGNORECASE)
        if match and not result[key]:
            result[key] = match.group(1).strip().strip('"\'')
    
    return result

# =====================
# 추론 함수
# =====================
def extract_info(image: Image.Image, return_raw: bool = False) -> str:
    """단일 이미지에서 정보 추출"""
    
    if image.mode in ('RGBA', 'LA', 'P'):
        image = image.convert('RGB')
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": """이 운송장 이미지에서 정보를 추출해서 JSON으로 출력해줘.
출력 형식:
{
    "tracking_number": "운송장번호",
    "region_code": "분류코드", 
    "recipient_name": "받는분",
    "recipient_address": "받는주소",
    "sender_name": "보내는분",
    "sender_address": "보내는주소"
}"""},
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
    
    raw_output = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    if return_raw:
        return raw_output
    
    parsed = parse_to_json(raw_output)
    return json.dumps(parsed, ensure_ascii=False, indent=2)

# =====================
# UI 핸들러
# =====================
def process_single_image(image, show_raw):
    if image is None:
        return "", ""
    
    try:
        raw = extract_info(image, return_raw=True)
        parsed = parse_to_json(raw)
        json_output = json.dumps(parsed, ensure_ascii=False, indent=2)
        
        if show_raw:
            return json_output, raw
        return json_output, ""
    except Exception as e:
        return f"❌ 오류: {str(e)}", ""

def process_multiple_images(files):
    if not files:
        return "❌ 파일을 선택해주세요."
    
    all_results = []
    for file in files:
        try:
            if not file.name.lower().endswith(SUPPORTED_EXT):
                continue
            
            image = Image.open(file.name)
            raw = extract_info(image, return_raw=True)
            parsed = parse_to_json(raw)
            parsed["_filename"] = os.path.basename(file.name)
            all_results.append(parsed)
        except Exception as e:
            all_results.append({"_filename": os.path.basename(file.name), "_error": str(e)})
    
    return json.dumps(all_results, ensure_ascii=False, indent=2)

def process_folder(folder_path):
    if not folder_path or not os.path.isdir(folder_path):
        return "❌ 유효한 폴더 경로를 입력해주세요."
    
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(SUPPORTED_EXT)]
    
    if not image_files:
        return "❌ 폴더에 이미지가 없습니다."
    
    all_results = []
    for i, fname in enumerate(sorted(image_files)):
        try:
            image = Image.open(os.path.join(folder_path, fname))
            raw = extract_info(image, return_raw=True)
            parsed = parse_to_json(raw)
            parsed["_filename"] = fname
            all_results.append(parsed)
            print(f"✅ {i+1}/{len(image_files)}: {fname}")
        except Exception as e:
            all_results.append({"_filename": fname, "_error": str(e)})
    
    return json.dumps(all_results, ensure_ascii=False, indent=2)

# =====================
# Gradio UI (6.x 호환)
# =====================
with gr.Blocks(title="운송장 정보 추출기") as app:
    gr.Markdown("# 📦 운송장 정보 추출기")
    
    with gr.Tabs():
        with gr.TabItem("🖼️ 단일 이미지"):
            with gr.Row():
                with gr.Column():
                    single_image = gr.Image(label="이미지 업로드", type="pil", height=400)
                    show_raw = gr.Checkbox(label="원본 출력도 보기", value=False)
                    single_btn = gr.Button("🔍 정보 추출", variant="primary")
                
                with gr.Column():
                    single_output = gr.Textbox(label="JSON 결과", lines=12)
                    raw_output = gr.Textbox(label="원본 출력", lines=5)
            
            single_btn.click(
                fn=process_single_image,
                inputs=[single_image, show_raw],
                outputs=[single_output, raw_output]
            )
        
        with gr.TabItem("📁 여러 이미지"):
            with gr.Row():
                with gr.Column():
                    multi_files = gr.File(label="이미지 파일들", file_count="multiple", file_types=["image"])
                    multi_btn = gr.Button("🔍 전체 추출", variant="primary")
                
                with gr.Column():
                    multi_output = gr.Textbox(label="JSON 결과 (배열)", lines=20)
            
            multi_btn.click(fn=process_multiple_images, inputs=multi_files, outputs=multi_output)
        
        with gr.TabItem("📂 폴더 전체"):
            with gr.Row():
                with gr.Column():
                    folder_input = gr.Textbox(label="폴더 경로", placeholder="예: ./img")
                    folder_btn = gr.Button("🔍 폴더 전체 추출", variant="primary")
                
                with gr.Column():
                    folder_output = gr.Textbox(label="JSON 결과 (배열)", lines=20)
            
            folder_btn.click(fn=process_folder, inputs=folder_input, outputs=folder_output)

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860)