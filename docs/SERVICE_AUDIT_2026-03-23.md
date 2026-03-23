# CIRE 서비스 점검 보고서 (2026-03-23, 짧은판)

## 요약
- 현재 서비스는 **핵심 API 동작 정상**(analyze/batch/register/content/docs).
- 단, 고객 확보 관점에서 **결제/온보딩/보안**에 중요한 리스크가 존재.

## 점검 범위
- 랜딩: `https://cire-landing.vercel.app`
- API: `https://web-production-9cdb4.up.railway.app`
- 퍼널: 랜딩 -> register -> first call -> credits -> checkout

## 확인 결과
### 정상
1. `GET /`, `/docs`, `/openapi.json`, `/content` 정상(200)
2. `POST /v1/register` 정상 (free 100 credits)
3. `POST /v1/analyze` 정상
4. `POST /v1/batch` 정상 (`charged_count`, `error_count` 포함)
5. `GET /v1/credits` 정상 차감 반영

### 문제/리스크
#### [치명] 결제 진입 실패(일부 500)
- `POST /v1/checkout?package_id=starter|growth|scale` -> 500 발생
- 기대 동작: 설정 미완료면 503 + 명확한 안내
- 영향: 결제 전환 퍼널 단절

#### [중요] 랜딩에 API 키 하드코딩 노출
- 랜딩 스크립트에 공개 키 직접 포함
- 영향: 키 오남용/크레딧 소모/운영 데이터 오염

#### [중요] 랜딩 register 성공 후 후속 동선 부족
- 키 발급 후 "다음 액션(복붙 코드/첫 호출)" 유도 약함
- 영향: 등록 후 첫 호출 전환 저하

#### [개선] 지표 관측 분리 미흡
- 테스트 트래픽과 실제 유입 분리 지표 부족
- 영향: 마케팅 효율 판단 저하

## 즉시 조치 우선순위 (권장)
1. 결제 500 원인 수정 + 503/가이드로 fail-safe 처리
2. 랜딩 하드코딩 API 키 제거(서버 프록시 또는 사용자 입력형)
3. register 성공 패널에 1클릭 first-call 코드/버튼 추가
4. 이벤트 계측: register, first_call, checkout_started, checkout_success

## 고객 관점 판정
- 현재: "기능 데모 가능" 단계
- 목표: "유료 전환 가능한 MVP"로 가려면 결제 안정화가 최우선
