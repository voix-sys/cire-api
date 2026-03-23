# CIRE Visual Roadmap (Whimsical/Mermaid용)

아래 Mermaid를 GitHub/Notion/Obsidian에 붙이면 시각 로드맵으로 바로 확인 가능.
Whimsical로 옮길 때는 섹션별 박스 그대로 노드로 복사.

```mermaid
flowchart TD
  A[Now: Core API Live\n/analyze /batch /content] --> B[Sprint 1\n전환/안정화 2주]
  B --> C[Sprint 2\nPro 고도화 2주]
  C --> D[Sprint 3\n유입 자동화/확장 2주]

  subgraph S1[SPRINT 1 (주요 KPI: register -> first call)]
    B1[Fix checkout 500\nFail-safe 503]
    B2[랜딩 키 하드코딩 제거]
    B3[Register 후 1-click first call]
    B4[이벤트 계측\nregister/first_call/checkout]
  end

  subgraph S2[SPRINT 2 (주요 KPI: Pro 전환)]
    C1[synergy/optimal 데이터 확장]
    C2[근거(evidence) 응답 표준화]
    C3[rate limit + retry 정책 문서화]
    C4[배치/크레딧 회귀테스트]
  end

  subgraph S3[SPRINT 3 (주요 KPI: 유입 성장)]
    D1[X 콘텐츠 루틴 고정\n60/30/10]
    D2[개발자 블로그 10개 누적]
    D3[퍼널 A/B 테스트\nCTA/랜딩 카피]
    D4[주간 리포트 자동화]
  end

  B --> B1 --> B2 --> B3 --> B4
  C --> C1 --> C2 --> C3 --> C4
  D --> D1 --> D2 --> D3 --> D4
```

## Whimsical 보드 구조(복붙용)
- Column 1: NOW
  - Core API live
  - Landing fixed(register flow)
- Column 2: Sprint 1 (2주)
  - checkout 안정화
  - onboarding friction 제거
  - tracking baseline
- Column 3: Sprint 2 (2주)
  - Pro value 강화
  - reliability hardening
- Column 4: Sprint 3 (2주)
  - growth engine 가동
  - weekly KPI loop

## 주간 리듬
- 월: 개발 우선순위 확정
- 화~목: 구현/검증
- 금: 배포 + KPI 리뷰
- 일: 다음 주 실험 설계
