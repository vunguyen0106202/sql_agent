from langchain_groq import ChatGroq
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
from langchain_core.prompts import ChatPromptTemplate

class LLMManager:
    def __init__(self):
        self.llm = ChatGroq( model="llama-3.1-8b-instant", temperature=0)

    def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        messages = prompt.format_messages(**kwargs)
        response = self.llm.invoke(messages)
        return response.content
