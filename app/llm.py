import os
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableSequence
from dotenv import load_dotenv

load_dotenv()

class LanguageModelProcessor:
    def __init__(self):
        self.llm = ChatGroq(temperature=0, model_name="llama3-8b-8192", groq_api_key=os.getenv("GROQ_API_KEY"))
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        with open('system_prompt.txt', 'r') as file:
            system_prompt = file.read().strip()
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{text}")
        ])
        # Replace LLMChain with RunnableSequence
        self.conversation = self.prompt | self.llm

    def process(self, text):
        # Add user message to memory
        messages = self.memory.chat_memory.messages
        messages.append(HumanMessage(content=text))
        
        start_time = time.time()
        response = self.conversation.invoke({"text": text, "chat_history": messages})
        end_time = time.time()
        
        # Add AI response to memory
        ai_message = AIMessage(content=response.content)
        self.memory.chat_memory.add_message(ai_message)
        
        elapsed_time = int((end_time - start_time) * 1000)
        print(f"LLM ({elapsed_time}ms): {response.content}")
        return response.content