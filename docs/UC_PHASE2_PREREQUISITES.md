# Phase 2 전제조건 준비 가이드

> Phase 2(UC-09~12)는 주간 추천 기능을 검증합니다.  
> Celery Beat 스케줄러(매주 월요일 자동 실행)를 사용하지 않으므로,  
> 아래 안내에 따라 추천을 수동으로 생성한 뒤 테스트를 진행하세요.

---

## 1. 전제조건

Phase 2 테스트를 시작하기 전에 다음 두 가지 조건을 모두 충족해야 합니다.

| 조건 | 확인 방법 |
|------|---------|
| FastAPI 서버 실행 중 | `GET http://localhost:8000/health` → `{"status": "ok"}` |
| **active 버킷리스트 아이템 1개 이상 존재** | 버킷리스트 탭에서 아이템 목록 확인 (없으면 아래 '아이템 준비' 참고) |

### 아이템 준비 (아이템이 없는 경우)

Phase 1의 UC-03 절차를 따르거나, Supabase SQL Editor에서 직접 삽입하세요.

```sql
-- Supabase SQL Editor에서 실행 ({USER_ID}를 실제 UUID로 교체)
INSERT INTO bucket_items (user_id, title, category, priority, status)
VALUES
  ('{USER_ID}', '한라산 등반하기', 'travel', 'high', 'active'),
  ('{USER_ID}', '미슐랭 레스토랑 방문', 'food', 'medium', 'active');
```

> 현재 테스트 계정의 user_id 확인:
> ```sql
> SELECT id FROM auth.users WHERE email = 'your-test@email.com';
> ```

---

## 2. 추천 수동 생성 (generate-now)

Celery 없이 즉시 추천을 생성하려면 `POST /api/v1/recommendations/generate-now` 엔드포인트를 호출합니다.

### 방법 A: curl 명령어 (터미널)

로그인 후 Supabase 세션에서 JWT 토큰을 복사하여 `{JWT}` 자리에 붙여넣으세요.

```bash
curl -X POST http://192.168.x.x:8000/api/v1/recommendations/generate-now \
  -H "Authorization: Bearer {JWT}" \
  -H "Content-Type: application/json"
```

> `192.168.x.x`는 FastAPI 서버가 실행 중인 기기의 로컬 IP로 교체하세요.  
> 로컬에서 직접 실행하는 경우 `http://localhost:8000`을 사용하세요.

**성공 응답 예시 (200 OK):**
```json
{
  "id": "rec_01HX...",
  "week_start": "2026-05-04",
  "item": {
    "id": "item_01HX...",
    "title": "한라산 등반하기",
    "category": "travel",
    "priority": "high"
  },
  "reason": "이번 주 봄 계절과 높은 우선순위를 고려해 선정했어요.",
  "score_breakdown": {
    "priority_score": 40,
    "recency_bonus": 20,
    "season_score": 18,
    "weather_score": 10
  },
  "status": "pending",
  "created_at": "2026-05-09T09:00:00Z"
}
```

### 방법 B: Swagger UI (`/docs`)

개발 환경에서는 FastAPI 자동 문서를 활용할 수 있습니다.

1. 브라우저에서 `http://localhost:8000/docs` 접속
2. `POST /api/v1/recommendations/generate-now` 항목 펼치기
3. "Authorize" 버튼 → JWT 토큰 입력
4. "Try it out" → "Execute"

### 방법 C: 앱 내 개발자 버튼

홈 화면에 개발자용 "지금 추천 생성" 버튼이 구현된 경우 해당 버튼을 탭합니다.  
버튼은 `services/recommendations.ts`의 `generateRecommendationNow()` 함수를 호출하며,  
내부적으로 `POST /api/v1/recommendations/generate-now`를 실행합니다.

> 앱 내 버튼 구현 위치: 홈 화면 하단 또는 개발자 모드 섹션 (프로덕션 빌드에서는 제거 예정)

---

## 3. OpenWeatherMap API 키 미설정 시 동작

날씨 API 키(`OPENWEATHERMAP_API_KEY`)를 `server/.env`에 입력하지 않아도 테스트에 지장이 없습니다.

- API 키 미설정 또는 호출 실패 시 `weather_score = 10` (중립값) 자동 적용
- 추천 점수 계산은 `priority_score + recency_bonus + season_score + 10`으로 진행됨
- 날씨 조건에 따른 점수 차이를 검증하는 UC는 Phase 2에 포함되지 않으므로 테스트 결과에 영향 없음

---

## 4. 각 UC별 필요 데이터 요약

| UC | 필요 조건 | 비고 |
|----|---------|------|
| UC-09-1 | 이번 주 추천 레코드 없음 | `weekly_recommendations` 비어있는 초기 상태 |
| UC-09-2 | active 아이템 1개 이상 | generate-now 호출로 추천 생성 |
| UC-09-3 | UC-09-2 완료 후 | 추천 카드 노출 상태 |
| UC-09-4 | UC-09-2 완료 후 | 앱 재시작 후 확인 |
| UC-10-1 | `pending` 상태 추천 | UC-09-2로 생성된 추천 사용 |
| UC-10-2 | UC-10-1 완료 후 | — |
| UC-11-1 | `pending` 상태 추천 | UC-10-1 미수행이거나 새 추천 생성 후 |
| UC-11-2 | UC-11-1 완료 후 | — |
| UC-12-1 | 홈 화면 접근 가능 | — |
| UC-12-2 | 추천 레코드 1개 이상 | UC-09~11 수행 후 자동 충족 |
| UC-12-3 | 추천 레코드 없음 | 테스트 데이터 초기화 후 진행 |

---

## 5. 테스트 데이터 정리 (검증 완료 후)

모든 Phase 2 검증이 끝나면 아래 SQL로 추천 데이터를 초기화하세요.

```sql
-- weekly_recommendations 테이블 초기화 (본인 user_id 지정)
DELETE FROM weekly_recommendations
WHERE user_id = '{USER_ID}';
```

UC-12-3(히스토리 Empty State) 검증이 필요한 경우, 위 SQL 실행 후 히스토리 화면으로 진입하세요.

버킷리스트 아이템까지 정리하려면 Phase 1 가이드(`UC02_PREREQUISITES.md`)의 정리 SQL을 함께 실행하세요.

```sql
-- 참고: 버킷리스트 아이템 전체 삭제 (item_tags → bucket_items 순서)
DELETE FROM item_tags
WHERE item_id IN (
  SELECT id FROM bucket_items WHERE user_id = '{USER_ID}'
);

DELETE FROM bucket_items WHERE user_id = '{USER_ID}';
```
