#!/usr/bin/env python3
"""
운송장 VLM 학습용 합성 데이터 생성기

사용법:
    python generate_waybill_data.py --count 5000 --template /path/to/waybill_template.jpg
    
필수 파일:
    - waybill_template.jpg (운송장 템플릿 이미지)
    
필수 라이브러리:
    pip install Pillow faker tqdm requests
"""

import os
import json
import random
import requests
import shutil
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from faker import Faker
from tqdm import tqdm


# --- 기본 설정 ---
DEFAULT_BASE_DIR = "./"
DEFAULT_TEMPLATE = "img/waybill_template.jpg"
DEFAULT_COUNT = 10


def download_fonts(fonts_dir: Path):
    """한글 폰트 다운로드"""
    FONT_URLS = {
        "NanumGothicBold": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf",
        "DoHyeon": "https://github.com/google/fonts/raw/main/ofl/dohyeon/DoHyeon-Regular.ttf",
    }
    
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    for name, url in FONT_URLS.items():
        font_path = fonts_dir / f"{name}.ttf"
        if not font_path.exists():
            print(f"📥 폰트 다운로드 중: {name}")
            try:
                r = requests.get(url, timeout=30)
                r.raise_for_status()
                with open(font_path, 'wb') as f:
                    f.write(r.content)
                print(f"   ✅ {name} 다운로드 완료")
            except Exception as e:
                print(f"   ⚠️ {name} 다운로드 실패: {e}")


def get_font(fonts_dir: Path) -> str:
    """랜덤 폰트 선택"""
    fonts = list(fonts_dir.glob("*.ttf"))
    return str(random.choice(fonts)) if fonts else "arial.ttf"


class VLMDataGenerator:
    """운송장 이미지 + JSON 데이터 생성기"""
    
    def __init__(self, template_path: str, fonts_dir: Path):
        if not Path(template_path).exists():
            raise FileNotFoundError(f"❌ 템플릿 파일이 없습니다: {template_path}")
        
        self.bg = Image.open(template_path).convert("RGB")
        self.fonts_dir = fonts_dir
        self.fake = Faker('ko_KR')
        
        # 텍스트 위치 좌표 (x1, y1, x2, y2)
        self.positions = {
            'tracking_number': (16, 191, 218, 241),     # 운송장번호
            'region_code': (443, 170, 628, 238),        # 분류코드
            'recipient_name': (60, 258, 200, 312),      # 받는분 이름
            'recipient_address': (15, 320, 630, 375),   # 받는분 주소
            'sender_name': (92, 394, 221, 454),         # 보내는분 이름
            'sender_address': (12, 458, 632, 537)       # 보내는분 주소
        }
        
        # 한글 키 → 영문 좌표 키 매핑
        self.key_map = {
            "운송장번호": 'tracking_number',
            "분류코드": 'region_code',
            "받는분": 'recipient_name',
            "받는분주소": 'recipient_address',
            "보내는분": 'sender_name',
            "보내는분주소": 'sender_address'
        }

    def render(self) -> tuple[Image.Image, dict]:
        """운송장 이미지 1장 생성"""
        img = self.bg.copy()
        draw = ImageDraw.Draw(img)
        
        # 랜덤 데이터 생성
        data = {
            "운송장번호": ''.join([str(random.randint(0, 9)) for _ in range(12)]),
            "분류코드": f"{self.fake.city()[:2]}{random.randint(1, 9)}",
            "받는분": self.fake.name(),
            "받는분주소": self.fake.address(),
            "보내는분": self.fake.name(),
            "보내는분주소": self.fake.address()
        }
        
        font_path = get_font(self.fonts_dir)
        
        for key, text in data.items():
            if key not in self.key_map:
                continue
            
            x1, y1, x2, y2 = self.positions[self.key_map[key]]
            box_width = x2 - x1
            box_height = y2 - y1
            
            # 폰트 크기 자동 조절 (박스에 맞게)
            size = 50
            font = ImageFont.truetype(font_path, size)
            
            while (font.getlength(text) > box_width or size > box_height) and size > 10:
                size -= 2
                font = ImageFont.truetype(font_path, size)
            
            # 텍스트 그리기
            draw.text((x1 + 5, y1 + 2), text, font=font, fill=(30, 30, 30))
        
        return img, data


def generate_dataset(
    template_path: str,
    output_dir: str,
    count: int,
    llama_factory_path: str = None
):
    """데이터셋 생성 메인 함수"""
    
    data_dir = Path(output_dir) / "data_vlm"
    images_dir = data_dir / "images"
    fonts_dir = Path(output_dir) / "fonts"
    
    # 기존 데이터 삭제 후 재생성
    if data_dir.exists():
        shutil.rmtree(data_dir)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # 폰트 다운로드
    print("\n📦 폰트 준비 중...")
    download_fonts(fonts_dir)
    
    # 생성기 초기화
    print("\n🔧 데이터 생성기 초기화...")
    generator = VLMDataGenerator(template_path, fonts_dir)
    
    # 데이터 생성
    print(f"\n🚀 운송장 데이터 {count}장 생성 중...")
    llama_data = []
    
    for i in tqdm(range(count)):
        img, json_data = generator.render()
        
        filename = f"{i:05d}.jpg"
        img_path = images_dir / filename
        img.save(img_path)
        
        entry = {
            "messages": [
                {
                    "role": "user",
                    "content": "<image>이 운송장 이미지에서 정보를 추출하여 JSON 형식으로 출력해줘."
                },
                {
                    "role": "assistant",
                    "content": json.dumps(json_data, ensure_ascii=False)
                }
            ],
            "images": [str(img_path)]
        }
        llama_data.append(entry)
    
    # JSON 저장
    train_file = data_dir / "train_data.json"
    with open(train_file, "w", encoding='utf-8') as f:
        json.dump(llama_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 데이터 생성 완료!")
    print(f"   📁 이미지: {images_dir}")
    print(f"   📄 JSON: {train_file}")
    
    # LLaMA-Factory 등록 (옵션)
    if llama_factory_path:
        register_to_llama_factory(str(train_file), llama_factory_path)
    
    return str(train_file)


def register_to_llama_factory(train_file: str, llama_factory_path: str):
    """LLaMA-Factory dataset_info.json에 등록"""
    
    info_path = Path(llama_factory_path) / "data" / "dataset_info.json"
    
    if not info_path.exists():
        print(f"⚠️ LLaMA-Factory 경로를 찾을 수 없습니다: {info_path}")
        return
    
    dataset_info = {
        "waybill_vlm": {
            "file_name": train_file,
            "formatting": "sharegpt",
            "columns": {
                "messages": "messages",
                "images": "images"
            },
            "tags": {
                "role_tag": "role",
                "content_tag": "content",
                "user_tag": "user",
                "assistant_tag": "assistant"
            }
        }
    }
    
    with open(info_path, "r", encoding='utf-8') as f:
        original_info = json.load(f)
    
    original_info.update(dataset_info)
    
    with open(info_path, "w", encoding='utf-8') as f:
        json.dump(original_info, f, indent=2, ensure_ascii=False)
    
    print(f"   🔗 LLaMA-Factory 등록 완료: {info_path}")


def main():
    parser = argparse.ArgumentParser(
        description="운송장 VLM 학습용 합성 데이터 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    # 기본 실행 (5000장)
    python generate_waybill_data.py
    
    # 1000장만 생성
    python generate_waybill_data.py --count 1000
    
    # 커스텀 경로 지정
    python generate_waybill_data.py --template ./my_template.jpg --output ./my_data
    
    # LLaMA-Factory에 자동 등록
    python generate_waybill_data.py --llama-factory /content/LLaMA-Factory
        """
    )
    
    parser.add_argument(
        '--template', '-t',
        type=str,
        default=DEFAULT_TEMPLATE,
        help=f'운송장 템플릿 이미지 경로 (기본값: {DEFAULT_TEMPLATE})'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=DEFAULT_BASE_DIR,
        help=f'출력 디렉토리 (기본값: {DEFAULT_BASE_DIR})'
    )
    
    parser.add_argument(
        '--count', '-n',
        type=int,
        default=DEFAULT_COUNT,
        help=f'생성할 이미지 개수 (기본값: {DEFAULT_COUNT})'
    )
    
    parser.add_argument(
        '--llama-factory', '-l',
        type=str,
        default=None,
        help='LLaMA-Factory 경로 (지정시 자동 등록)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("🏷️  운송장 VLM 데이터 생성기")
    print("="*60)
    print(f"   템플릿: {args.template}")
    print(f"   출력 경로: {args.output}")
    print(f"   생성 개수: {args.count}장")
    if args.llama_factory:
        print(f"   LLaMA-Factory: {args.llama_factory}")
    
    generate_dataset(
        template_path=args.template,
        output_dir=args.output,
        count=args.count,
        llama_factory_path=args.llama_factory
    )
    
    print("\n" + "="*60)
    print("🎉 완료!")
    print("="*60)


if __name__ == "__main__":
    main()