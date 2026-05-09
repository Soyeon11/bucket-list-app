# 버킷리스트 쇼츠 앱 (bucket-list-app)

## 프로젝트 개요
매주 1개씩 스몰 버킷리스트 아이템을 제안하고, 실천 과정을 쇼츠/릴스 형식의 세로 영상으로 자동 제작·저장하는 앱.

## 핵심 기능
1. 버킷리스트 관리 (CRUD)
2. 매주 자동 아이템 추천 (우선순위, 계절, 날씨 고려)
3. 실천 기록 (사진/영상 업로드)
4. 쇼츠/릴스 형식 세로 영상 자동 생성 (템플릿 기반)
5. 갤러리 및 공유 기능

## 기술 스택

### Frontend
- **React Native + Expo** (SDK 51+)
- **TypeScript**
- **Expo Router** (파일 기반 네비게이션)
- **Zustand** (클라이언트 상태 관리)
- **TanStack Query** (서버 상태 / API 캐싱)
- **NativeWind** (Tailwind CSS for React Native)

### Backend
- **Python 3.11+**
- **FastAPI** (REST API)
- **SQLAlchemy** (ORM)
- **Celery + Redis** (영상 생성 비동기 처리)

### 영상 처리
- **FFmpeg** (핵심 영상 처리 엔진)
- **moviepy** (Python FFmpeg 래퍼, 템플릿 합성)

### Database & 인프라
- **Supabase** (PostgreSQL + Auth + Storage + Realtime)
  - DB: 버킷리스트, 기록, 영상 메타데이터
  - Storage: 업로드 사진/영상, 생성된 쇼츠 파일
  - Auth: 소셜 로그인 (Google, Apple)

### 개발 도구
- **Prettier + ESLint** (코드 스타일)
- **pytest** (백엔드 테스트)
- **Jest + Testing Library** (프론트엔드 테스트)

## 프로젝트 구조

```
bucket-list-app/
├── app/                          # Expo Router 페이지
│   ├── (tabs)/
│   │   ├── index.tsx             # 홈: 이번 주 추천 아이템
│   │   ├── bucketlist.tsx        # 버킷리스트 관리
│   │   ├── record.tsx            # 실천 기록 (사진/영상 업로드)
│   │   └── gallery.tsx           # 생성된 쇼츠 갤러리
│   ├── item/[id].tsx             # 아이템 상세
│   ├── _layout.tsx
│   └── +not-found.tsx
├── components/                   # 재사용 UI 컴포넌트
│   ├── BucketItem/
│   ├── VideoCard/
│   └── WeeklyCard/
├── hooks/                        # 커스텀 훅
├── store/                        # Zustand 스토어
│   ├── bucketlistStore.ts
│   └── userStore.ts
├── services/                     # API 호출 레이어
│   ├── api.ts
│   ├── bucketlist.ts
│   └── videos.ts
├── assets/
│   └── templates/                # 쇼츠 영상 템플릿 파일
├── server/                       # FastAPI 백엔드
│   ├── main.py
│   ├── routers/
│   │   ├── bucketlist.py
│   │   ├── recommendations.py
│   │   └── videos.py
│   ├── services/
│   │   ├── recommender.py        # 주간 추천 로직
│   │   └── video_processor.py   # FFmpeg 영상 생성
│   ├── models/                   # SQLAlchemy 모델
│   ├── schemas/                  # Pydantic 스키마
│   ├── requirements.txt
│   └── .env.example
├── package.json
├── tsconfig.json
├── .eslintrc.js
├── .prettierrc
└── CLAUDE.md
```

## 개발 로드맵

### Phase 1 — 기반 구축 (1~2주)
- [ ] Expo 프로젝트 초기화 (TypeScript + Expo Router)
- [ ] FastAPI 서버 초기화 + Supabase 연결
- [ ] 버킷리스트 CRUD API 구현
- [ ] 버킷리스트 목록/추가/수정/삭제 UI

### Phase 2 — 주간 추천 시스템 (1~2주)
- [ ] 추천 알고리즘 설계 (우선순위 점수 계산)
- [ ] 계절/날씨 API 연동 (OpenWeatherMap)
- [ ] 홈 화면: 이번 주 추천 아이템 카드 UI
- [ ] 추천 수락/거절/다음 주로 미루기 기능

### Phase 3 — 실천 기록 (1주)
- [ ] 사진/영상 업로드 (Expo ImagePicker)
- [ ] Supabase Storage 연동
- [ ] 기록 타임라인 UI

### Phase 4 — 쇼츠 영상 자동 생성 (2~3주)
- [ ] FFmpeg + moviepy 영상 템플릿 설계
- [ ] 세로(9:16) 영상 합성 파이프라인 구현
- [ ] Celery 비동기 영상 생성 큐
- [ ] 생성 완료 푸시 알림

### Phase 5 — 갤러리 & 공유 (1주)
- [ ] 쇼츠 갤러리 UI (무한 스크롤)
- [ ] 영상 다운로드 / 공유 기능
- [ ] 인스타그램 릴스 / 유튜브 쇼츠 공유 딥링크

## 환경 변수

```
# server/.env
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
OPENWEATHER_API_KEY=
REDIS_URL=

# app/.env
EXPO_PUBLIC_SUPABASE_URL=
EXPO_PUBLIC_SUPABASE_ANON_KEY=
EXPO_PUBLIC_API_URL=
```

## 개발 시작 명령어

```bash
# 프론트엔드
cd bucket-list-app
npm install
npx expo start

# 백엔드
cd bucket-list-app/server
pip install -r requirements.txt
uvicorn main:app --reload
```

## 코드 규칙
- 루트 CLAUDE.md의 공통 규칙 준수
- 컴포넌트: PascalCase, 훅: camelCase + `use` prefix
- API 응답 타입은 반드시 Pydantic(서버) / TypeScript interface(클라이언트)로 정의
- 영상 생성 작업은 반드시 Celery 큐를 통해 비동기 처리
