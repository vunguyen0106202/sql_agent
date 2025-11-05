import sys
import os
from State import AgentState
from schema_sql import SCHEMASQL
from sql_agent import SQLAGENT
from llm_manager import LLMManager
import sqlite3
from typing import Literal, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os
from langsmith import traceable
import pandas as pd
import matplotlib.pyplot as plt
from langchain_core.messages import AIMessage
from dotenv import load_dotenv
load_dotenv()

def main():
    table_name = "product"
    llm=LLMManager()
    # Khởi tạo state
    input="những thông tin về loại sản phẩm là automotivo"
    
    state = {
        "user_input":input,
        "table_name": table_name,
        "schema_info": "",
        "sql_query": "",
        "query_result": "",
        "results": "",
        "final_answer": "",
        "error": "",
        "show_visualization": False,
        "visualization_data": {}
    }   
    schema=SCHEMASQL()
    state=schema.get_schema(state)
    agent1=SQLAGENT()
    state=agent1.generate_sql(state)
    state=agent1.execute_sql(state)
    print(state["sql_query"])
    print(state['query_result']) 



if __name__ == "__main__":
    main()