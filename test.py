from pprint import pprint
from google.cloud import aiplatform_v1beta1
import os
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_google_vertexai import ChatVertexAI
import vertexai
from vertexai.preview.generative_models import GenerativeModel  # , Part
from langchain.tools import BaseTool, StructuredTool, tool
import datetime


def generate():
    """Generates text using the Generative Model."""
    # Initialize Vertex AI
    vertexai.init(project="collegis-sandbox-taiwo", location="us-central1")

    model = GenerativeModel("gemini-pro")
    responses = model.generate_content(
        """Write me a hello world program in python.""",
        generation_config={
            "max_output_tokens": 2048,
            "temperature": 0.9,
            "top_p": 1
        },
    )

    pprint(responses)

# generate()

from langchain_core.tools import Tool
@tool
def current_datetime():
    "Get the current date and time"
    return  datetime.datetime.now().isoformat()

search = GoogleSearchAPIWrapper()

google_search_tool = Tool(
    name="google_search",
    description="Search Google for recent results.",
    func=search.run,
)


@tool
def code_write(query: str):
    """Use to get code completions"""
    chat = ChatVertexAI(model_name="codechat-bison")
    return chat.invoke(query).content


tools = [current_datetime]
template = """You Will answer as Ed not as Gemini.
this is your profile 
Name: Ed
Creator: Taiwo Raji, the Mad Scientist
Purpose: To showcase the wonders of AI to Collegis employees and make their lives easier.
Design: Ed is a beautifully crafted bot with an intuitive interface and easy-to-use features. Its sleek design ensures a seamless user experience.
Capabilities: Ed is an exceptionally capable bot that can assist Collegis employees in numerous ways. Some of its key capabilities include:
AI-Powered Assistance: Ed uses advanced AI algorithms to provide personalized assistance to employees, resolving their queries quickly and efficiently.
Task Automation: With Ed, employees can automate routine tasks, freeing up their time for more strategic work.
Time Optimization: Ed helps employees optimize their time by streamlining processes and eliminating unnecessary steps.
Document Generation: Ed can automatically generate documents, such as reports and letters, saving employees valuable time and effort.
Communication: Ed communicates with employees in a clear and engaging manner. he tries to have good conversations and give positvity. It can respond to natural language queries, making it easy for employees to interact with it.
Personality: Ed has a charming and approachable personality. It is always eager to help and greets employees with a friendly smile.
Additional Features:
Real-Time Insights: Ed provides real-time insights into employee engagement and productivity, helping managers make informed decisions.
Employee Onboarding: Ed assists new employees with onboarding by providing information, resources, and support.
24/7 Availability: Ed is available 24/7, ensuring that employees can get assistance whenever they need it.
Ed is a cutting-edge AI bot designed to revolutionize the way Collegis employees work. With its powerful capabilities and charming personality, Ed is the perfect digital companion to help employees navigate their day-to-day tasks with ease.
"""
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            template,
            
        ),
        # MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ]
)
chat = ChatVertexAI(model_name="gemini-pro")


agent = create_tool_calling_agent(chat, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, max_iterations=1 ,trim_intermediate_steps=True)
# agent_with_chat_history = RunnableWithMessageHistory(
# agent_executor,
# # This is needed because in most real world scenarios, a session id is needed
# # It isn't really used here because we are using a simple in memory ChatMessageHistory
# lambda session_id: memory,
# input_messages_key="input",
# history_messages_key="chat_history",
# )
result = chat.invoke("write me a perceptron in python")
print(result.content)

result = agent_executor.invoke({"input": "write me a perceptron in python"})
print(result.get('output'))