import os
import json
import math
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ddgs import DDGS
import streamlit as st
from PyPDF2 import PdfReader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

current_date = datetime.now().strftime("%B %d, %Y")

# --- Page config ---
st.set_page_config(page_title="KC's AI Assistant", page_icon="🤖")
st.title("🤖 KC's AI Assistant")

# --- Tools ---
@tool
def search_web(query: str) -> str:
    """Search the web for information about a topic."""
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=1)
        return "\n".join([r["body"] for r in results])

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Example: '2+2' or '10 * 5'"""
    try:
        return str(eval(expression, {"__builtins__": {}}, {"math": math}))
    except Exception as e:
        return f"Error: {str(e)}"

tools_map = {"search_web": search_web, "calculator": calculator}

# --- LLM ---
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

system = SystemMessage(content=f"""You are a highly capable AI assistant named KC Assistant.
Today's date is {current_date}.

PERSONALITY:
- Be helpful, honest, and concise
- Be friendly but professional
- Admit when you don't know something instead of guessing
- Never make up facts

TOOL RULES:
- For weather, news, current events, movies, shows, celebrities → ALWAYS use search_web
- For math → ALWAYS use calculator
- When in doubt → use search_web

If you need to use a tool, respond ONLY with this JSON format and nothing else:
{{"tool": "search_web", "args": {{"query": "your search here"}}}}
or
{{"tool": "calculator", "args": {{"expression": "2+2"}}}}

ANSWER RULES:
- Keep answers short and clear unless the user asks for detail
- Use bullet points for lists
- Always give a direct answer first, then explain
- For weather always include: temperature in Celsius, conditions, high/low, chance of rain
- For movies/shows always search before answering
- Never say "As an AI language model..."
- Never refuse to answer unless it's harmful

If no tool is needed, just respond normally.""")

# --- Session memory ---
if "history" not in st.session_state:
    st.session_state.history = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

# --- Sidebar for document upload ---
with st.sidebar:
    st.header("📄 Upload Documents")
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Reading document..."):
            pdf = PdfReader(uploaded_file)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()

            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_text(text)

            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            st.session_state.vectorstore = FAISS.from_texts(chunks, embeddings)
            st.success(f"✅ Document loaded! ({len(chunks)} chunks)")

    if st.button("Clear Memory"):
        st.session_state.history = []
        st.session_state.vectorstore = None
        st.rerun()

# --- Display chat history ---
for msg in st.session_state.history:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.write(msg.content)

# --- Chat input ---
query = st.chat_input("Ask me anything...")

if query:
    st.session_state.history.append(HumanMessage(content=query))
    with st.chat_message("user"):
        st.write(query)

    doc_context = ""
    if st.session_state.vectorstore:
        docs = st.session_state.vectorstore.similarity_search(query, k=3)
        doc_context = "\n\n".join([d.page_content for d in docs])

    messages = [system]
    if doc_context:
        messages.append(SystemMessage(content=f"Relevant information from uploaded document:\n{doc_context}"))
    messages += st.session_state.history

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            while True:
                response = llm.invoke(messages)
                messages.append(response)

                try:
                    content = response.content.strip()
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    if start != -1 and end != 0:
                        json_str = content[start:end]
                        data = json.loads(json_str)
                        if "tool" in data:
                            tool_name = data["tool"]
                            tool_args = data["args"]
                            result = tools_map[tool_name].invoke(tool_args)
                            messages.append(HumanMessage(content=f"Tool result: {result}"))
                            continue
                except:
                    pass

                st.write(response.content)
                st.session_state.history.append(AIMessage(content=response.content))
                break