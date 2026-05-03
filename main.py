import os
import json
import math
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ddgs import DDGS

load_dotenv()

# --- Tools ---
@tool
def search_web(query: str) -> str:
    """Search the web for information about a topic."""
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
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

HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        history = []
        for msg in data:
            if msg["role"] == "human":
                history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "ai":
                history.append(AIMessage(content=msg["content"]))
        return history
    return []

def save_history(messages):
    data = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            data.append({"role": "human", "content": msg.content})
        elif isinstance(msg, AIMessage):
            data.append({"role": "ai", "content": msg.content})
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --- System prompt ---
system = SystemMessage(content="""You are a helpful AI assistant with access to tools.
You also remember previous conversations with the user.

If you need to use a tool, respond ONLY with this JSON format and nothing else:
{"tool": "search_web", "args": {"query": "your search here"}}
or
{"tool": "calculator", "args": {"expression": "2+2"}}

Available tools:
- search_web: use for weather, news, current events, facts
- calculator: use for math

If no tool is needed, just respond normally.""")

# --- Chat loop ---
print("AI Assistant (type 'quit' to exit, 'clear' to reset memory)\n")
history = load_history()

while True:
    query = input("You: ")

    if query.lower() == "quit":
        print("Goodbye!")
        break
    if query.lower() == "clear":
        history = []
        os.remove(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else None
        print("Memory cleared!\n")
        continue

    messages = [system] + history + [HumanMessage(content=query)]

    while True:
        response = llm.invoke(messages)
        messages.append(response)

        try:
            data = json.loads(response.content)
            if "tool" in data:
                tool_name = data["tool"]
                tool_args = data["args"]
                print(f"[Using tool: {tool_name}]")
                result = tools_map[tool_name].invoke(tool_args)
                messages.append(HumanMessage(content=f"Tool result: {result}"))
                continue
        except:
            pass

        print(f"\nAssistant: {response.content}\n")
        history.append(HumanMessage(content=query))
        history.append(AIMessage(content=response.content))
        save_history(history)
        break