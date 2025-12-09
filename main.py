import streamlit as st
from agents import SQLiteSession, Agent, Runner 
import time
import asyncio
import dotenv

dotenv.load_dotenv()

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        instructions="""
        You are a helpful assistant.
        """,
        name="ChatGPT Clone"
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
        if message["role"] == "user":
            with st.chat_message("human"):
                st.write(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(message["content"][0]["text"])

asyncio.run(paint_history())


async def run_agent(message):
    stream = Runner.run_streamed(agent, message, session=session)

    async for event in stream.stream_events():
        if event.type == "raw_response_event":
            if event.data.type == "response.output_text.delta":
                with st.chat_message("ai"):
                    st.write(event.data.delta)
    

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