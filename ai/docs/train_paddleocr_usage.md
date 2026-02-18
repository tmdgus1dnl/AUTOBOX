# PaddleOCR 파인튜닝 사용법

운송장 OCR 데이터를 전처리하고 PaddleOCR 모델을 파인튜닝합니다.

## 전체 워크플로우

```bash
# 1. 학습 데이터 생성
python generate_ocr_data.py -n 30000 --clear

# 2. 전처리 + 학습 (한 번에 실행)
python train_paddleocr.py
```

---

## 명령어 옵션

### 경로 설정

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--generated-dir` | 생성된 데이터 디렉토리 | `generated` |
| `--output-dir` | PaddleOCR 데이터 출력 디렉토리 | `paddle_data` |
| `--model-dir` | 최종 모델 저장 디렉토리 | `models/paddleocr_korean_finetuned` |

### 학습 설정

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--batch-size` | 배치 크기 | 128 |
| `--epochs` | 에폭 수 | 100 |
| `--lr` | 학습률 | 0.0005 |
| `--train-ratio` | Train/Val 분할 비율 | 0.9 |

### GPU 설정

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--gpu` | 사용할 GPU ID | 7 |
| `--cpu` | CPU 모드로 학습 | False |

### 실행 모드

| 옵션 | 설명 |
|------|------|
| `--preprocess-only` | 전처리만 실행 |
| `--train-only` | 학습만 실행 (전처리 건너뜀) |
| `--eval-only` | 평가만 실행 |
| `--export-only` | 모델 내보내기만 실행 |

---

## 사용 예시

### 1. 전체 실행 (전처리 + 학습)

```bash
python train_paddleocr.py
```

### 2. 전처리만 실행

```bash
python train_paddleocr.py --preprocess-only
```

### 3. 학습만 실행 (전처리 완료 후)

```bash
python train_paddleocr.py --train-only
```

### 4. GPU 지정

```bash
# GPU 7번 사용 (기본값)
python train_paddleocr.py

# 다른 GPU 사용 시
python train_paddleocr.py --gpu 0
```

### 5. CPU 모드

```bash
python train_paddleocr.py --cpu
```

### 6. 학습 설정 변경

```bash
# 배치 크기, 에폭, 학습률 조정
python train_paddleocr.py --batch-size 64 --epochs 50 --lr 0.001
```

### 7. 커스텀 경로

```bash
python train_paddleocr.py \
    --generated-dir my_data \
    --output-dir my_paddle_data \
    --model-dir my_models/custom_ocr
```

---

## 실행 단계

스크립트는 다음 단계를 순차적으로 실행합니다:

1. **데이터 전처리**: 생성된 이미지를 필드별로 크롭하여 PaddleOCR 형식으로 변환
2. **문자 사전 생성**: 학습 데이터의 모든 문자 + 한글 완성형 사전 생성
3. **PaddleOCR 클론**: GitHub에서 PaddleOCR 저장소 클론
4. **사전 학습 모델 다운로드**: 한국어 PP-OCRv3 모델 다운로드
5. **설정 파일 생성**: 학습 설정 YAML 파일 생성
6. **모델 학습**: PaddleOCR 파인튜닝 실행
7. **모델 평가**: 학습된 모델 성능 평가
8. **모델 내보내기**: 추론용 모델로 변환
9. **최종 모델 저장**: 지정된 폴더로 모델 복사

---

## 출력 구조

```
ai/
├── generated/              # 생성된 원본 데이터
│   ├── images/
│   └── labels/
├── paddle_data/            # PaddleOCR 형식 데이터
│   ├── train/
│   │   ├── images/
│   │   └── label.txt
│   ├── val/
│   │   ├── images/
│   │   └── label.txt
│   ├── korean_dict.txt     # 문자 사전
│   └── rec_korean_finetune.yml  # 학습 설정
├── PaddleOCR/              # PaddleOCR 저장소
│   └── output/
│       └── rec_korean_finetune/
│           ├── best_accuracy/
│           └── inference/
└── models/
    └── paddleocr_korean_finetuned/  # 최종 모델
        ├── inference.pdiparams
        ├── inference.pdmodel
        └── korean_dict.txt
```

---

## 파인튜닝된 모델 사용법

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    rec_model_dir='models/paddleocr_korean_finetuned',
    rec_char_dict_path='models/paddleocr_korean_finetuned/korean_dict.txt',
    use_angle_cls=False,
    lang='korean'
)

result = ocr.ocr('your_image.jpg', cls=False)
for line in result[0]:
    bbox, (text, confidence) = line
    print(f"텍스트: {text}, 신뢰도: {confidence:.4f}")
```

---

## 권장 설정

### 데이터 양에 따른 설정

| 데이터 양 | Batch Size | Epochs | 예상 학습 시간 (V100) |
|----------|------------|--------|---------------------|
| 1,000개 | 64 | 50 | ~10분 |
| 10,000개 | 128 | 100 | ~1시간 |
| 30,000개 | 128 | 100 | ~3시간 |

### GPU 메모리에 따른 Batch Size

| GPU 메모리 | 권장 Batch Size |
|-----------|-----------------|
| 8GB | 32~64 |
| 16GB | 64~128 |
| 32GB | 128~256 |

---

## 문제 해결

### GPU 메모리 부족

```bash
# Batch Size 줄이기
python train_paddleocr.py --batch-size 32
```

### 학습이 너무 느릴 때

```bash
# Worker 수 조정 (train_paddleocr.py에서 num_workers 수정)
# 또는 Batch Size 늘리기
python train_paddleocr.py --batch-size 256
```

### 학습 재개

학습이 중단된 경우, PaddleOCR의 checkpoint 기능을 사용하세요:

```bash
cd PaddleOCR
python tools/train.py -c ../paddle_data/rec_korean_finetune.yml \
    -o Global.checkpoints=./output/rec_korean_finetune/latest
```

---

## 필수 패키지

```bash
# PaddlePaddle GPU 버전
pip install paddlepaddle-gpu

# 또는 CPU 버전
pip install paddlepaddle

# PaddleOCR
pip install paddleocr
```
