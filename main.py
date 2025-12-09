import streamlit as st
import time

st.header("# ChatGPT Clone!!")

st.button("Click me please!!")

st.text_input("Enter API Key", max_chars=20)

st.feedback("faces")

with st.sidebar:
    st.badge("Badge #1")

tab1, tab2, tab3 = st.tabs(["Agent", "Chat", "Output"])

with tab1:
    st.header("Agent")

with tab2:
    st.header("Chat")

with tab3:
    st.header("Output")


with st.chat_message("ai"):
    st.write("Hello")
    with st.status("Agent is using tool") as status:
        time.sleep(2)
        status.update(label="Agent is searching web...")
        time.sleep(2)
        status.update(label="Agent is reading page...")
        time.sleep(2)
        status.update(label="Agent is done!", state="complete")
        
with st.chat_message("human"):
    st.write("Hello")

st.chat_input("Write a message for the assistant", accept_file=True)
