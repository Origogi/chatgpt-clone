import streamlit as st
from openai import OpenAI
from agents import (
    SQLiteSession,
    Agent,
    Runner,
    WebSearchTool,
    FileSearchTool,
    CodeInterpreterTool,
    HostedMCPTool,
)
from agents.mcp.server import MCPServerStdio
import time
import asyncio
import dotenv
import base64

dotenv.load_dotenv()
client = OpenAI()

VECTOR_STORE_ID = "vs_6938dee473148191a1a36f16115afd73"


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "chat-gpt-clone-memory.db",
    )

session = st.session_state["session"]


async def paint_history():
    message = await session.get_items()
    for message in message:
        if "role" in message:
            if message["role"] == "user":
                content = message["content"]
                with st.chat_message("human"):
                    if isinstance(content, str):
                        st.write(content.replace("$", r"\$"))
                    elif isinstance(content, list):
                        for item in content:
                            if "image_url" in item:
                                st.image(item["image_url"])
            elif message["role"] == "assistant":
                with st.chat_message("ai"):
                    st.write(message["content"][0]["text"].replace("$", r"\$"))
        if "type" in message:
            if message["type"] == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 Searched the web...")
            elif message["type"] == "file_search_call":
                with st.chat_message("ai"):
                    st.write("🗄️ Searched your files...")
            elif message["type"] == "code_interpreter_call":
                with st.chat_message("ai"):
                    st.code(message["code"])
            elif message["type"] == "mcp_list_tools":
                with st.chat_message("ai"):
                    st.write(f"Listed {message['server_label']}'s tools")
            elif message["type"] == "mcp_call":
                with st.chat_message("ai"):
                    st.write(
                        f"Called {message['server_label']}'s {message['name']} with args {message['arguments']}"
                    )


def update_status(status_container, event):
    status_messages = {
        "response.web_search_call.completed": ("✅ Web search completed.", "complete"),
        "response.web_search_call.in_progress": (
            "🔍 Starting web search...",
            "running",
        ),
        "response.web_search_call.searching": (
            "🔍 Web search in progress...",
            "running",
        ),
        "response.completed": (" ", "complete"),
        "response.file_search_call.completed": (
            "✅ File search completed.",
            "complete",
        ),
        "response.file_search_call.in_progress": (
            "🔍 Starting file search...",
            "running",
        ),
        "response.file_search_call.searching": (
            "🔍 File search in progress...",
            "running",
        ),
        "response.code_interpreter_call_code.done": ("🤖 Ran code.", "complete"),
        "response.code_interpreter_call.completed": ("🤖 Ran code.", "complete"),
        "response.code_interpreter_call.in_progress": (
            "🤖 Running code...",
            "complete",
        ),
        "response.code_interpreter_call.interpreting": (
            "🤖 Running code...",
            "complete",
        ),
        "response.mcp_call.in_progress": ("⚒️ Calling MCP tool...", "running"),
        "response.mcp_call.completed": ("✅ MCP tool completed.", "complete"),
        "response.mcp_list_tools.in_progress": ("⚒️ Listing MCP Tools", "running"),
        "response.mcp_list_tools.completed": ("⚒️ Listed MCP Tools", "complete"),
        "response.mcp_list_tools.failed": ("⚒️ Error Listing MCP Tools", "complete"),
        "response.function_call_output": ("📤 Function output received.", "complete"),
        "response.complete": (" ", "complete"),
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


asyncio.run(paint_history())


async def run_agent(message):
    yfinance_server = MCPServerStdio(
        params={
            "command": "uvx",
            "args": ["mcp-yahoo-finance"],
        },
        cache_tools_list=True,
        client_session_timeout_seconds=30,
    )

    timezone_server = MCPServerStdio(
        params={
            "command": "uvx",
            "args": [
                "mcp-server-time",
                "--local-timezone=America/New_York",
            ],
        }
    )

    async with yfinance_server, timezone_server:
        agent = Agent(
            mcp_servers=[
                yfinance_server,
                timezone_server,
            ],
            instructions="""
        You are a helpful assistant.

        You have access to the following tools:
            - File Search Tool : Use this tool FIRST when the user asks a question about facts related to themselves or about specific files.
            - Web Search Tool : Use this when the user asks questions that isn't in your training data, or about current/future events.
            - Code Interpreter : Use this tool when you need to write and run code to answer the user's question.

        IMPORTANT: Never give up on answering a question. Follow this strategy:
            1. First, try File Search if the question might relate to user's files.
            2. If File Search returns no results or insufficient information, use Web Search.
            3. If Web Search also doesn't help, use your own knowledge and reasoning to provide the best possible answer.
            4. For images (characters, objects, places, etc.), analyze the image visually and use Web Search to identify it. Never say "I couldn't find information in files" and stop there.
        """,
            name="ChatGPT Clone",
            model="gpt-4o",
            tools=[
                WebSearchTool(),
                FileSearchTool(
                    vector_store_ids=[VECTOR_STORE_ID],
                    max_num_results=3,
                ),
                CodeInterpreterTool(
                    tool_config={
                        "type": "code_interpreter",
                        "container": {"type": "auto"},
                    }
                ),
                HostedMCPTool(
                    tool_config={
                        "server_url": "https://mcp.context7.com/mcp",
                        "type": "mcp",
                        "server_label": "Context7",
                        "server_description": "Use this to get the doxs from software project",
                        "require_approval": "never",
                    }
                ),
            ],
        )

        with st.chat_message("ai"):
            status_container = st.status("⏳", expanded=False)
            code_placeholder = st.empty()
            text_placeholder = st.empty()

            st.session_state["code_placeholder"] = code_placeholder
            st.session_state["text_placeholder"] = text_placeholder

            response = ""
            code_response = ""

            stream = Runner.run_streamed(agent, message, session=session)

            async for event in stream.stream_events():
                if event.type == "raw_response_event":
                    update_status(status_container, event.data.type)

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response)
                    elif event.data.type == "response.code_interpreter_call_code.delta":
                        code_response += event.data.delta
                        code_placeholder.code(code_response)


prompt = st.chat_input(
    "Write a message for your assistant",
    accept_file=True,
    file_type=[
        "txt",
        "json",
        "png",
        "jpg",
        "jpeg",
        "webp",
    ],
)

if prompt:
    if "code_placeholder" in st.session_state:
        st.session_state["code_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    if prompt.text:
        with st.chat_message("human"):
            st.write(prompt.text)

    for file in prompt.files:
        if file.type.startswith("text/") or file.type.startswith("application/json"):
            with st.chat_message("ai"):
                with st.status("⏳ Uploading file...", expanded=False) as status:
                    upload_file = client.files.create(
                        file=(file.name, file.getvalue()), purpose="user_data"
                    )
                status.update(label="⏳ Attaching file..")
                client.vector_stores.files.create(
                    file_id=upload_file.id, vector_store_id=VECTOR_STORE_ID
                )
                status.update(label="⏳ Indexing file...")
                time.sleep(10)
                status.update(label="✅ File ready.", state="complete")
        elif file.type.startswith("image"):
            with st.status("⏳ Uploading image...", expanded=False) as status:
                file_bytes = file.getvalue()
                file_base64 = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{file.type};base64,{file_base64}"
                asyncio.run(
                    session.add_items(
                        [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_image",
                                        "detail": "auto",
                                        "image_url": data_uri,
                                    }
                                ],
                            }
                        ]
                    )
                )

                status.update(label="✅ Image ready.", state="complete")
            with st.chat_message("human"):
                st.image(data_uri)

    if prompt.text:
        asyncio.run(run_agent(prompt.text))


with st.sidebar:
    reset = st.button("Reset")
    if reset:
        asyncio.run(session.clear_session())
        st.rerun()
    st.write(asyncio.run(session.get_items()))
