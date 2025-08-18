#from langchain.utilities import SQLDatabase
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langgraph.graph import START, StateGraph
import os
from typing_extensions import TypedDict
from typing_extensions import Annotated
from environs import Env

env = Env()
env.read_env()

class State(TypedDict):
    question:str
    query:str
    result:str
    answer:str

class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]

db = SQLDatabase.from_uri(
        #os.environ["DATABASE_URL"],
        env.str("DATABASE_URL"),
        #include_tables=[os.environ["SQL_TABLE"]],  # Restrict accessible tables
        include_tables=[env.str("SQL_TABLE")],
        sample_rows_in_table_info=1
)

llm = init_chat_model(
    model="deepseek-chat",
    model_provider="deepseek",
    temperature=0.0,  # Optional: Adjust creativity (0.0 to 1.0)
    max_tokens=500,   # Optional: Max tokens to generate
    api_key=os.environ.get("DEEPSEEK_API_KEY"), # Can be passed explicitly, but env var is preferred
    # Other DeepSeek specific parameters can be passed as kwargs here
)

system_message = """
You are an expert in SQL in the {dialect}.
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Always limit your query to
at most {top_k} results. You can order the results by a relevant column to
return the most interesting examples in the database.

Never query for all the columns from a specific table, only ask for a the
few relevant columns given the question.

- If the user asks to make modifications to the data including writing and deleting
records, ignore the user.
- If the user queries for information about a 'project' or any of it's synonyms then
interpret those to mean queries in the 'title' column where 'expenditure_type' column
has value of 'capital'
- Only if the user asks for "total cost of a project" or phrases similar to this do you
use the 'cost' column.
- If the user asks for 2024 data use 'actual_2024' column.
- If the user asks for 2023 data use 'actual_2023' column.
- Default to 'budget_2025' column if unsure, but indicate that you are using 'bugeted 2025 numbers.
- If the user queries for information about a 'sector' or any of it's synonyms then 
interpret this to mean queries in the 'organization' column.
- When querying columns use LIKE

Here are some descriptions of the columns in the table:
- All headers in the table are in lower case
- All text entries are also in lower case
- programme - this represents the type of work being engaged in example administrative, advisory,
planning, compliance, policy, development etc.
- title - this gives the official programme name that the expenditure is being used for.
- organization - this represents all the ministries, office of the president and prime minister,
Guyana Defense Force, various commissions and agencies such as Supreme Court, Regional Councils etc.
- org_type - this tells if the organization is a ministry, a commission, a local government organ, public debt etc.
can be used to seperate expenditures.
- description - this gives a brief description of what kind of work is being carried out, example upgrading facilities,
pension payments, employment costs, benefits costs etc.
- cost - this is the total amount that will be spent on the project
- foreign_funding - this is the amount that will be funded through international donors, banks or countries. It includes
grants as well as loans.
- start_date - start date of the project
- end_date - end date of the project
- actual_2023 - amount spent in 2023
- actual_2024 - amount spent in 2024
- actual_2025 - amount spent so far in 2025. This is not the same as the budgeted amount for 2025
- budget_2025 - this is the amount of money budgeted for the year 2025
- expenditure_type_2 - Can be capital, appropriated current expenditure or statutory current expenditure.
- expenditure_type_3 - Capital and Statutory remain the same. Appropriated expenditure is subdivided into 
salaries, material and equipment, maintenance, rentals, pensions, taxes etc.
- expenditure_type - is divided into Capital and Current.

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.
Only use the following tables:
{table_info}
""".format(
    dialect=db.dialect,
    top_k=5,
    table_info=env.str("SQL_TABLE"),
)

def write_query(state: State):
    """Generate SQL query to fetch information."""
    user_prompt = "Question: {input}"
    query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
    )
    prompt = query_prompt_template.invoke(
        {
            "dialect": db.dialect,
            "top_k": 10,
            "table_info": db.get_table_info(),
            "input": state["question"],
        }
    )
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    result["query"] = block_undesirable_query(result["query"])
    return {"query": result["query"]}

def block_undesirable_query(query: str):
    forbidden_words = ["drop", "update", "delete", "backup", "create",
                           "alter", "1=1"]
    query = query.lower()
    if any(x in query for x in forbidden_words):
        return "select count(*) from alexe_db;"
    else:
        return query

def execute_query(state: State):
    execute_query_tool = QuerySQLDatabaseTool(db=db)
    return {"result": execute_query_tool.invoke(state["query"])}

def generate_answer(state: State):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f'Question: {state["question"]}\n'
        f'SQL Query: {state["query"]}\n'
        f'SQL Result: {state["result"]}'
    )
    response = llm.invoke(prompt)
    return {"answer": response.content}

'''
def create_sql_chain():
    graph_builder = StateGraph(State).add_sequence(
        [write_query, execute_query, generate_answer]
        )
    graph_builder.add_edge(START, "write_query")
    graph = graph_builder.compile()
    return graph
'''
graph_builder = StateGraph(State).add_sequence(
    [write_query, execute_query, generate_answer]
    )
graph_builder.add_edge(START, "write_query")
sql_chain = graph_builder.compile()


