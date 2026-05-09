# 개발 현황 (Status)

> 마지막 업데이트: 2026-05-09 (Phase 1 E2E 검증 완료)

---

## 전체 진행률

| Phase | 이름 | 상태 | 진행률 |
|-------|------|------|--------|
| Phase 1 | 기반 구축 | ✅ Complete | 100% |
| Phase 2 | 주간 추천 시스템 | ⏳ Planned | 0% |
| Phase 3 | 실천 기록 | ⏳ Planned | 0% |
| Phase 4 | 쇼츠 영상 자동 생성 | ⏳ Planned | 0% |
| Phase 5 | 갤러리 & 공유 | ⏳ Planned | 0% |

---

## Phase 1 — 기반 구축 세부 현황

### 완료된 항목 ✅

#### 문서 (기획 에이전트)
- [x] `docs/PRD.md` — 38개 User Story, 13개 화면 명세, 추천 알고리즘 상세
- [x] `docs/API_SPEC.md` — 25개 엔드포인트, 15개 에러 코드, Rate Limiting 정책
- [x] `docs/DB_SCHEMA.md` — 8개 테이블, RLS 정책, 9개 인덱스, ERD
- [x] `docs/VIDEO_SPEC.md` — 영상 스펙 (1080x1920/30fps), 3종 템플릿, BGM 처리 방식

#### 백엔드 (백엔드 에이전트)
- [x] FastAPI 프로젝트 구조 (`server/`)
- [x] 환경 변수 관리 (`config.py`, pydantic-settings)
- [x] Supabase 클라이언트 + JWT 인증 미들웨어 (`database.py`)
- [x] 버킷리스트 CRUD API 6개 엔드포인트 (`routers/bucketlist.py`)
  - GET /api/v1/items (필터, 페이지네이션)
  - POST /api/v1/items
  - GET /api/v1/items/{id}
  - PUT/PATCH /api/v1/items/{id}
  - DELETE /api/v1/items/{id}
  - PATCH /api/v1/items/{id}/complete
- [x] Pydantic v2 스키마 + 통일 에러 응답 형식 (`schemas/`)
- [x] SQLAlchemy 2.0 모델 (`models/`)
- [x] DB 초기화 SQL (`migrations/001_initial_schema.sql`)
- [x] `outdoor` 카테고리 추가 마이그레이션 (`migrations/003_add_outdoor_category.sql`)
- [x] ES256 JWT 검증 (Supabase JWKS 엔드포인트 연동)
- [x] Phase 2, 4용 라우터 플레이스홀더

#### 프론트엔드 (프론트엔드 에이전트)
- [x] Expo SDK 54 + TypeScript 프로젝트 설정
- [x] NativeWind v4.2.3 + TanStack Query v5 + Zustand 설정
- [x] Expo Router 네비게이션 구조 (탭 4개, 인증 플로우)
- [x] 버킷리스트 목록 화면 (카테고리 필터, FlatList, 당겨서 새로고침, FAB)
- [x] 아이템 추가/수정 화면 (BucketItemForm)
- [x] 아이템 상세 화면 (완료 처리, 삭제 포함)
- [x] API 서비스 레이어 (Axios + JWT 인터셉터, 낙관적 업데이트)
- [x] 로그아웃 버튼 (홈 화면 우상단, 확인 알림 포함)
- [x] Stack 네비게이터 설정 (`_layout.tsx` — 뒤로가기 버튼 활성화)
- [x] KeyboardAvoidingView (아이템 폼 태그 입력란 키보드 대응)
- [x] 홈/기록/갤러리 화면 플레이스홀더

#### 미디어 (미디어 에이전트)
- [x] `server/services/video_processor.py` — FFmpeg 영상 파이프라인 전체 구현
  - 3종 템플릿 (minimal / vibrant / film) 지원
  - BGM 정규화 (-16 LUFS), 트랜지션 (fade/slide/zoom)
  - Celery 진행률 콜백, 임시파일 자동 정리
- [x] `assets/templates/` — 3종 템플릿 JSON 설정 파일

---

### 미완료 항목 (Phase 1 나머지) ⏳

- [x] ~~**Supabase 프로젝트 생성**~~ — 완료
- [x] ~~**DB 마이그레이션 실행**~~ — 8개 테이블 + RLS + 인덱스 생성 완료
- [x] ~~**환경 변수 입력**~~ — `server/.env`, `.env` Supabase 키 입력 완료
- [x] ~~**패키지 설치**~~ — `npm install` (1375개), `pip install` (전체 패키지) 완료
- [x] ~~**FastAPI 백엔드 실행**~~ — `http://localhost:8000/health` 응답 확인 완료
- [x] ~~**Expo 프론트엔드 실행**~~ — Metro Bundler `http://localhost:8081` 응답 확인 완료
- [x] ~~**실제 기기 화면 확인**~~ — iOS Expo Go에서 로그인 화면 정상 출력 확인

---

## Phase 1 검증 결과 (2026-05-09)

### 정적 검증

| 검증 항목 | 결과 |
|-----------|------|
| TypeScript (`npx tsc --noEmit`) | ✅ 0 errors |
| FastAPI 백엔드 `/health` | ✅ 200 OK |
| FastAPI CRUD 엔드포인트 (미인증) | ✅ 401 Unauthorized 정상 반환 |
| Expo Metro 번들러 | ✅ :8081 응답 확인 |
| iOS Expo Go 로그인 화면 | ✅ 정상 출력 |

### E2E 유저케이스 검증

> 상세 체크리스트: [`docs/E2E_VALIDATION_PHASE1.md`](./E2E_VALIDATION_PHASE1.md)

| 유저케이스 | 총 항목 | 통과 | 상태 |
|------------|--------|------|------|
| UC-01. 인증 | 3 | 3 | ✅ PASS |
| UC-02. 목록 조회 | 6 | 6 | ✅ PASS |
| UC-03. 아이템 생성 | 7 | 7 | ✅ PASS |
| UC-04. 상세 조회 | 3 | 3 | ✅ PASS |
| UC-05. 아이템 수정 | 4 | 4 | ✅ PASS |
| UC-06. 완료 처리 | 3 | 3 | ✅ PASS |
| UC-07. 아이템 삭제 | 3 | 3 | ✅ PASS |
| UC-08. 에러 처리 | 3 | 3 | ✅ PASS |
| **합계** | **32항목** | **32** | ✅ **전체 통과** |

**Phase 2 진입 조건: E2E 32개 항목 중 critical 실패 0건 → ✅ 충족**

---

## 알려진 이슈 / 기술 부채

| 항목 | 내용 | 우선순위 |
|------|------|--------|
| reanimated 버전 경고 | 3.16.7 사용 중 (SDK 54 권장: ~4.1.1). 기능 동작엔 문제 없음 | 추후 해결 |
| FastAPI 서버 수동 실행 | 현재 로컬 수동 기동 필요 (포트 8002). CI/CD 미구성 | Phase 2 전 해결 |

## 개발 환경

| 도구 | 버전 | 상태 |
|------|------|------|
| Node.js | v24.15.0 | ✅ 설치됨 |
| npm | v11.12.1 | ✅ 설치됨 |
| Python | 3.12.10 | ✅ 설치됨 |
| FFmpeg | 8.1.1 | ✅ 설치됨 |
| Git | - | ✅ 설치됨 |
| Supabase 프로젝트 | fbmgwadhlrcoduwuojvd | ✅ 생성 및 연결됨 |

---

## 주요 기술 결정 사항

| 항목 | 결정 | 이유 |
|------|------|------|
| 모바일 프레임워크 | React Native + Expo SDK 51 | TypeScript 일관성, 빌드 복잡도 최소화 |
| 백엔드 | FastAPI (Python 3.12) | 영상처리·AI 추천에 Python 생태계 유리 |
| 영상 처리 | FFmpeg + moviepy | 세로 영상 템플릿 합성에 검증된 조합 |
| DB/인프라 | Supabase | DB + Auth + Storage 통합, 멀티 디바이스 동기화 |
| 비동기 처리 | Celery + Redis | 영상 생성은 큐 처리 필수 |
| 상태 관리 | Zustand (클라이언트) + TanStack Query (서버) | 역할 명확히 분리 |
