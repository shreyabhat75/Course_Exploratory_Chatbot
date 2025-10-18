import streamlit as st
from backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid
import re
import time


# **************************************** utility functions *************************

def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id, name="New Chat"):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        st.session_state['thread_names'][thread_id] = name

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])


def extract_keyword(text: str) -> str:
    """Extracts a keyword for naming the chat."""
    common_words = {"what", "is", "the", "a", "an", "tell", "about", "explain", "define", "who", "when", "where"}
    words = re.findall(r"\w+", text.lower())
    for w in words:
        if w not in common_words:
            return w.capitalize()
    return "Chat"


# **************************************** Session Setup ******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if 'thread_names' not in st.session_state:
    st.session_state['thread_names'] = {}

add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

st.sidebar.title('Course Exploratory Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

if st.sidebar.button('Clear All Chats'):  # ✅ clear chat history
    st.session_state['chat_threads'] = []
    st.session_state['thread_names'] = {}
    st.session_state['message_history'] = []
    st.session_state['thread_id'] = generate_thread_id()
    add_thread(st.session_state['thread_id'])

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    chat_name = st.session_state['thread_names'].get(thread_id, "New Chat")
    if st.sidebar.button(chat_name, key=f"chat_button_{thread_id}"):  # ✅ unique key
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages


# **************************************** Main UI ************************************

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])  # ✅ show formatted markdown

user_input = st.chat_input('Type here')

if user_input:
    # Save user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # ✅ If this is the first user message in this thread, set chat name to a keyword
    if st.session_state['thread_names'][st.session_state['thread_id']] == "New Chat":
        keyword = extract_keyword(user_input)
        st.session_state['thread_names'][st.session_state['thread_id']] = keyword

    # Assistant response
    with st.chat_message('assistant'):
        status = st.empty()   # placeholder for "Analyzing..." and "Got it!"
        status.markdown("🔎 *Analyzing...*")

        response_container = st.empty()
        full_response = ""
        for message_chunk, metadata in chatbot.stream(
            {'messages': [HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode='messages'
        ):
            text_piece = message_chunk.content
            full_response += text_piece

            # ✅ Format output line by line
            formatted_lines = []
            for line in full_response.split("\n"):
                if line.strip():
                    formatted_lines.append(f"- {line.strip()}")  # bullet style
                else:
                    formatted_lines.append("")  # preserve blank line for spacing

            response_container.markdown("\n".join(formatted_lines))

            time.sleep(0.05)  # typing effect

        status.markdown("✅ *Got the answer!*")

    # Save assistant reply (in formatted markdown)
    st.session_state['message_history'].append({'role': 'assistant', 'content': full_response})