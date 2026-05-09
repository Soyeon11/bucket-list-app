# 템플릿 시스템 (Template System)

## 개요

쇼츠 영상 생성에 사용되는 시각 스타일 템플릿 정의 파일 모음입니다.  
각 템플릿은 `template.json` 파일로 구성되며, `VideoProcessor`가 런타임에 로드하여 영상에 적용합니다.

## 폴더 구조

```
assets/templates/
├── README.md               # 이 파일 (템플릿 시스템 설명)
├── minimal/
│   └── template.json       # 미니멀 스타일 템플릿
├── vibrant/
│   └── template.json       # 활기찬 컬러 템플릿
└── film/
    └── template.json       # 시네마틱 필름 템플릿
```

## template.json 스키마

각 `template.json`은 아래 최상위 섹션으로 구성됩니다.

```jsonc
{
  "name": "템플릿 식별자 (폴더명과 동일)",
  "display_name": "사용자에게 노출되는 이름 (한국어)",
  "description": "템플릿 설명 (한국어)",
  "version": "1.0.0",

  "background": { ... },      // 인트로/아웃트로 배경 설정
  "text_boxes": { ... },      // 제목·캡션 텍스트 박스 설정
  "media_area": { ... },      // 미디어 클립 배치 영역 설정
  "transition": { ... },      // 클립 간 트랜지션 설정
  "overlay": { ... },         // 오버레이 레이어 설정
  "color_grading": { ... }    // 색상 보정 설정 (선택적)
}
```

## 필드 규칙

- 좌표(x, y)와 크기(width, height): 픽셀 단위 (기준 해상도 1080×1920)
- 색상: HEX 문자열 (`"#RRGGBB"`) 또는 RGBA 배열 (`[R, G, B, A]`, A는 0.0~1.0)
- 비율값(opacity, volume 등): 0.0 ~ 1.0
- 시간(duration 등): 초(float) 단위

## 새 템플릿 추가 방법

1. `assets/templates/<template_name>/` 폴더 생성
2. 위 스키마를 따르는 `template.json` 작성
3. `server/services/video_processor.py`의 `SUPPORTED_TEMPLATES` 목록에 추가
4. `docs/VIDEO_SPEC.md` 섹션 3에 새 템플릿 정보 추가

## 버전 관리

`template.json`의 `version` 필드를 semver 형식으로 관리합니다.  
영상 생성 결과물의 재현성을 위해 `generated_videos.template` 컬럼에 `"minimal@1.0.0"` 형식으로 버전을 함께 저장하는 것을 권장합니다.
