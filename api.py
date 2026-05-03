import os
import json
import math
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ddgs import DDGS

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://kAI-rho-one.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

current_date = datetime.now().strftime("%B %d, %Y")

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

# --- Request model ---
class ChatRequest(BaseModel):
    message: str
    history: list

# --- Chat endpoint ---
@app.post("/chat")
async def chat(request: ChatRequest):
    history = []
    for msg in request.history:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history.append(AIMessage(content=msg["content"]))

    messages = [system] + history + [HumanMessage(content=request.message)]

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

        return {"response": response.content}