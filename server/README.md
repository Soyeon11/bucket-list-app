# Bucket List App — Backend Server

FastAPI 백엔드 서버입니다.

## 기술 스택

- Python 3.12
- FastAPI 0.115 + Uvicorn
- Supabase (PostgreSQL 15, Auth, Storage)
- Pydantic v2 + pydantic-settings
- Celery + Redis (Phase 4 — 영상 생성용, 현재 구조만 준비)

## 빠른 시작

```bash
# 1. 가상환경 생성 및 패키지 설치
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 Supabase 프로젝트 정보 입력

# 3. DB 마이그레이션 실행
# Supabase SQL Editor에 migrations/001_initial_schema.sql 붙여넣기 후 실행

# 4. 서버 실행
uvicorn main:app --reload --port 8000
```

## API 문서

서버 실행 후 아래 URL에서 Swagger UI 확인 가능 (개발 환경만):

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조

```
server/
├── main.py                     # FastAPI 앱, CORS, 라우터 등록
├── config.py                   # 환경 변수 (pydantic-settings)
├── database.py                 # Supabase 클라이언트, JWT 미들웨어
├── routers/
│   ├── bucketlist.py           # Phase 1: 버킷리스트 CRUD (6개 엔드포인트)
│   ├── recommendations.py      # Phase 2: 주간 추천 (placeholder)
│   └── videos.py               # Phase 4: 영상 생성 (placeholder)
├── services/
│   ├── recommender.py          # Phase 2 (placeholder)
│   └── video_processor.py      # Phase 4 (placeholder)
├── models/
│   └── bucket_item.py          # SQLAlchemy 2.0 ORM 모델
├── schemas/
│   ├── bucket_item.py          # Pydantic 요청/응답 스키마
│   └── common.py               # 통일 에러 응답, 페이지네이션
├── migrations/
│   └── 001_initial_schema.sql  # 전체 DB 스키마 + RLS 정책
├── requirements.txt
└── .env.example
```

## 환경 변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `SUPABASE_URL` | Yes | Supabase 프로젝트 URL |
| `SUPABASE_SERVICE_KEY` | Yes | 서비스 롤 키 (비밀 유지) |
| `SUPABASE_ANON_KEY` | Yes | 익명/공개 키 |
| `SUPABASE_JWT_SECRET` | Yes | JWT 서명 시크릿 |
| `REDIS_URL` | No | Redis URL (Phase 4) |
| `APP_ENV` | No | `development` \| `staging` \| `production` |
| `CORS_ORIGINS` | No | 허용할 CORS 출처 (콤마 구분) |
