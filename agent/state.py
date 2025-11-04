from typing import TypedDict


class AgentState(TypedDict):
    user_input: str
    table_name:str
    schema_info: str
    sql_query: str
    query_result: str
    results:str
    final_answer: str
    error: str
    show_visualization: bool
    visualization_data: dict
