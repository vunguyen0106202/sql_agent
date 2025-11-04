import sqlite3
from typing import Literal, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os
from langsmith import traceable
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
load_dotenv()

# Cấu hình
# os.environ["GROQ_API_KEY"] = "your_groq_api_key_here"

# Định nghĩa State
class AgentState(TypedDict):
    user_input: str
    schema_info: str
    sql_query: str
    query_result: str
    results:str
    final_answer: str
    error: str
    show_visualization: bool
    visualization_data: dict

# Khởi tạo Groq LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant", 
    temperature=0
)

# Kết nối SQLite
def get_db_connection():
    conn = sqlite3.connect("data1.db")
    return conn

# Node 1: Lấy schema của bảng
@traceable
def get_schema(state: AgentState) -> AgentState:
    """Lấy thông tin schema của bảng auto_table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Lấy thông tin cột
        cursor.execute("PRAGMA table_info(auto_table)")
        columns = cursor.fetchall()
        
        schema_info = "Bảng: auto_table\nCác cột:\n"
        for col in columns:
            schema_info += f"  - {col[1]} ({col[2]})\n"
        
        cursor.execute("SELECT * FROM auto_table LIMIT 3")
        samples = cursor.fetchall()
        schema_info += f"\nDữ liệu mẫu (3 dòng đầu):\n{samples}"
        
        conn.close()
        
        state["schema_info"] = schema_info
        state["error"] = ""
        
    except Exception as e:
        state["error"] = f"Lỗi khi lấy schema: {str(e)}"
        state["schema_info"] = ""
    
    return state

# Node 2: Sinh SQL query
@traceable
def generate_sql(state: AgentState) -> AgentState:
    """Sử dụng LLM để sinh SQL query từ input người dùng"""
    if state.get("error"):
        return state
    
    try:
#         system_prompt = f"""Bạn là một chuyên gia SQL. Nhiệm vụ của bạn là tạo câu truy vấn SQL chính xác dựa trên yêu cầu của người dùng.

        # Thông tin database:
        # {state['schema_info']}

        # Quy tắc:
        # - Chỉ trả về câu SQL, không giải thích
        # - Sử dụng đúng tên bảng: auto_table
        # - Đảm bảo syntax SQLite đúng
        # - Không thêm dấu chấm phẩy ở cuối
        # """
        system_prompt = f"""Bạn là một chuyên gia SQL. Nhiệm vụ của bạn là tạo câu truy vấn SQL chính xác dựa trên yêu cầu của người dùng.

            Thông tin database:
            {state['schema_info']}
            Quy Tắc:
            - Nếu người dùng hỏi "tên là ...", "chứa ...", "có ...", "bao gồm ...", "giống ..." → dùng LIKE '%từ_khóa%'
            - Nếu người dùng hỏi "bắt đầu bằng ..." → dùng LIKE 'từ_khóa%'
            - Nếu người dùng hỏi "kết thúc bằng ..." → dùng LIKE '%từ_khóa'
            - Nếu người dùng nhắc đến nhiều giá trị (ví dụ: 'trạng thái là done hoặc fail') → dùng IN ('done','fail')
            - Nếu người dùng nói "rỗng", "chưa có", "trống" → dùng IS NULL hoặc = ''
            - Nếu người dùng nói "trong khoảng thời gian ..." → dùng BETWEEN hoặc >=, <= tương ứng
            - Nếu người dùng hỏi liên quan đến ngày, tháng, năm (ví dụ 'ngày 1/7/2025', 'tháng 4 năm 2025'):
                → KHÔNG được dùng dấu '=' với giá trị có định dạng 'YYYY-MM-DD 00:00:00'
                → Thay vào đó dùng một trong hai cách sau:
                    + Dùng LIKE 'YYYY-MM-DD%' để khớp mọi thời gian trong ngày đó
                    + Hoặc dùng hàm date() của SQLite, ví dụ: date(Report_Time) = 'YYYY-MM-DD'
            - Luôn đảm bảo syntax SQLite đúng chuẩn
            - Luôn truy vấn bảng: auto_table
            - Không thêm dấu chấm phẩy cuối câu
            - Chỉ trả về câu SQL thuần, không giải thích, không markdown
            """

        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Yêu cầu: {state['user_input']}")
        ]
        
        response = llm.invoke(messages)
        sql_query = response.content.strip()
        
        # Loại bỏ markdown code blocks nếu có
        if sql_query.startswith("```"):
            sql_query = sql_query.split("\n", 1)[1]
            sql_query = sql_query.rsplit("```", 1)[0]
        
        state["sql_query"] = sql_query.strip()
        
    except Exception as e:
        state["error"] = f"Lỗi khi sinh SQL: {str(e)}"
        state["sql_query"] = ""
    
    return state

# Node 3: Thực thi SQL query
@traceable
def execute_sql(state: AgentState) -> AgentState:
    """Thực thi SQL query trên database"""
    if state.get("error"):
        return state
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(state["sql_query"])
        results = cursor.fetchall()
        
        # Lấy tên cột
        column_names = [description[0] for description in cursor.description]
        
        conn.close()
        
        # Format kết quả
        result_str = f"Cột: {column_names}\n\nKết quả ({len(results)} dòng):\n"
        for row in results[:10]:  # Giới hạn 10 dòng
            result_str += f"{row}\n"
        
        if len(results) > 10:
            result_str += f"\n... và {len(results) - 10} dòng khác"
        
        state["query_result"] = result_str
        
    except Exception as e:
        state["error"] = f"Lỗi khi thực thi SQL: {str(e)}"
        state["query_result"] = ""
    
    return state
@traceable
def check_visualization(state: AgentState) -> AgentState:
    
    user_input = state["user_input"].lower()
    query_result = state.get("query_result", "")
    
    # Từ khóa trigger visualization
    viz_keywords = [
        "tháng", 
    ]
    
    # Kiểm tra user input có chứa từ khóa không
    has_viz_keyword = any(keyword in user_input for keyword in viz_keywords)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(state["sql_query"])
    results = cursor.fetchall()
    re_viz=False
    report_time=0
    clear_Time=0
    if len(results)>1:
        
        for description in cursor.description:
            if description[0]=="Report_Time":
                report_time=1
            elif description[0]=="Clear_Time":
                clear_Time=1    
        if(clear_Time==1&report_time==1):    
            re_viz=True
    
    # Quyết định có cần visualization không
    state["show_visualization"] = has_viz_keyword and re_viz
    # state["show_visualization"]=re_viz 
    
    if not state.get("show_visualization"):
        state["show_visualization"] = False    
    return state

# Node 5: Tạo visualization
@traceable
def create_visualization(state: AgentState) -> AgentState:
    """
    Tạo biểu đồ từ dữ liệu query
    """
    if not state.get("show_visualization", False):
        return state
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(state["sql_query"])
    results = cursor.fetchall()
    
    # Lấy tên cột
    column_names = [description[0] for description in cursor.description]
    df = pd.DataFrame(results, columns=column_names)
    df["Report_Time"] = pd.to_datetime(df["Report_Time"])
    df["Clear_Time"] = pd.to_datetime(df["Clear_Time"])
    
    df = df.sort_values("Report_Time").reset_index(drop=True)
    merged = []
    current_start, current_end= df.loc[0, ["Report_Time", "Clear_Time"]]

    for i in range(1, len(df)):
        start, end = df.loc[i, ["Report_Time", "Clear_Time"]]
        if start <= current_end:  
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end= start, end

    merged.append((current_start, current_end)) 

    df_merged = pd.DataFrame(merged, columns=["Report_Time", "Clear_Time"])
    df_merged["Downtime_hours"] = (df_merged["Clear_Time"] - df_merged["Report_Time"]).dt.total_seconds() / 3600
    df_merged["Date"] = df_merged["Report_Time"].dt.date
    daily_downtime = df_merged.groupby("Date")["Downtime_hours"].sum()
    state['visualization_data']=daily_downtime
    plt.figure(figsize=(10, 5))
    daily_downtime.plot(kind="bar", color="steelblue")
    plt.title("Tổng thời gian downtime theo ngày")
    plt.xlabel("Ngày")
    plt.ylabel("Số giờ downtime")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

    return state
# Node 4: Tạo câu trả lời cuối cùng
@traceable
def generate_answer(state: AgentState) -> AgentState:
    """Sử dụng LLM để tạo câu trả lời tự nhiên từ kết quả"""
    if state.get("error"):
        state["final_answer"] = f"{state['error']}"
        return state
    
    try:
        system_prompt = """Bạn là trợ lý phân tích dữ liệu. Hãy tóm tắt kết quả truy vấn một cách dễ hiểu và thân thiện."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""Người dùng hỏi: {state['user_input']}

            SQL đã thực thi: {state['sql_query']}

            Kết quả:
            {state['query_result']}
            
            Hãy trả lời câu hỏi của người dùng dựa trên kết quả trên.
            Câu trả lời đúng với yêu cầu và đầu câu cần tổng hợp số lượng truy vấn lấy đc""")
                    ]
        
        response = llm.invoke(messages)
        state["final_answer"] = response.content
        
    except Exception as e:
        state["final_answer"] = f"Lỗi khi tạo câu trả lời: {str(e)}"
    
    return state
# def check_visualization(state: AgentState) -> AgentState:
#     return state
# def create_visualization(state: AgentState) -> AgentState:

#     return state
def route_after_check(state: AgentState) -> Literal["create_visualization", "skip"]:
    """Điều hướng sau khi check visualization"""
    if state.get("show_visualization", False):
        return "create_visualization"
    return "skip"
# Xây dựng LangGraph
def build_graph():
    workflow = StateGraph(AgentState)
    
    # Thêm các nodes
    workflow.add_node("get_schema", get_schema)
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("check_visualization", check_visualization)
    workflow.add_node("create_visualization", create_visualization)
    workflow.add_node("generate_answer", generate_answer)
    
    # Định nghĩa luồng
    workflow.set_entry_point("get_schema")
    workflow.add_edge("get_schema", "generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "check_visualization")
    # routing
    workflow.add_conditional_edges(
        "check_visualization",
        route_after_check,
        {
            "create_visualization": "create_visualization",
            "skip": "generate_answer"
        }
    )
    
    workflow.add_edge("create_visualization", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    return workflow.compile()

# Hàm chạy agent


@traceable
def run_agent(user_input: str):
    """Chạy agent với input từ người dùng"""
    graph = build_graph()
    
    initial_state = {
        "user_input": user_input,
        "schema_info": "",
        "sql_query": "",
        "query_result": "",
        "final_answer": "",
        "error": ""
    }
    # if os.name == 'nt':  
    #     os.startfile("workflow_diagram.png")
    result = graph.invoke(initial_state)
    # with tracing_v2_enabled(project_name="LangGraph SQL Agent"):
    #     result = graph.invoke(initial_state)
    print("\n" + "="*60)
    print("KẾT QUẢ PHÂN TÍCH")
    print("="*60)
    print(f"\nCâu hỏi: {result['user_input']}")
    print(f"\nSQL Query: {result['sql_query']}")
    print(f"\nKết quả Query:{result['query_result']}")
    print(f"\nCâu trả lời:\n{result['final_answer']}")
    print("\n" + "="*60)
    
    return result


# Main
if __name__ == "__main__":
    # Tạo database mẫu
    # setup_sample_database()
    
    print("SQL Agent với LangGraph và Groq")
    print("Nhập 'exit' để thoát\n")
    
    while True:
        user_input = input("\nNhập câu hỏi của bạn: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Tạm biệt!")
            break
        
        if not user_input:
            continue
        
        run_agent(user_input)