# OCR 학습 데이터 생성기 사용법

운송장 이미지 템플릿을 기반으로 텍스트만 변경한 합성 이미지와 JSON 라벨 데이터를 생성합니다.

## 기본 사용법

```bash
python generate_ocr_data.py [옵션]
```

## 명령어 옵션

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--count` | `-n` | 생성할 이미지 수 | 10 |
| `--template` | `-t` | 템플릿 이미지 경로 | `img/운송장 예시파일.jpg` |
| `--output` | `-o` | 출력 디렉토리 | `generated` |
| `--font` | `-f` | 폰트 파일 경로 | 시스템 폰트 자동 감지 |
| `--start-index` | - | 시작 인덱스 (이어서 생성 시 사용) | 1 |
| `--effect` | - | 효과 비율 설정 | 없음 |
| `--strength` | - | 효과 강도 (1-20) | 5 |
| `--random-strength` | - | 랜덤 강도 사용 | False |
| `--clear` | - | 기존 파일 삭제 후 새로 생성 | False |

---

## 사용 예시

### 1. 기본 생성 (10개)

```bash
python generate_ocr_data.py
```

### 2. 대량 생성 (30,000개)

```bash
python generate_ocr_data.py -n 30000
```

### 3. 출력 폴더 지정

```bash
python generate_ocr_data.py -n 1000 -o training_data
```

### 4. 기존 데이터 삭제 후 새로 생성

```bash
python generate_ocr_data.py -n 5000 --clear
```

### 5. 이어서 생성 (기존 데이터 유지)

```bash
# 첫 번째 실행: 1~10000번 생성
python generate_ocr_data.py -n 10000

# 두 번째 실행: 10001~20000번 생성 (이어서)
python generate_ocr_data.py -n 10000 --start-index 10001

# 세 번째 실행: 20001~30000번 생성 (이어서)
python generate_ocr_data.py -n 10000 --start-index 20001
```

### 6. 커스텀 템플릿 사용

```bash
python generate_ocr_data.py -n 1000 -t "path/to/custom_template.jpg"
```

### 7. 커스텀 폰트 사용

```bash
python generate_ocr_data.py -n 1000 -f "C:/Windows/Fonts/NanumGothic.ttf"
```

---

## 이미지 효과 설정

### 효과 종류

| 효과명 | 설명 |
|--------|------|
| `none` | 효과 없음 (원본) |
| `blur` | 가우시안 블러 |
| `mosaic` | 모자이크 |
| `noise` | 노이즈 추가 |
| `combined` | 블러 + 노이즈 복합 |

### 효과 적용 예시

```bash
# 블러 50%, 원본 50%
python generate_ocr_data.py -n 1000 --effect "blur:50,none:50"

# 모든 효과 균등 배분
python generate_ocr_data.py -n 1000 --effect "none:25,blur:25,mosaic:25,noise:25"

# 원본만 생성 (효과 없음)
python generate_ocr_data.py -n 1000 --effect "none:100"

# 블러 100%, 강도 10
python generate_ocr_data.py -n 1000 --effect "blur:100" --strength 10

# 랜덤 강도 (1~10 사이)
python generate_ocr_data.py -n 1000 --effect "blur:100" --strength 10 --random-strength
```

---

## 출력 구조

```
generated/
├── images/
│   ├── 00001.jpg
│   ├── 00002.jpg
│   ├── ...
│   └── 30000.jpg
└── labels/
    ├── 00001.json
    ├── 00002.json
    ├── ...
    ├── 30000.json
    └── labels.json  (통합 라벨 파일)
```

### 개별 라벨 파일 형식 (00001.json)

```json
{
  "image_path": "images/00001.jpg",
  "width": 1280,
  "height": 960,
  "fields": [
    {
      "field_name": "tracking_number",
      "text": "12345678",
      "bbox": [35, 115, 440, 210]
    },
    {
      "field_name": "region_code",
      "text": "서울3",
      "bbox": [905, 90, 1265, 220]
    },
    {
      "field_name": "recipient_name",
      "text": "홍길동",
      "bbox": [60, 270, 580, 365]
    },
    {
      "field_name": "recipient_address",
      "text": "서울특별시 강남구 테헤란로 123",
      "bbox": [20, 380, 1260, 490]
    },
    {
      "field_name": "sender_name",
      "text": "김철수",
      "bbox": [80, 520, 580, 615]
    },
    {
      "field_name": "sender_address",
      "text": "부산광역시 해운대구 센텀로 456",
      "bbox": [20, 660, 1260, 760]
    }
  ]
}
```

---

## 영역 설정 (GUI)

텍스트 영역과 마스킹 영역을 조절하려면 `label_editor.py`를 실행하세요:

```bash
python label_editor.py
```

GUI에서 영역을 조절한 후 저장하면 `label_config.json`에 설정이 저장되고,
다음 데이터 생성 시 자동으로 적용됩니다.

---

## 권장 사용법

### 대량 데이터 생성 (30,000개)

```bash
# 방법 1: 한 번에 생성
python generate_ocr_data.py -n 30000 --clear

# 방법 2: 나눠서 생성 (메모리 부족 시)
python generate_ocr_data.py -n 10000 --clear
python generate_ocr_data.py -n 10000 --start-index 10001
python generate_ocr_data.py -n 10000 --start-index 20001
```

### 학습 데이터 품질 향상

```bash
# 원본 70% + 약한 블러 30%
python generate_ocr_data.py -n 30000 --effect "none:70,blur:30" --strength 2
```

---

## 필수 패키지

```bash
pip install Pillow faker
```

또는

```bash
pip install -r requirements.txt
```
