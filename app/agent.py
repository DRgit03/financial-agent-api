from langchain_ollama import ChatOllama
from langchain.agents import Tool, AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph
from typing import TypedDict, List, Dict, Any
from app.tools import validate_uploaded_pdfs, summarize_financials


tools = [
    Tool.from_function(
        func=validate_uploaded_pdfs,
        name="validate_uploaded_pdfs",
        description="Validate uploaded financial PDFs using extracted income statements"
    ),

     Tool.from_function(func=summarize_financials, name="summarize_financials", description="testing prompts")
]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a financial document validation agent. Use the tool to validate PDFs."),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

class AgentState(TypedDict):
    input: str
    validation_requests: List[Dict[str, Any]]
    results: List[Dict[str, Any]]
    summary: str


# def invoke_agent(state: AgentState) -> AgentState:
#     llm = ChatOllama(model="mistral")  # Ensure 'ollama' and model are ready
#     agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
#     executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

#     #FIX: Call the raw Python function instead of the wrapped tool
#     raw_tool_fn = validate_uploaded_pdfs.func  # Extract original function

#     output = raw_tool_fn(state["validation_requests"])
    

#     return {
#         "input": state["input"],
#         "validation_requests": state["validation_requests"],
#         "results": output,
#         "summary": summary

#     }
    #What is api and it description

def invoke_agent(state: AgentState) -> AgentState:
    llm = ChatOllama(model="mistral")
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    raw_tool_fn = validate_uploaded_pdfs.func
    output = raw_tool_fn(state["validation_requests"])

    summary = "Summary not available."
    try:
        summary_tool = summarize_financials.func
        summary = summary_tool(output)
    except Exception as e:
        summary = f" Summary generation failed: {str(e)}"

    return {
        "input": state["input"],
        "validation_requests": state["validation_requests"],
        "results": output,
        "summary": summary  
    }


def create_langgraph_agent():
    graph = StateGraph(AgentState)
    graph.add_node("invoke", invoke_agent)
    graph.set_entry_point("invoke")
    graph.set_finish_point("invoke")
    return graph.compile()

