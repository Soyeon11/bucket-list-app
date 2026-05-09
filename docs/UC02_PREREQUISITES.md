# UC-02 전제조건 준비 가이드

> UC-02-2 이후 테스트케이스는 "아이템이 1개 이상 존재"하는 상태가 필요합니다.  
> 아래 두 가지 방법 중 하나를 선택하세요.

---

## 방법 A: 앱에서 직접 아이템 생성 (권장)

UC-03(아이템 생성)을 먼저 수행하면 UC-02의 전제조건이 자동으로 충족됩니다.

**순서 변경**: UC-02-1 → UC-03 일부 → UC-02-2~6 → UC-03 나머지

1. UC-02-1(빈 목록) 검증 완료
2. FAB(+) 버튼으로 아이템 생성:
   - **아이템 1** (카테고리 A): 제목 + 카테고리만 입력
   - **아이템 2** (카테고리 B): 제목 + 카테고리 다르게 입력 (필터 테스트용)
   - **아이템 3**: 설명/태그 포함 (상세 조회 테스트용)
3. 생성 후 UC-02-2~6 검증 진행

---

## 방법 B: Supabase Dashboard에서 직접 삽입

서버가 실행 중이고 테스트 계정의 user_id를 알아야 합니다.

### Step 1. 테스트 계정 user_id 확인

Supabase Dashboard → Authentication → Users → 테스트 계정 행의 UUID 복사

또는 앱 로그인 후 Supabase SQL Editor에서:
```sql
SELECT id FROM auth.users WHERE email = 'your-test@email.com';
```

### Step 2. Supabase SQL Editor에서 아이템 삽입

[Supabase Dashboard](https://supabase.com/dashboard) → 프로젝트 → SQL Editor

아래 SQL에서 `{USER_ID}`를 실제 UUID로 교체 후 실행:

```sql
-- ⚠️ 먼저 이 마이그레이션을 실행해야 합니다 (outdoor 카테고리 추가):
ALTER TYPE category_enum ADD VALUE IF NOT EXISTS 'outdoor';

-- 필수 항목만 있는 아이템 (카테고리: travel)
INSERT INTO bucket_items (user_id, title, category, priority, status)
VALUES
  ('{USER_ID}', '제주도 한 달 살기', 'travel', 'high', 'active'),
  ('{USER_ID}', '후지산 등반하기', 'travel', 'medium', 'active');

-- 다른 카테고리 아이템 (카테고리: food) — 필터 테스트용
INSERT INTO bucket_items (user_id, title, category, priority, status)
VALUES
  ('{USER_ID}', '미슐랭 3스타 레스토랑 방문', 'food', 'low', 'active');

-- 설명과 태그가 있는 아이템 (상세조회 UC-04-2 테스트용)
INSERT INTO bucket_items (user_id, title, category, priority, description, status)
VALUES
  ('{USER_ID}', '스카이다이빙 체험', 'outdoor', 'high',
   '인생에서 한 번은 해봐야 할 도전. 제주도나 가평에서 진행하는 프로그램 알아보기.',
   'active')
RETURNING id;
```

태그가 있는 아이템의 경우, 위 INSERT의 RETURNING id 결과를 {ITEM_ID}로 사용:
```sql
INSERT INTO item_tags (item_id, tag)
VALUES
  ('{ITEM_ID}', '도전'),
  ('{ITEM_ID}', '익스트림'),
  ('{ITEM_ID}', '버킷리스트');
```

---

## 각 UC별 필요 데이터 요약

| UC | 필요 조건 | 최소 데이터 |
|----|---------|------------|
| UC-02-2 | 아이템 1개 이상 | 아이템 1개 (아무 카테고리) |
| UC-02-3 | 다른 카테고리 2개 이상 | 카테고리 A 아이템 1개 + 카테고리 B 아이템 1개 |
| UC-02-4 | UC-02-3 이후 | — |
| UC-02-5 | 아이템 1개 이상 | — |
| UC-02-6 | 아이템 1개 이상 | — |
| UC-04-2 | 설명/태그 있는 아이템 | description + tags 있는 아이템 1개 |
| UC-04-3 | 설명/태그 없는 아이템 | 제목+카테고리만 있는 아이템 1개 |

---

## 테스트 데이터 정리 (UC 완료 후)

모든 검증이 끝나면 아래로 정리:

```sql
-- 테스트 아이템 전체 삭제 (본인 user_id 지정)
DELETE FROM item_tags
WHERE item_id IN (
  SELECT id FROM bucket_items WHERE user_id = '{USER_ID}'
);

DELETE FROM bucket_items WHERE user_id = '{USER_ID}';
```
