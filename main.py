import streamlit as st
from agents import SQLiteSession, Agent, Runner, WebSearchTool
import time
import asyncio
import dotenv

dotenv.load_dotenv()

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        instructions="""
        You are a helpful assistant.

        You hava access to the following tools:
            - Web Search Tool : Use this when the user asks a questions that isn't in your training data. Use this to learn about current events
        """,
        name="ChatGPT Clone",
        tools=[
            WebSearchTool()   
        ]
    )

agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "chat-gpt-clone-memory.db"
    )

session = st.session_state["session"]

async def paint_history():
    message = await session.get_items()
    for message in message:
        if "role" in message:
            if message["role"] == "user":
                with st.chat_message("human"):
                    st.write(message["content"])
            elif message["role"] == "assistant":
                with st.chat_message("ai"):
                    st.write(message["content"][0]["text"])
        if "type" in message:
            if message["type"] == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 Searching the web...")

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
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)

asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        status_container = st.status("⏳",expanded=False)
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(agent, message, session=session)

        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)
                
                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)
    

prompt = st.chat_input("Write a message for your assistant")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))    


with st.sidebar:
    reset = st.button("Reset")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))