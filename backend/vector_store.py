import os
from typing import List
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

load_dotenv()

class VectorStoreManager:
    def __init__(self, index_path: str = "faiss_index"):
        self.index_path = index_path
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables.")

        self.embeddings = OpenAIEmbeddings(
            model="openai/text-embedding-3-small", 
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:3000", 
                "X-Title": "Research Agent"
            }
        )
        self.vector_store = None

    def create_or_update_index(self, documents: List[Document]):
        """
        Takes documents, creates a FAISS index, and saves it locally.
        """
        print(f"Creating index for {len(documents)} chunks...")
        
        if os.path.exists(self.index_path):
            existing_db = FAISS.load_local(
                self.index_path, 
                self.embeddings, 
                allow_dangerous_deserialization=True
            )
            existing_db.add_documents(documents)
            self.vector_store = existing_db
        else:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        
        self.vector_store.save_local(self.index_path)
        print(f"Vector store saved to '{self.index_path}'")

    def get_retriever(self, k: int = 4):
        """
        Returns a retriever. If no index exists, it raises a controlled error
        that our agent can catch and explain to the user.
        """
        if not self.vector_store:
            if os.path.exists(self.index_path):
                self.vector_store = FAISS.load_local(
                    self.index_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
            else:
                raise FileNotFoundError("Empty Index")
        
        return self.vector_store.as_retriever(search_kwargs={"k": k})