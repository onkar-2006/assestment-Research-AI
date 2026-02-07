import os
import arxiv
from dotenv import load_dotenv
from typing import Annotated, List, Union
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_tavily import TavilySearch


from vector_store import VectorStoreManager
from prompt import RESEARCH_AGENT_SYSTEM_PROMPT

load_dotenv()

@tool
def search_local_papers(query: str):
    """Searches the research papers ALREADY UPLOADED by the user."""
    try:
        vs_manager = VectorStoreManager()
        retriever = vs_manager.get_retriever(k=3)
        docs = retriever.invoke(query)
        return "\n\n".join([f"Source: {d.metadata.get('source_file')}\nContent: {d.page_content}" for d in docs])
    except FileNotFoundError:
        return "The local document database is currently empty. Inform the user to upload a PDF."
    except Exception as e:
        return f"Error in local search: {str(e)}"


@tool
def search_arxiv(description: str):
    """Searches ArXiv for NEW research papers based on a user's topic."""
    client = arxiv.Client()
    search = arxiv.Search(query=description, max_results=3)
    results = []
    try:
        for result in client.results(search):
            results.append(f"Title: {result.title}\nLink: {result.pdf_url}")
        return "\n---\n".join(results) if results else "No papers found on ArXiv."
    except Exception as e:
        return f"ArXiv error: {str(e)}"


tavily_tool = TavilySearch(k=3)


tools = [search_local_papers, search_arxiv, tavily_tool]
tool_node = ToolNode(tools)

llm = ChatOpenAI(
    model="google/gemini-2.0-flash-001",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Research Agent"
    }
).bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def call_model(state: State):
    messages = [SystemMessage(content=RESEARCH_AGENT_SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

def should_continue(state: State):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
