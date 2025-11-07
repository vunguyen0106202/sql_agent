from langgraph.graph import StateGraph
from State import AgentState
from langgraph.graph import END
from sql_agent import SQLAGENT
from schema_sql import SCHEMASQL

class WorkflowManager:
    def __init__(self):
        self.db_manager = SCHEMASQL()
        self.sql_agent=SQLAGENT()

    def create_workflow(self)-> StateGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node("get_schema", self.db_manager.get_schema)
        workflow.add_node("generate_sql", self.sql_agent.generate_sql)
        workflow.add_node("execute_sql", self.sql_agent.execute_sql)
        # workflow.add_node("check_visualization", check_visualization)
        # workflow.add_node("create_visualization", create_visualization)
        workflow.add_node("generate_answer", self.sql_agent.generate_answer)
        workflow.set_entry_point("get_schema")
        workflow.add_edge("get_schema", "generate_sql")
        workflow.add_edge("generate_sql", "execute_sql")
        workflow.add_edge("execute_sql","generate_answer")
        # workflow.add_edge("execute_sql", "check_visualization")
        # routing
        # workflow.add_conditional_edges(
        #     "check_visualization",
        #     route_after_check,
        #     {
        #         "create_visualization": "create_visualization",
        #         "skip": "generate_answer"
        #     }
        # )
        
        # workflow.add_edge("create_visualization", "generate_answer")
        workflow.add_edge("generate_answer", END)
        return workflow.compile()

    def run_agent(self,user_input: str,table_name:str):
        """Chạy agent với input từ người dùng"""
        graph = self.create_workflow()
        
        initial_state = {
            "user_input": user_input,
            "table_name":table_name,
            "schema_info":"",
            "sql_query": "",
            "query_result":"",
            "results":"",
            "final_answer": "",
            "error": "",
            "show_visualization":1,
            "visualization_data": []
        }
        result = graph.invoke(initial_state)
        return result