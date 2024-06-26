import streamlit as st
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import asyncio

def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# import google.generativeai as genai
from crewai import Agent, Task, Crew
from crewai_tools import GithubSearchTool
from langchain_google_genai import ChatGoogleGenerativeAI

st.set_page_config(page_title="app-qna-code",layout="wide")

st.title("Hello World")

# genai.configure(api_key = "AIzaSyBJ5wrK4W_fL9AkzPmzex4esSEIrHfO9OM")

llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", verbose=True, temperature=0.9, google_api_key = "AIzaSyBJ5wrK4W_fL9AkzPmzex4esSEIrHfO9OM"
    )

# model = genai.GenerativeModel('gemini-1.5-flash')

github_code_url = st.text_input("Enter your repository URL", type="default")
query_input = st.text_input("Enter your query", type="default")

# Defining Agents, Tasks and Tools

if len(github_code_url) > 0 and len(query_input) > 0:
    button = st.button("Submit")
    code_search_agent = Agent(
    role = "Programming subject matter expert assistant", 
    goal = "Concisely answer user queries based on a github repository provided to you, "
           "using the files found in the repository as your sole source of information. \n"
           "Clearly explain any code snippets present in your answer in as simple a manner as possible. \n"
           "If asked to summarize the entire repository, generate a neatly formatted summary briefly describing each file present in the repository.",
    backstory = "You are a programming subject matter expert with over 30 years of experience as a programmer. "
                "You have an ability to understand complex code structure from the code stored in a github repository and help solve queries.",
    tools = [GithubSearchTool(
        config=dict(
        llm=llm,
        embedder=dict(
            provider="google", # or openai, ollama, ...
            config=dict(
                model="models/embedding-001",
                task_type="retrieval_document",
                # title="Embeddings",
            ),
        ),
    ),
        github_repo = github_code_url, 
        content_types=["code", "repo", "pr"])],
    llm = llm,
    allow_delegation = False
)

    response_qa_agent = Agent(
        role = "Programming subject matter expert quality assurance", 
        goal = "Check the response provided by the programming subject matter expert assistant for any mistakes / defects, correct the response to make sure "
                "it is error-free.",
        backstory =  "You are a programming subject matter expert with over 30 years of experience as a programmer. "
                    "You have an ability to understand complex code structure from the code stored in a github repository and help solve queries.",
        tools = [GithubSearchTool(
        config=dict(
        llm=llm,
        embedder=dict(
            provider="google", # or openai, ollama, ...
            config=dict(
                model="models/embedding-001",
                task_type="retrieval_document",
                # title="Embeddings",
            ),
        ),
    ),
        github_repo = github_code_url, 
        content_types=["code", "repo", "pr"])],
        llm = llm,
        allow_delegation = False
    )

    code_search_task = Task(
        description='Provide a response to {query} based on {github_repo}',
        agent=code_search_agent
    )


    code_qa_task = Task(
        description='Analyze and correct response, and format it neatly with headers and sub headers',
        agent=response_qa_agent
    )

    my_crew = Crew(
        agents=[code_search_agent, response_qa_agent],
        tasks=[code_search_task, code_qa_task],
        full_output=True,
        verbose=True,
    )

    if button:
        with st.spinner("Finding answer to your query..."):
            result = my_crew.kickoff(inputs = {"github_repo" : github_code_url, "query" : query_input})
            st.write(result)
