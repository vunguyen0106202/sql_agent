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
from workflow import WorkflowManager
load_dotenv()

def main():
    table_name = "product"
    input="những thông tin về loại sản phẩm là automotivo"
    workflow_manager = WorkflowManager()
    
    # Gọi method
    result = workflow_manager.run_agent(input, table_name)
    print(f"nKết quả truy vân:{result['query_result']}")
    print(f"\nCâu trả lời: {result['final_answer']}")


if __name__ == "__main__":
    main()