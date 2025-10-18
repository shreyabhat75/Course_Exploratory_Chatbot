import streamlit as st
from backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid
import re
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Course Exploratory Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for attractive styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .sidebar-section {
        background: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    
    .chat-thread {
        background: #f1f3f4;
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .chat-thread:hover {
        background: #e8eaf6;
        transform: translateX(5px);
    }
    
    .stats-card {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .feature-highlight {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin-bottom: 1rem;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .learning-indicator {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []
    st.session_state['awaiting_understanding'] = False
    st.session_state['current_explanation'] = ""
    st.session_state['question_count'] = 0

def add_thread(thread_id, name="New Chat"):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        st.session_state['thread_names'][thread_id] = name

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])

def extract_keyword(text: str) -> str:
    """Extracts a keyword for naming the chat."""
    common_words = {"what", "is", "the", "a", "an", "tell", "about", "explain", "define", "who", "when", "where", "how", "why"}
    words = re.findall(r"\w+", text.lower())
    for w in words:
        if w not in common_words and len(w) > 2:
            return w.capitalize()
    return "Chat"

def format_message_content(content):
    """Format message content with better styling."""
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            if line.startswith('•') or line.startswith('-'):
                formatted_lines.append(f"  {line}")
            elif line.endswith('?'):
                formatted_lines.append(f"**{line}**")
            else:
                formatted_lines.append(line)
        else:
            formatted_lines.append("")
    
    return '\n'.join(formatted_lines)

# Initialize session state
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if 'thread_names' not in st.session_state:
    st.session_state['thread_names'] = {}

if 'awaiting_understanding' not in st.session_state:
    st.session_state['awaiting_understanding'] = False

if 'current_explanation' not in st.session_state:
    st.session_state['current_explanation'] = ""

if 'question_count' not in st.session_state:
    st.session_state['question_count'] = 0

if 'learning_mode' not in st.session_state:
    st.session_state['learning_mode'] = True

add_thread(st.session_state['thread_id'])

# Main header
st.markdown("""
<div class="main-header">
    <h1>🎓 Course Exploratory Chatbot</h1>
    <p>Your Interactive Learning Companion - Ask, Learn, and Master!</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.markdown("### 🎯 Learning Dashboard")
    
    # Stats
    total_chats = len(st.session_state['chat_threads'])
    current_messages = len(st.session_state['message_history'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{total_chats}</h3>
            <p>Total Chats</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{current_messages}</h3>
            <p>Messages</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Learning Mode Toggle
    st.markdown("### 🎓 Learning Settings")
    st.session_state['learning_mode'] = st.toggle("Interactive Teaching Mode", value=st.session_state['learning_mode'])
    
    if st.session_state['learning_mode']:
        st.markdown("""
        <div class="feature-highlight">
            <strong>Interactive Mode Active!</strong><br>
            The bot will ask if you understand and provide follow-up questions or simpler explanations.
        </div>
        """, unsafe_allow_html=True)
    
    # Chat Management
    st.markdown("### 💬 Chat Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button('🆕 New Chat', help="Start a new conversation"):
            reset_chat()
            st.rerun()
    
    with col2:
        if st.button('🗑️ Clear All', help="Delete all chat history"):
            st.session_state['chat_threads'] = []
            st.session_state['thread_names'] = {}
            st.session_state['message_history'] = []
            st.session_state['thread_id'] = generate_thread_id()
            add_thread(st.session_state['thread_id'])
            st.session_state['awaiting_understanding'] = False
            st.session_state['current_explanation'] = ""
            st.rerun()

    # Conversation History
    st.markdown("### 📚 My Conversations")
    
    if st.session_state['chat_threads']:
        for i, thread_id in enumerate(st.session_state['chat_threads'][::-1]):
            chat_name = st.session_state['thread_names'].get(thread_id, "New Chat")
            is_current = thread_id == st.session_state['thread_id']
            
            button_style = "🟢" if is_current else "💬"
            
            if st.button(f"{button_style} {chat_name}", key=f"chat_button_{thread_id}", help=f"Switch to {chat_name}"):
                st.session_state['thread_id'] = thread_id
                messages = load_conversation(thread_id)
                
                temp_messages = []
                for msg in messages:
                    role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                    temp_messages.append({'role': role, 'content': msg.content})
                
                st.session_state['message_history'] = temp_messages
                st.session_state['awaiting_understanding'] = False
                st.session_state['current_explanation'] = ""
                st.rerun()
    else:
        st.info("No conversations yet. Start chatting below!")

    # Help section
    st.markdown("### ❓ How it Works")
    with st.expander("Learning Features", expanded=False):
        st.markdown("""
        **Interactive Learning Mode:**
        - Bot explains concepts clearly
        - Asks "Do you understand?"
        - Provides quiz questions if you understand
        - Gives simpler explanations if you don't
        
        **Features:**
        - 🎯 Personalized learning pace
        - 📝 Follow-up questions
        - 🔄 Retry explanations
        - 💡 Examples and analogies
        """)

# Main chat interface
st.markdown("### 💬 Chat Interface")

# Display learning indicator if in interactive mode
if st.session_state['learning_mode'] and st.session_state['awaiting_understanding']:
    st.markdown("""
    <div class="learning-indicator">
        🎓 <strong>Interactive Learning Mode:</strong> The bot is waiting for your understanding confirmation.
        Reply with "yes" if you understand, or "no" if you need a simpler explanation.
    </div>
    """, unsafe_allow_html=True)

# Chat messages container
chat_container = st.container()

with chat_container:
    for message in st.session_state['message_history']:
        with st.chat_message(message['role'], avatar="🎓" if message['role'] == 'assistant' else "🧑‍🎓"):
            formatted_content = format_message_content(message['content'])
            st.markdown(formatted_content)

# Chat input
user_input = st.chat_input('Ask me anything about any topic! 🚀', key="chat_input")

if user_input:
    # Add user message to history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    
    with st.chat_message('user', avatar="🧑‍🎓"):
        st.markdown(user_input)
    
    # Update chat name if it's a new chat
    if st.session_state['thread_names'][st.session_state['thread_id']] == "New Chat":
        keyword = extract_keyword(user_input)
        st.session_state['thread_names'][st.session_state['thread_id']] = keyword
    
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    
    # Handle interactive learning mode
    if st.session_state['learning_mode'] and st.session_state['awaiting_understanding']:
        user_response = user_input.lower().strip()
        
        if any(word in user_response for word in ['yes', 'yeah', 'yep', 'understand', 'got it', 'clear']):
            # User understands - ask a follow-up question
            follow_up_prompt = f"""The user understood the explanation about: "{st.session_state['current_explanation']}"

Now ask them a thoughtful follow-up question to test their understanding or help them apply the concept. Make it engaging and educational. Start with "Great! Let me test your understanding:" """
            
            st.session_state['awaiting_understanding'] = False
            st.session_state['question_count'] += 1
            
        elif any(word in user_response for word in ['no', 'nope', 'dont understand', "don't understand", 'confused', 'unclear']):
            # User doesn't understand - provide simpler explanation
            follow_up_prompt = f"""The user did NOT understand the explanation about: "{st.session_state['current_explanation']}"

Please provide a much simpler explanation with easy examples, analogies, or step-by-step breakdown. Use everyday language and relatable examples. After the explanation, ask "Do you understand this explanation?" """
            
            st.session_state['awaiting_understanding'] = True
            
        else:
            # Regular response, treat as new question
            follow_up_prompt = user_input
            st.session_state['awaiting_understanding'] = False
        
        modified_message = HumanMessage(content=follow_up_prompt)
    else:
        modified_message = HumanMessage(content=user_input)
    
    # Generate response
    with st.chat_message('assistant', avatar="🎓"):
        status = st.empty()
        status.markdown("🔍 *Thinking and analyzing...*")
        
        response_container = st.empty()
        full_response = ""
        
        for message_chunk, metadata in chatbot.stream(
            {'messages': [modified_message]},
            config=CONFIG,
            stream_mode='messages'
        ):
            text_piece = message_chunk.content
            full_response += text_piece
            
            formatted_response = format_message_content(full_response)
            response_container.markdown(formatted_response)
        
        status.empty()
        
        # Add to message history
        st.session_state['message_history'].append({'role': 'assistant', 'content': full_response})
        
        # Check if we should enter interactive learning mode
        if st.session_state['learning_mode'] and not st.session_state['awaiting_understanding']:
            # Check if the response seems to be an explanation (contains educational content)
            if any(keyword in full_response.lower() for keyword in ['explain', 'concept', 'means', 'definition', 'understand', 'learn']):
                st.session_state['awaiting_understanding'] = True
                st.session_state['current_explanation'] = user_input
                
                # Add understanding check message
                understanding_check = "Do you understand this explanation? Please reply with 'yes' if it's clear, or 'no' if you'd like me to explain it differently."
                
                with st.chat_message('assistant', avatar="🎓"):
                    st.markdown("---")
                    st.markdown(f"**🎯 {understanding_check}**")
                
                st.session_state['message_history'].append({'role': 'assistant', 'content': f"---\n**{understanding_check}**"})

# Quick action buttons
st.markdown("### 🚀 Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📚 Explain a Concept", help="Ask the bot to explain any concept"):
        st.session_state['quick_input'] = "Explain the concept of"

with col2:
    if st.button("❓ Ask a Question", help="Get help with a specific question"):
        st.session_state['quick_input'] = "I have a question about"

with col3:
    if st.button("🧠 Test Knowledge", help="Get quiz questions on a topic"):
        st.session_state['quick_input'] = "Test my knowledge on"

with col4:
    if st.button("💡 Get Examples", help="Request examples on any topic"):
        st.session_state['quick_input'] = "Give me examples of"

# Display current session info
if st.session_state['message_history']:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Current Session")
    st.sidebar.info(f"Messages: {len(st.session_state['message_history'])}")
    if st.session_state['learning_mode']:
        st.sidebar.info(f"Questions asked: {st.session_state['question_count']}")
        if st.session_state['awaiting_understanding']:
            st.sidebar.warning("⏳ Awaiting understanding confirmation")
