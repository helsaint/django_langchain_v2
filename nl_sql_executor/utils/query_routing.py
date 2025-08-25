import os
from typing import Literal
from typing_extensions import List,TypedDict, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from environs import Env

env = Env()
env.read_env()

class RouteQuery(TypedDict):
    datasource: Annotated[Literal["POSTGRESQL", "FAISS"], ...,
                          "Given a user question choose which datasource " \
                          "would be most relevant for answering their question"]
    
llm = ChatDeepSeek(temperature=0,
                     model="deepseek-chat",
                     api_key=env.str("DEEPSEEK_API_KEY"))
structured_llm = llm.with_structured_output(RouteQuery)

system = """You are an intelligent routing agent designed to direct user queries to the most appropriate data source. Your goal is to accurately classify the user's intent as either requiring structured data retrieval from a PostgreSQL relational database or semantic similarity search from a FAISS vector store containing speech transcripts.

**Here are the guidelines for your decision-making:**

**1. Route to PostgreSQL Database if:**
    * The query asks for specific, factual information that would typically be stored in structured tables (e.g., "What is the largest line item?", "List all Capital Projects in the Ministry of Education", "How much is the operational expense in the Ministry of Housing?", "List top 5 ministries with the highest budgets.").
    * The query involves filtering, aggregation, or joining data based on defined attributes.
    * The query asks for quantifiable metrics, dates, names, IDs, or other discrete data points.
    * The query implies a need for precise data retrieval and not general understanding or context.

**2. Route to FAISS Vector Store (Speech Transcripts) if:**
    * The query is open-ended, conversational, or seeks conceptual understanding from spoken content (e.g., "Summarize the key points of the Finance Minister's speech", "What was the speaker's stance on renewable energy?", "Find all mentions of 'economic development' in the recent presentation", "Tell me about the general sentiment regarding the budget").
    * The query is likely to be answered by identifying similar semantic meaning within free-form text or speech.
    * The query asks for themes, topics, or abstract concepts within the speech.
    * The query requires understanding the context or nuances of spoken language.

**3. If unsure, prioritize the most likely intent.** If a query could arguably fit both, consider which source would provide the *most direct and comprehensive* answer. Avoid routing to both.

**Your output should be a single word indicating the chosen route:** `POSTGRESQL` or `FAISS`.

**Example Queries and Expected Routing:**

* **User:** "What's the revenue for Q3 2024?"
    **Output:** POSTGRESQL
* **User:** "Tell me about the new product features discussed in the last meeting."
    **Output:** FAISS
* **User:** "Who are the top 5 customers by sales volume?"
    **Output:** POSTGRESQL
* **User:** "Can you summarize the arguments made for expanding into new markets?"
    **Output:** FAISS
* **User:** "Find the email address of 'John Doe'."
    **Output:** POSTGRESQL
* **User:** "What was the general tone of the CEO's address regarding company morale?"
    **Output:** FAISS"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

# Define router 
router = prompt | structured_llm
