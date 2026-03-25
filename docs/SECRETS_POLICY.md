# CIRE Secrets Policy (No-Confusion / No-Plaintext)

## 목적
작업 혼선을 막고, 키 유출 리스크를 구조적으로 차단한다.

## 원칙
1. **평문 키를 문서(.md)에 저장하지 않는다.**
2. 실키는 **환경변수/시크릿 매니저**에서만 사용한다.
3. 문서에는 키를 `****` 형태로 마스킹해서 참조만 남긴다.
4. 키 노출 의심 시 즉시 rotate 후 구키 폐기한다.

## 허용 저장 위치
- Railway Variables
- Paddle Dashboard Secrets
- 로컬 임시 세션 환경변수 (필요 시)

## 금지 저장 위치
- Obsidian md 파일
- Git tracked 파일
- 채팅 로그에 원문 전체 붙여넣기

## 운영 규칙
- `CIRE-Keys.md`: 실키 금지, 상태/마스킹/조치 이력만 기록
- `LINK_REGISTRY.md`: 링크/파일 위치만 기록, 비밀값 금지
- 새 작업 시작 전: `echo ${#KEY}` 방식 길이 확인만 수행

## 사고 대응
1) 키 회전
2) 배포 재시작
3) 최소 smoke test
4) 사고 기록(시간/영향/복구)
