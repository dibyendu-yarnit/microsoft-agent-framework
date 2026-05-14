import asyncio
import re

import streamlit as st

from agent import create_agent
from schemas import AgentOutput

st.set_page_config(page_title="Gemini Chat", page_icon="💬")
st.title("Gemini Chat")

if "agent" not in st.session_state:
    st.session_state.agent = asyncio.run(create_agent())

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            with st.expander("Details"):
                st.write(f"Sentiment: {msg['sentiment']}")
                st.write(f"Score: {msg['score']:.2f}")

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()

        async def _stream():
            accumulated = ""
            stream = st.session_state.agent.run(prompt, stream=True)
            async for update in stream:
                accumulated += update.text
                match = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)', accumulated)
                display = match.group(1) if match else ""
                placeholder.markdown((display or "...") + "▌")
                
            return await stream.get_final_response()

        final_response = asyncio.run(_stream())
        output = AgentOutput.model_validate_json(final_response.text)

        placeholder.markdown(output.answer)
        with st.expander("Details"):
            st.write(f"Sentiment: {output.sentiment}")
            st.write(f"Score: {output.score:.2f}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": output.answer,
        "sentiment": output.sentiment,
        "score": output.score,
    })
