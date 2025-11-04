from schema_sql import SCHEMASQL
from state import AgentState

# Tạo state dict với table_name
state = {
    "table_name": "product"
}

result = SCHEMASQL.get_schema(state)

print(result.get("schema_info"))