# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from botbuilder.core import ActivityHandler, TurnContext, CardFactory
from botbuilder.schema import ChannelAccount
from botbuilder.core.show_typing_middleware import ShowTypingMiddleware
import os
import logging
import json

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "collegis-sandbox-taiwo-58826b977943.json"
system = """You Will answer as Ed not as Gemini.
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

class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    # card = CardFactory.adaptive_card
    chat = ChatVertexAI(model_name="gemini-pro", convert_system_message_to_human=True)
    async def on_message_activity(self, turn_context: TurnContext):
        # turn_context.Activity.RemoveRecipientMention()
        # modified_text = TurnContext.remove_recipient_mention(turn_context.activity)
        # print(modified_text)
        name = turn_context.get
        logging.info(turn_context.activity.text)
        prompt = ChatPromptTemplate.from_messages([("system", system), ("human", turn_context.activity.text)])
        chain = prompt | self.chat
        response = chain.invoke({}).content
        logging.info(response)
        await turn_context.send_activity(response)

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")
