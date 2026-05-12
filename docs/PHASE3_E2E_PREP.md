# Phase 3 E2E 검증 사전 준비 가이드

> 대상: UC-13 ~ UC-17 (실천 기록 / Activity Logging) 검증 전 준비 사항

---

## 1. Supabase Storage 버킷 생성 (최초 1회)

Phase 3의 미디어 업로드는 Supabase Storage `logs` 버킷을 사용합니다.
마이그레이션 SQL에 버킷 생성 구문이 포함되어 있으나, **Supabase 대시보드에서 직접 확인**이 필요합니다.

### 확인 절차
1. [Supabase 대시보드](https://supabase.com/dashboard) → 프로젝트 선택 (`fbmgwadhlrcoduwuojvd`)
2. 좌측 메뉴 **Storage** 진입
3. `logs` 버킷 존재 여부 확인

### 버킷이 없으면 직접 생성
| 설정 항목 | 값 |
|-----------|-----|
| 버킷 이름 | `logs` |
| Public | ❌ (비공개) |
| 파일 크기 제한 | `200MB` |
| 허용 MIME 타입 | `image/jpeg, image/png, image/webp, image/heic, video/mp4, video/quicktime` |

### RLS 정책 확인
Storage `logs` 버킷에 아래 RLS 정책이 적용되어 있어야 합니다.
Supabase 대시보드 → Storage → Policies에서 확인:

```sql
-- SELECT: 본인 파일만 조회
CREATE POLICY "Users can view own logs media"
ON storage.objects FOR SELECT
USING (bucket_id = 'logs' AND auth.uid()::text = (storage.foldername(name))[1]);

-- INSERT: 본인 경로에만 업로드
CREATE POLICY "Users can upload own logs media"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'logs' AND auth.uid()::text = (storage.foldername(name))[1]);

-- DELETE: 본인 파일만 삭제
CREATE POLICY "Users can delete own logs media"
ON storage.objects FOR DELETE
USING (bucket_id = 'logs' AND auth.uid()::text = (storage.foldername(name))[1]);
```

> 정책이 없으면 Supabase Dashboard → Storage → Policies → **New policy** 로 추가.

---

## 2. FastAPI 서버 실행

### 터미널 1 — 백엔드 서버

```powershell
# 프로젝트 루트에서 실행
cd C:\Projects\claude-workspace\bucket-list-app\server

# 가상환경 활성화 (있는 경우)
# .\.venv\Scripts\Activate.ps1

python -m uvicorn main:app --reload --port 8000
```

### 서버 기동 확인

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
# 기대 응답: {"status":"ok", "timestamp":"...", ...}
```

### Phase 3 신규 엔드포인트 확인

```powershell
$r = Invoke-RestMethod -Uri "http://localhost:8000/openapi.json"
$r.paths.PSObject.Properties.Name | Where-Object { $_ -like "*logs*" }
# 기대 출력:
# /api/v1/items/{item_id}/logs
# /api/v1/items/{item_id}/logs/{log_id}
# /api/v1/items/{item_id}/logs/{log_id}/upload-urls
```

---

## 3. Expo Metro 번들러 실행

### 터미널 2 — 프론트엔드

```powershell
# 프로젝트 루트에서 실행
cd C:\Projects\claude-workspace\bucket-list-app

npx expo start
```

### iOS Expo Go 연결

1. iPhone에서 **Expo Go** 앱 실행
2. Metro 터미널에 표시된 **QR 코드** 스캔
3. 앱 로드 완료 후 로그인 화면 확인

### 네트워크 주의사항

- PC와 iPhone이 **동일한 Wi-Fi** 에 연결되어 있어야 합니다
- `server/.env`의 `EXPO_PUBLIC_API_BASE_URL`이 PC의 **로컬 IP** 로 설정되어 있는지 확인

```powershell
# PC의 로컬 IP 확인
ipconfig | Select-String "IPv4"
```

- 현재 설정값 확인: `bucket-list-app/.env` → `EXPO_PUBLIC_API_BASE_URL`
- 예시: `EXPO_PUBLIC_API_BASE_URL=http://192.168.x.x:8000/api/v1`
- IP가 변경된 경우 `.env` 수정 후 Metro 재시작 (`r` 키 입력 또는 Metro 재실행)

---

## 4. 테스트 데이터 사전 준비

E2E 검증 전 아래 상태를 확인하세요.

| 항목 | 확인 방법 | 필요 상태 |
|------|-----------|-----------|
| 로그인 | 앱 실행 후 확인 | 로그인 완료 |
| active 아이템 | 버킷리스트 탭 | 1개 이상 존재 |
| 기록 없는 아이템 | UC-15-3 용도 | 1개 이상 존재 (신규 생성) |
| 갤러리 사진 | 기기 사진 앱 | 10장 이상 존재 |

### 테스트용 초기화 (필요시)

Supabase 대시보드 → **Table Editor** → `activity_logs` 테이블에서 테스트 데이터 삭제:

```sql
-- 본인 계정 기록 전체 삭제 (테스트 초기화용)
DELETE FROM activity_logs WHERE user_id = auth.uid();
```

---

## 5. 검증 순서 권장

```
UC-15-3 (빈 상태)  →  UC-13-1, 13-2 (기록 생성)
 → UC-13-3, 13-4 (기록 확인)
 → UC-14-1 (사진 1장 업로드)
 → UC-15-1, 15-2 (기록/미디어 조회)
 → UC-14-2 (사진 10장)
 → UC-16-1 (기록 삭제)
 → UC-16-2 (미디어 Storage 삭제 확인)
 → UC-17 (에러 처리)
```

---

## 6. 알려진 주의사항

| 항목 | 내용 |
|------|------|
| `logs` 버킷 미생성 | 미디어 업로드 시 500 에러 — Supabase Storage에서 버킷 먼저 생성 필요 |
| 기록 삭제 UI 미구현 | UC-16은 현재 API 레벨에서만 동작. 삭제 버튼 UI가 없으므로 Supabase 대시보드에서 직접 삭제 또는 Phase 3 후속 작업으로 UI 추가 필요 |
| 미디어 썸네일 표시 | LogCard에서 썸네일 확인을 위해 "사진 N장 ▼" 버튼 탭 필요 (기본 접힘 상태) |
| `logs_count` 업데이트 | `activity_logs` INSERT/DELETE 시 `bucket_items.logs_count`는 DB 트리거로 자동 업데이트되어야 함. 트리거 미설정 시 수동 카운트 확인 필요 |
