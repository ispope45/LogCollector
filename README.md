# LogCollector
- netmiko base

## 2025028 Collector V1.0
- 쿠팡 정기점검 Command 자동화
- CISCO_IOS, CISCO_NXOS, CISCO_XE, CISCO_WLC 지원
- Thread Count 8개(CPU에 따름)

## 2025028 Collector V1.1
- MaxThread 5개 고정
- Thread 간 0.1 gap 적용
- Conn timeout, Read timeout 20초 변경
- Disconnect Logic 추가

## 20250320 Collector V1.2
- MaxThread 8개 고정
- send_command -> execute_command 로 변경
  - send_command read_timeout 60초 적용 
  - retry, delay 적용

## 20250320 Collector V1.3
- Login prompt 처리
- USER/PASS 물어볼 경우 직접 입력

## 20250323 Collector V1.4
- Parse form에 Hostname 추가

## 20250416 Collector V1.5
- Timeout 3번씩 로그 찍히는거 1번으로 변경
- 성공한 세션 Logging

## 20250514 Collector V1.5
- Command timeout 발생시 read_timeout 2배로 설정하여 재시도 최대 3회

## 20250515 Collector V1.5
- Connection timeout 발생시 conn_timeout 2배로 설정하여 재시도 최대 3회
- logging_text에서 raw log file 생성하도록 변경

## 20250611 Collector V1.7
- ??

## 20250714 Collector V1.8
- 응답시간이 긴 Command 는 예외처리

## 20250828 Collector V2.0(ing)
- Module 분리
- Parsing tool과 기능 통합
- Collector로 수집된 정보만 출력
- Collector
  - Hostname/SN 수집되지 않은 Device 수집하지 않음.
