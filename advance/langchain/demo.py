import os
os.environ["OPENAI_API_KEY"] = '你的Open API Key'
from langchain.chat_mod5ieBels import ChatOpenAI

ChatOpenAI()

chat = ChatOpenAI(model="gpt-4",
                    temperature=0.8,
                    max_tokens=60)

from langchain.schema import (
    HumanMessage,
    SystemMessage
)
messages = [
    SystemMessage(content="你是一个很棒的智能助手"),
    HumanMessage(content="请给我的花店起个名")
]
response = chat(messages)
print(response)
