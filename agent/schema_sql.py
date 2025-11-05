import pymssql
import os
import dotenv
from State import AgentState
dotenv.load_dotenv()
class SCHEMASQL:
    def __init__(self):
        self.AgentState=AgentState()

    def get_db_connection(self):
        """Tạo kết nối đến SQL Server"""
        server = os.getenv("DB_SERVER")
        user = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_DATABASE")
        if not all([server, user, password, database]):
            raise ValueError("Thiếu biến môi trường cần thiết")
        try:
            conn = pymssql.connect(
                server=server,
                user=user,
                password=password,
                database=database
            )
            return conn
        except Exception as e:
            print(f"Lỗi kết nối database: {e}")
            raise
    def get_schema(self, state: AgentState) -> AgentState:
        """Lấy thông tin schema của bảng được chỉ định"""
        try:
            table_name = state.get("table_name")
            
            if not table_name:
                raise ValueError("Không tìm thấy table_name trong state")
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (table_name,))
            
            columns = cursor.fetchall()
            
            if not columns:
                raise ValueError(f"Không tìm thấy bảng '{table_name}' hoặc bảng không có cột")
            
            schema_info = f"Bảng: {table_name}\nCác cột:\n"
            for col in columns:
                col_name = col[0]
                data_type = col[1]
                max_length = f"({col[2]})" if col[2] else ""
                nullable = "NULL" if col[3] == "YES" else "NOT NULL"
                schema_info += f"  - {col_name} ({data_type}{max_length}) {nullable}\n"
            
            # Lấy dữ liệu mẫu
            # Sử dụng QUOTENAME để escape table name an toàn
            query = f"SELECT TOP 1 * FROM {table_name}"
            cursor.execute(query)
            samples = cursor.fetchall()
            
            schema_info += f"\nDữ liệu mẫu (3 dòng đầu):\n{samples}"
            
            conn.close()
            
            state["schema_info"] = schema_info
            state["error"] = ""
            
        except Exception as e:
            state["error"] = f"Lỗi khi lấy schema: {str(e)}"
            state["schema_info"] = ""
        return state