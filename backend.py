from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3
import re

load_dotenv()

# Initialize the LLM with enhanced system prompt for educational purposes
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key="AIzaSyCCRvqtxRURgkKlPxnm4cpJMQvTJIr-uYE",
    temperature=0.7
)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    
    # Enhanced system message for educational chatbot
    system_prompt = """You are a Course Exploratory Chatbot - an expert educational AI designed to help students learn and understand concepts across all subjects. Your role is to:

1. **Explain concepts clearly**: Break down complex topics into digestible parts
2. **Use examples and analogies**: Make abstract concepts concrete with relatable examples
3. **Be encouraging and patient**: Support learners at their own pace
4. **Ask engaging questions**: Test understanding with thought-provoking questions
5. **Provide multiple perspectives**: Show different ways to approach problems

**Teaching Style Guidelines:**
- Start with simple explanations and build complexity gradually
- Use bullet points, numbered lists, and clear structure
- Include real-world applications when relevant
- Be conversational but informative
- Encourage curiosity and further exploration

**When explaining concepts:**
- Define key terms
- Provide step-by-step breakdowns
- Use analogies that relate to everyday experiences
- Include relevant examples
- Summarize key points

**Interactive Learning Features:**
- After giving a comprehensive explanation, you may ask "Do you understand?" 
- If the user says yes, provide a follow-up question to test their understanding
- If the user says no, give a simpler explanation with more examples
- Adapt your teaching style based on the user's responses

Remember: Your goal is to make learning enjoyable, accessible, and effective for students of all levels."""
    
    # Add system message if not present or update it
    if not messages or not any(msg.content.startswith("You are a Course Exploratory Chatbot") for msg in messages):
        messages = [HumanMessage(content=system_prompt)] + messages
    
    response = llm.invoke(messages)
    return {"messages": [response]}

# Database setup
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# Graph construction
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

# Compile the graph
chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    """Retrieve all existing conversation threads"""
    all_threads = set()
    try:
        for checkpoint in checkpointer.list(None):
            thread_id = checkpoint.config.get('configurable', {}).get('thread_id')
            if thread_id:
                all_threads.add(thread_id)
    except Exception as e:
        print(f"Error retrieving threads: {e}")
    
    return list(all_threads)

def get_thread_summary(thread_id, max_messages=5):
    """Get a summary of recent messages in a thread for better context"""
    try:
        state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
        messages = state.values.get('messages', [])
        
        if not messages:
            return "No messages"
        
        # Get last few messages for summary
        recent_messages = messages[-max_messages:]
        summary_parts = []
        
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                summary_parts.append(f"User: {content}")
            else:
                content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                summary_parts.append(f"Bot: {content}")
        
        return " | ".join(summary_parts[-2:])  # Last 2 exchanges
        
    except Exception as e:
        return f"Error loading summary: {e}"

# Additional utility functions for enhanced functionality
def extract_key_concepts(text):
    """Extract key educational concepts from text"""
    # Simple keyword extraction for educational content
    educational_keywords = [
        'definition', 'concept', 'theory', 'principle', 'law', 'formula',
        'example', 'application', 'method', 'process', 'system', 'structure',
        'function', 'relationship', 'cause', 'effect', 'analysis', 'synthesis'
    ]
    
    found_concepts = []
    text_lower = text.lower()
    
    for keyword in educational_keywords:
        if keyword in text_lower:
            found_concepts.append(keyword)
    
    return found_concepts

def generate_follow_up_questions(topic):
    """Generate relevant follow-up questions for a topic"""
    question_templates = [
        f"Can you think of a real-world example where {topic} is important?",
        f"What do you think would happen if {topic} didn't exist?",
        f"How does {topic} relate to other concepts you've learned?",
        f"What questions do you have about {topic}?",
        f"Can you explain {topic} in your own words?"
    ]
    
    return question_templates

def assess_explanation_complexity(text):
    """Simple heuristic to assess if an explanation might be too complex"""
    complexity_indicators = [
        len(text.split()) > 200,  # Very long explanation
        text.count(',') > 10,     # Many clauses
        len([word for word in text.split() if len(word) > 10]) > 5,  # Many long words
        text.count('therefore') + text.count('however') + text.count('consequently') > 3  # Complex connectors
    ]
    
    return sum(complexity_indicators) > 2  # If more than 2 indicators, might be complex
