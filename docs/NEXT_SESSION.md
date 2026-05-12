# 다음 세션 인수인계 문서

> 작성일: 2026-05-10  
> 현재 브랜치: `phase3`  
> 현재 상태: Phase 3 구현 완료, E2E 검증 대기 중

---

## 현재 진행 상황

| Phase | 상태 | 비고 |
|-------|------|------|
| Phase 1 — 기반 구축 | ✅ 완료 | 32/32 UC 통과, `phase1-complete` 태그 |
| Phase 2 — 주간 추천 | ✅ 완료 | 11/11 UC 통과, `phase2-complete` 태그 |
| Phase 3 — 실천 기록 | 🔨 구현 완료, E2E 검증 대기 | `phase3` 브랜치, 커밋 `086f53f` |
| Phase 4 — 쇼츠 영상 자동 생성 | ⏳ 미시작 | |
| Phase 5 — 갤러리 & 공유 | ⏳ 미시작 | |

---

## Phase 3에서 구현한 내용

### 백엔드 (신규 파일)
| 파일 | 내용 |
|------|------|
| `server/schemas/log.py` | Pydantic v2 스키마 (ActivityLogCreate, ActivityLogResponse, MediaItem 등) |
| `server/services/storage.py` | Supabase Storage 서비스 (signed URL 생성/조회, 파일 삭제) |
| `server/routers/logs.py` | Activity Log API 5개 엔드포인트 |

### 백엔드 (수정 파일)
| 파일 | 변경 내용 |
|------|-----------|
| `server/main.py` | `logs` 라우터 등록 추가 |

### 프론트엔드 (신규 파일)
| 파일 | 내용 |
|------|------|
| `services/logs.ts` | API 서비스 레이어 (6개 함수) |
| `hooks/useActivityLog.ts` | TanStack Query 훅 (useActivityLogs, useCreateLog, useDeleteLog 등) |
| `components/ActivityLog/LogCard.tsx` | 단일 기록 카드 (노트 + 미디어 토글) |
| `components/ActivityLog/MediaGrid.tsx` | 3열 미디어 그리드 |
| `components/ActivityLog/MediaPreviewItem.tsx` | 단일 미디어 썸네일 |

### 프론트엔드 (수정 파일)
| 파일 | 변경 내용 |
|------|-----------|
| `app/(tabs)/record.tsx` | 플레이스홀더 → active 아이템 목록으로 교체 |
| `app/item/[id].tsx` | 실천 기록 섹션 + 기록 추가 모달 추가 |

### API 엔드포인트 (5개)
```
POST   /api/v1/items/{item_id}/logs                      기록 생성 (201)
GET    /api/v1/items/{item_id}/logs                      기록 목록 조회 (페이지네이션)
GET    /api/v1/items/{item_id}/logs/{log_id}             기록 단건 조회
DELETE /api/v1/items/{item_id}/logs/{log_id}             기록 삭제 (204)
POST   /api/v1/items/{item_id}/logs/{log_id}/upload-urls 미디어 서명 업로드 URL 발급
```

### 미디어 업로드 플로우
```
앱 → POST /logs (기록 생성)
앱 → POST /logs/{id}/upload-urls (서명 URL 발급)
앱 → PUT {signed_url} (Supabase Storage 직접 업로드)
```

---

## 다음 세션에서 할 일

### 즉시 — Phase 3 E2E 검증 (우선순위 높음)

1. **Supabase Storage `logs` 버킷 생성** (대시보드에서 확인 필요)
   - 버킷명: `logs`, 비공개, 200MB 제한
   - 준비 가이드: [`docs/PHASE3_E2E_PREP.md`](./PHASE3_E2E_PREP.md)

2. **E2E 검증 진행** — [`docs/E2E_VALIDATION_PHASE3.md`](./E2E_VALIDATION_PHASE3.md)
   - UC-13~17, 총 15개 항목
   - 실패 발생 시 fix 커밋: `fix(e2e/uc-NN-M): 수정 내용`

3. **알려진 미구현 항목 (E2E 전 수정 필요)**

   | 항목 | 위치 | 내용 |
   |------|------|------|
   | 기록 삭제 UI | `app/item/[id].tsx` | LogCard에 삭제 버튼 없음. `useDeleteLog` 훅은 준비되어 있으나 UI 연결 미완 |
   | `logs_count` 트리거 | Supabase DB | `activity_logs` INSERT/DELETE 시 `bucket_items.logs_count` 자동 업데이트 트리거 미확인 |
   | 파일 크기 클라이언트 검증 | `app/item/[id].tsx` | UC-17-3용 클라이언트 사이드 파일 크기 체크 미구현 |

4. **Phase 3 완료 처리** (E2E 전체 통과 후)
   ```
   phase3 → dev → main 머지
   git tag phase3-complete
   git push origin main dev --tags
   docs/STATUS.md Phase 3 완료로 업데이트
   ```

### 이후 — Phase 4 (쇼츠 영상 자동 생성)
- PRD 참고: [`docs/PRD.md`](./PRD.md)
- 주요 작업: FFmpeg 영상 파이프라인 (`server/services/video_processor.py` 이미 구현됨), Celery 큐, 영상 생성 API
- `server/services/video_processor.py`는 Phase 1에서 이미 구현되어 있음 (재사용 가능)

---

## 개발 환경 빠른 시작

```powershell
# 백엔드 (터미널 1)
cd C:\Projects\claude-workspace\bucket-list-app\server
python -m uvicorn main:app --reload --port 8000

# 프론트엔드 (터미널 2)
cd C:\Projects\claude-workspace\bucket-list-app
npx expo start
```

- 서버 헬스체크: `http://localhost:8000/health`
- API 문서(Swagger): `http://localhost:8000/docs`
- `.env`의 `EXPO_PUBLIC_API_BASE_URL`이 PC 로컬 IP로 설정되어 있는지 확인 (IP 변경 시 수정 필요)

---

## 기술 부채 / 알려진 이슈

| 항목 | 내용 | 우선순위 |
|------|------|--------|
| reanimated 버전 경고 | 3.16.7 사용 중 (SDK 54 권장: ~4.1.1). 기능 동작엔 문제 없음 | 추후 |
| FastAPI 서버 수동 실행 | 로컬 수동 기동 필요. CI/CD 미구성 | Phase 3 이후 |
| [DEV] 추천 생성 버튼 | 홈 화면 하단 개발용 버튼 — 배포 전 제거 필요 | 배포 전 |
| 기록 삭제 UI | `LogCard`에 삭제 버튼 UI 미구현 | Phase 3 E2E 전 |
| 파일 크기 클라이언트 검증 | UC-17-3 통과를 위해 추가 필요 | Phase 3 E2E 전 |

---

## 주요 파일 경로

```
bucket-list-app/
├── docs/
│   ├── PRD.md                        전체 기획서
│   ├── API_SPEC.md                   API 명세
│   ├── DB_SCHEMA.md                  DB 스키마
│   ├── STATUS.md                     개발 현황
│   ├── E2E_VALIDATION_PHASE1.md      Phase 1 E2E (✅ 완료)
│   ├── E2E_VALIDATION_PHASE2.md      Phase 2 E2E (✅ 완료)
│   ├── E2E_VALIDATION_PHASE3.md      Phase 3 E2E (⬜ 대기)
│   ├── PHASE3_E2E_PREP.md            Phase 3 E2E 준비 가이드 ← 이번 세션 작성
│   └── daily-log/                    일일 작업 로그
│       └── 2026-05-09.md
├── server/
│   ├── routers/logs.py               Phase 3 신규
│   ├── schemas/log.py                Phase 3 신규
│   └── services/storage.py          Phase 3 신규
├── services/logs.ts                  Phase 3 신규
├── hooks/useActivityLog.ts           Phase 3 신규
└── components/ActivityLog/           Phase 3 신규 (3개 컴포넌트)
```
