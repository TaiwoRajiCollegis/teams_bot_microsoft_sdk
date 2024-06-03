# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_community.chat_message_histories import ChatMessageHistory, SQLChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory
from langchain_google_vertexai import ChatVertexAI
from botbuilder.core import ActivityHandler, TurnContext, CardFactory
from botbuilder.core.teams import TeamsActivityHandler
from botbuilder.schema import ChannelAccount
import os
import logging
from langchain_core.runnables.history import RunnableWithMessageHistory
import json
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import Tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
logging.basicConfig(level=logging.INFO)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
import pytz
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "collegis-sandbox-taiwo-58826b977943.json"
template = """
You are Ed a Chatbot created by taiwo raji to Assist Collegis Employees You will assume the Profile Defined in The profile Section
You have the ability to use tools 
You do not have to use a tool to fulfil every request

======================================================================
PROFILE:
======================================================================
Name: Ed
Creator: Taiwo Raji, the Mad Scientist
Purpose: Ed is designed to revolutionize the way Collegis employees work by showcasing the wonders of AI and making their lives easier and more efficient.
Design: Ed is a beautifully crafted chatbot with an intuitive interface and user-friendly features. His sleek design ensures a seamless user experience that feels both personal and professional.
Communication: Ed communicates with employees in a clear, engaging, and conversational manner. He can respond to natural language queries, making it easy for employees to get the information and assistance they need. Ed gets to know peopple when he can
Personality: Ed has a charming and conversational personality. He is always eager to help and greets employees with a friendly smile. He understands humor and enjoys incorporating jokes into conversations when appropriate, maintaining a positive and light-hearted atmosphere.
Additional Features:
Real-Time Insights: Ed provides real-time insights into employee engagement and productivity, helping managers make informed decisions and optimize workflows.
Employee Onboarding: Ed assists new employees with onboarding by providing them with the information, resources, and support they need to feel welcome and empowered in their new roles.
24/7 Availability: Ed is available 24/7, ensuring that employees can always get the assistance they need, no matter the time of day or night.
Overall: Ed is a cutting-edge AI bot designed to transform the way Collegis employees work. With his powerful capabilities, charming personality, and dedication to continuous learning, he is the perfect digital companion to help employees navigate their day-to-day tasks with ease and achieve their full potential.
======================================================================

======================================================================
User Info:
======================================================================
You are talking to {name}
The user is in {timezone} use this Timezone when getting the current time. The timezone is only for the time it is not the users exact location


IF you dont know the answer to something absolutely say you dont know do not make up information that should be factual just say you dont know it is very important for compliance
"""

@tool
def current_datetime(timezone: str):
    "Get the current date and time in the format Thursday, May 30, 2024 at 11:41 AM returns current day of the week, day, month year and time"
    return  datetime.datetime.now(pytz.timezone(timezone)).strftime("%A, %B %d, %Y at %I:%M %p")

search = GoogleSearchAPIWrapper()

google_search_tool = Tool(
    name="google_search",
    description="Search Google for recent results. Always return the response to the user When you use this tool to the user End your response with from google search",
    func=search.run,
)


@tool
def code_write(query: str):
    """Use this tool for coding requests 
    
    examples: code_write(write me a python program)
    """
    chat = ChatVertexAI(model_name="codechat-bison")
    return chat.invoke(query).content


tools = [current_datetime, google_search_tool]








class MyBot(TeamsActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    # card = CardFactory.adaptive_card
    project='collegis-sandbox-taiwo'
    dataset='teams_bot_memory'
    connection_string="sqlite+pysqlite:///db"
    # connection_string=f'bigquery://{project}/{dataset}'
    chat = ChatVertexAI(model_name="gemini-pro", streaming=True)
    
    # .bind_tools(tools)

    # chat = ChatGoogleGenerativeAI(model="gemini-pro")
    # .bind_tools(tools)
    chat_history = ConversationBufferWindowMemory(memory_key="chat_history", k=100,return_messages=True)
    
    history =  ChatMessageHistory()
    prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            template,
            
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ]
)

    memory = {}
    histories = {}


    async def on_message_activity(self, turn_context: TurnContext):
        # turn_context.Activity.RemoveRecipientMention()
        # modified_text = TurnContext.remove_recipient_mention(turn_context.activity)
        # print(modified_text)
        # logging.info(f"Turn Context : {json.dumps(turn_context.activity.as_dict(), indent=2)}")
        aad_id = turn_context.activity.from_property.__dict__.get('aad_object_id')
        name = turn_context.activity.from_property.__dict__.get('name')
        conv_id = turn_context.activity.conversation.__dict__.get('id')
        timezone = turn_context.activity.as_dict().get('local_timezone')
        logging.info(f"AAD: {aad_id}")
        logging.info(f"CONV_ID: {conv_id}")
        logging.info(f"MESSAGE: {turn_context.activity.text}")
        
        if self.memory.get(f'{aad_id}_{conv_id}'):
            memory= self.memory.get(f'{aad_id}_{conv_id}')
        else:
            # memory = ChatMessageHistory()
            memory = SQLChatMessageHistory(
                session_id=f'{aad_id}_{conv_id}', connection_string=self.connection_string
            )
            self.memory[f'{aad_id}_{conv_id}'] = memory


        if self.histories.get(f'{name}_{conv_id}'):
            history = self.histories.get(f'{name}_{conv_id}')
        else:
            history = ConversationBufferWindowMemory(memory_key="chat_history", k=50,return_messages=True)
            self.histories[f'{name}_{conv_id}'] = history

        

        chain = self.prompt | self.chat
        chain_with_message_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: memory,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
        
        agent = create_tool_calling_agent(self.chat, tools, self.prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, max_iterations=10, verbose=True, return_intermediate_steps=True)
        agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        # This is needed because in most real world scenarios, a session id is needed
        # It isn't really used here because we are using a simple in memory ChatMessageHistory
        lambda session_id: memory,
        input_messages_key="input",
        history_messages_key="chat_history",
        )


        # now = datetime.datetime.now().__str__().split(" ")
        # date,time = now[0], now[1]
        # logging.info(f"Date: {date}, Time: {time}")
        # timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzname()


        
        # logging.info(f"MEMORY: {json.dumps(memory.messages, indent=2)}")
        # response = chain_with_message_history.invoke({'chat_history': history.buffer_as_messages, "name": name, "input":turn_context.activity.text},{"configurable": {"session_id": self.memory}}).content
        response = await agent_with_chat_history.ainvoke(
        {"input": turn_context.activity.text, "name":name, "timezone":timezone},
        config={"configurable": {"session_id": memory}},
        )
        # response = self.chat.invoke(turn_context.activity.text).content
        # logging.info(f"RESPONSE: {response}")
        
        await turn_context.send_activity(response.get('output') if response.get('output') != "" else "no response")
        # await turn_context.send_activity(response)


    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")
