import streamlit as st
from openai import OpenAI
from agents import SQLiteSession, Agent, Runner, WebSearchTool, FileSearchTool
import time
import asyncio
import dotenv
import base64

dotenv.load_dotenv()
client = OpenAI()

VECTOR_STORE_ID = "vs_6938dee473148191a1a36f16115afd73"

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        instructions="""
        You are a helpful assistant.

        You have access to the following tools:
            - Web Search Tool : Use this when the user asks a questions that isn't in your training data.
            Use this tool when the users asks about current or future events, 
            when you think you don't know the answer, try searching for it in the web first.
            - File Search Tool : Use this tool when the user asks a question about facts related to themselves. 
            Or when they ask questions about specitices files.
        """,
        name="ChatGPT Clone",
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[VECTOR_STORE_ID],
                max_num_results=3,
            ),
        ],
    )

agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history", "chat-gpt-clone-memory.db"
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
                        st.write(content.replace("$", "\$"))
                    elif isinstance(content, list):
                        for item in content:
                            if "image_url" in item:
                                st.image(item["image_url"])
            elif message["role"] == "assistant":
                with st.chat_message("ai"):
                    st.write(message["content"][0]["text"].replace("$", "\$"))
        if "type" in message:
            if message["type"] == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 Searching the web...")
            elif message["type"] == "file_search_call":
                with st.chat_message("ai"):
                    st.write("🗄️ Searching the file...")


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
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳", expanded=False)
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(agent, message, session=session)

        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)


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
    st.write(asyncio.run(session.get_items()))
