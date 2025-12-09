# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChatGPT 클론 프로젝트로, OpenAI Agents SDK (`openai-agents`)를 활용하여 멀티 에이전트 대화 시스템과 영구 메모리 저장 기능을 갖춘 챗봇 애플리케이션입니다.

## Architecture

### Core Components
- **Streamlit UI** (`main.py`): Streamlit 기반 웹 인터페이스로 실시간 스트리밍 채팅 구현
- **Agent System**: `openai-agents` 라이브러리를 사용한 대화형 에이전트
  - Multi-agent handoff 아키텍처 지원
  - SQLite 기반 대화 메모리 (`SQLiteSession`)
  - Function tools를 통한 에이전트 기능 확장
  - 에이전트 상호작용 그래프 시각화

### Agent Architecture Patterns
- **Agent 정의**: `Agent(name, instructions, handoffs?, tools?, output_type?)`
  - `handoffs`: 특수 에이전트로 라우팅 (멀티 에이전트 시스템)
  - `tools`: `@function_tool` 데코레이터로 정의된 함수 도구
  - `output_type`: Pydantic 모델로 구조화된 출력 정의
- **Session Management**: `SQLiteSession(user_id, db_file)`로 대화 컨텍스트 영구 저장
- **Runner Modes**:
  - `Runner.run()`: 동기 실행 (최종 결과만 반환)
  - `Runner.run_streamed()`: 비동기 스트리밍 (실시간 이벤트)
- **Tracing**: `trace(user_id)` 컨텍스트로 에이전트 상호작용 시각화

### Streaming Event Types
Streamlit UI는 다음 이벤트 타입을 처리:
- `response.output_text.delta`: 텍스트 출력 스트림
- `response.function_call_arguments.delta`: 함수 호출 인자 스트림
- `response.output_text.done` / `response.function_call_arguments.done`: 완료 이벤트
- `response.completed`: 응답 완료

### Database
- `chat-gpt-clone-memory.db`: Streamlit UI 대화 히스토리
- `ai-memory.db`: Jupyter 실험용 대화 히스토리
- User-scoped session 관리
- Session 연산: `add_items()`, `pop_item()`, `clear_session()`, `get_items()`

## Development Commands

### Running the Application
```bash
# Streamlit UI 실행 (권장)
uv run streamlit run main.py

# 또는 run.py 스크립트 사용
python run.py

# 이메일 입력 프롬프트 비활성화
STREAMLIT_EMAIL="" uv run streamlit run main.py
```

### Jupyter Notebooks (실험용)
```bash
# Jupyter Lab 실행
jupyter lab

# 또는 Jupyter Notebook
jupyter notebook
```

### Package Management
```bash
# 의존성 설치
uv sync

# 새 패키지 추가
uv add <package-name>

# 패키지 제거
uv remove <package-name>

# 설치된 패키지 목록
uv pip list
```

## Key Files

### Application
- `main.py`: Streamlit 웹 UI (비동기 스트리밍 채팅)
- `run.py`: Streamlit 실행 헬퍼 스크립트
- `.env`: OpenAI API 키 설정

### Notebooks (실험용)
- `agent-handoff.ipynb`: 멀티 에이전트 handoff 패턴 (지리/경제 전문 에이전트)
- `dummy-agent.ipynb`: SQLiteSession 메모리 기본 사용법

## Environment Variables
- `OPENAI_API_KEY`: OpenAI API 인증 (`.env` 파일에 설정)

## Dependencies
- `openai-agents[viz]`: 에이전트 프레임워크 및 시각화
- `streamlit`: 웹 UI 프레임워크
- `python-dotenv`: 환경 변수 관리
- `graphviz`: 에이전트 그래프 시각화
- `ipykernel`: Jupyter 노트북 지원

## Implementation Notes
- Python 3.13 사용
- `uv` 패키지 매니저로 의존성 관리
- Streamlit 세션 상태로 에이전트 및 SQLite 세션 관리
- 비동기 패턴 (`asyncio.run()`)으로 스트리밍 이벤트 처리
- Agent handoff를 통한 전문 에이전트 라우팅 지원
