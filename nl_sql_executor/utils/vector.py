import os
from langchain_postgres.vectorstores import PGVector
from langchain import hub
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from langchain_core.documents import Document
from typing_extensions import List, TypedDict
from langgraph.graph import START, StateGraph
from environs import Env
import requests

env = Env()
env.read_env()

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

def get_embedding(text: str):
    api_url = env.str("HF_URL")
    headers = {"Authorization": f"Bearer {env.str('HF_API_TOKEN_WRITE')}",
               "Content-Type": "application/json"}
    payload = {"inputs": {
        "source_sentence": text,
        "sentences": [text]
    },
               "options": {"wait_for_model": True}}
    try:
        response = requests.post(api_url, headers=headers, 
                                 json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if response is not None:
            print(f"Response status code: {response.status_code}")
            # This is crucial for 400 errors:
            print(f"Response content: {response.text}")
        return None

def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    prompt = hub.pull("rlm/rag-prompt")
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

#embeddings = get_embedding("What is the document talking about")
embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=env.str("HF_API_TOKEN_READ"),
    task="feature-extraction",
)

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=env.str("DB_COLLECTION_NAME"),
    connection=env.str("DATABASE_URL"),
    use_jsonb=True,
)

llm = ChatDeepSeek(
    temperature=0,
    model="deepseek-chat",
    #model_kwargs={"model_provider":"deepseek"},
    max_tokens=500, 
    api_key=os.environ["DEEPSEEK_API_KEY"]
    )

graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
vector_chain = graph_builder.compile()