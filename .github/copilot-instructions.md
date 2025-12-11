# Copilot Instructions

ChatGPT 클론 프로젝트 - OpenAI Agents SDK 기반 멀티 에이전트 대화 시스템

## 아키텍처

### 핵심 컴포넌트
- **Streamlit UI** (`main.py`): 비동기 스트리밍 채팅 인터페이스
- **Agent System**: `openai-agents` 라이브러리 기반
  - SQLite 영구 메모리 (`SQLiteSession`)
  - 멀티 에이전트 handoff 아키텍처
  - Function tools 확장 (`@function_tool` 데코레이터)

### Agent 정의 패턴
```python
Agent(
    name="Agent Name",
    instructions="역할 및 행동 지침",
    handoffs=[other_agent],  # 멀티 에이전트 라우팅
    tools=[WebSearchTool(), @function_tool],
    output_type=PydanticModel  # 구조화된 출력
)
```

### Runner 실행 모드
- `Runner.run()`: 동기 실행 (최종 결과만)
- `Runner.run_streamed()`: 비동기 스트리밍 (실시간 이벤트)
  - `response.output_text.delta`: 텍스트 스트림
  - `response.web_search_call.*`: 웹 검색 상태
  - `response.file_search_call.*`: 파일 검색 상태
  - `response.completed`: 완료

## 개발 워크플로우

### 애플리케이션 실행
```bash
# Streamlit UI (권장)
uv run streamlit run main.py

# 이메일 프롬프트 비활성화
STREAMLIT_EMAIL="" uv run streamlit run main.py
```

### 패키지 관리 (uv)
```bash
uv sync           # 의존성 설치
uv add <package>  # 패키지 추가
uv pip list       # 설치 목록
```

### 실험 환경
- `agent-handoff.ipynb`: 멀티 에이전트 handoff 패턴 (지리/경제 전문 에이전트)
- `dummy-agent.ipynb`: SQLiteSession 메모리 기본 사용법

## 프로젝트별 규칙

### Session 관리
- User-scoped session: `SQLiteSession(user_id, db_file)`
- 대화 컨텍스트 영구 저장 (`chat-gpt-clone-memory.db`)
- 연산: `add_items()`, `pop_item()`, `clear_session()`, `get_items()`

### 이벤트 처리 (Streamlit)
`update_status()` 함수로 검색 상태 표시:
- Web/File search `in_progress` → `searching` → `completed`
- `st.status()` 컨테이너로 실시간 업데이트

### 파일 업로드 워크플로우
1. 텍스트/JSON: `client.files.create()` → Vector Store 추가 → 10초 인덱싱 대기
2. 이미지: Base64 인코딩 → Data URI → Session에 직접 저장

### Tracing & 시각화
```python
with trace(user_id):
    await Runner.run(agent, message, session=session)
# 에이전트 상호작용 그래프 자동 생성 (graphviz 필요)
```

## 환경 설정
- `.env`: `OPENAI_API_KEY` 필수
- Vector Store ID: `main.py`의 `VECTOR_STORE_ID` 상수
- Python 3.13+ 필요 (`pyproject.toml`)
