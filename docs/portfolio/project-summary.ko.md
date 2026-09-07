# 포트폴리오 프로젝트 요약

## Local Context-Aware Smart Home Controller

### 한 줄 소개

MacBook에서 STT와 경량 LLM을 로컬 실행하고, 실내 센서·날씨·태양 정보를 함께 판단해 Home Assistant의 실제 커튼과 IR 에어컨을 제어한 스마트홈 시스템이다.

### 문제

단순 음성 리모컨은 사용자가 장치와 동작을 정확히 말해야 한다. 또한 LLM 출력을 그대로 실제 장치에 전달하면 잘못된 엔티티나 불필요한 반복 명령이 실행될 수 있다.

### 해결

- 음성과 텍스트를 하나의 명령 처리 경로로 통합했다.
- Home Assistant에서 현재 온도, 습도, 조도, 커튼 상태를 요청 시점에 읽었다.
- 일출·일몰, 태양 위치, 외부 날씨와 일사량을 Context에 추가했다.
- 로컬 LLM의 JSON 계획을 스키마, 정규화 규칙, 상태 정책, 장치 allow-list로 검증했다.
- 제조사 엔티티 ID를 논리 장치 ID 뒤에 숨겨 LLM과 하드웨어를 분리했다.
- Matter에 직접 노출되지 않는 IR 에어컨은 Aqara Scene Sync를 제한된 명령형 actuator로 연결했다.

### 대표 시나리오

```text
User: "It's too hot in the living room. Make it comfortable."

Context:
- Indoor temperature: 29.3 C
- Curtain: open
- Illuminance and solar context available

Decision:
- Close the curtain
- Send the AC Cool 24 IR preset
```

브라우저 마이크 입력부터 실제 커튼과 에어컨 동작까지 현장에서 촬영하고 육안 검증했다.

### 기술 스택

Python, FastAPI, faster-whisper, Ollama, llama3.2:3b, Home Assistant OS, Matter, Aqara Hub M3, Astral, Open-Meteo, HTML, CSS, JavaScript

### 담당 및 기여

- 로컬 STT·LLM 실행 환경 구성
- 자연어 명령 JSON 스키마와 fallback parser 구현
- Home Assistant adapter와 논리 엔티티 매핑 구현
- 센서 Context 정규화 및 상황 기반 정책 구현
- Matter Bridge 네트워크 문제 진단과 실제 장치 연동
- Aqara IR Scene Sync 재트리거 방식 구현
- 시뮬레이션 및 물리 경로 테스트와 개발 기록 관리

### 검증

- 자동화 테스트로 parser, policy, simulation API, HA REST 매핑, IR scene 순서, 태양 계산, 날씨 캐시 검증
- 사용자 육안으로 마이크 기반 커튼 제어, AC ON, AC OFF 및 반복 동작 확인

### 한계와 다음 단계

IR 에어컨 상태는 양방향 피드백이 없어 실제 상태가 아니라 마지막 명령만 표현한다. 다음 단계는 VPN 기반 원격 개발 환경, 이벤트 기반 자동 제어, 상시 실행 가능한 edge device 이전이다.
