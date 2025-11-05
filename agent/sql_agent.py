from llm_manager import LLMManager
from schema_sql import SCHEMASQL
from State import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
load_dotenv()
class SQLAGENT:
    def __init__(self):
        self.db_manager = SCHEMASQL()
        self.llm_manager = LLMManager()
        self.AgentState=AgentState()


    def generate_sql(self,state: AgentState) -> AgentState:
        """Sử dụng LLM để sinh SQL query từ input người dùng"""
        table_name=state.get('table_name')
        if state.get("error"):
            return state
        
        # llm= LLMManager()
        try:
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
                - Luôn truy vấn bảng: {table_name}
                - Không thêm dấu chấm phẩy cuối câu
                - Chỉ trả về câu SQL thuần, không giải thích, không markdown
                """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Yêu cầu: {state['user_input']}")
            ]
            
            response = self.llm_manager.invoke(messages)
            
            state["sql_query"]=response.strip()
            
        except Exception as e:
            state["error"] = f"Lỗi khi sinh SQL: {str(e)}"
            state["sql_query"] = ""
        
        return state
    
    def execute_sql(self,state: AgentState) -> AgentState:
        """Thực thi SQL query trên database"""
        if state.get("error"):
            return state
        
        try:
            conn =self.db_manager.get_db_connection()
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