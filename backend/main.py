import os
import shutil
import uuid  
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from data_ingestion import DocumentIngestor
from vector_store import VectorStoreManager
from agent import app as agent_graph

load_dotenv()

app = FastAPI(title="AI Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_session" 

@app.get("/")
async def root():
    return {"status": "online", "message": "Research Agent API is running"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
        print(f"Received file: {file.filename}")

        ingestor = DocumentIngestor()
        docs = ingestor.ingest(file_path)
        
        vs_manager = VectorStoreManager()
        vs_manager.create_or_update_index(docs)
        
        os.remove(file_path)
        
        return {
            "status": "success", 
            "filename": file.filename, 
            "chunks_created": len(docs)
        }
    
    except Exception as e:
        print(f" Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Sends the user message to the LangGraph agent with memory configuration.
    """
    try:

        config = {"configurable": {"thread_id": request.thread_id}}
        
        inputs = {"messages": [("user", request.message)]}   
        
        result = agent_graph.invoke(inputs, config=config)
        
        ai_response = result["messages"][-1].content
        
        return {
            "response": ai_response,
            "thread_id": request.thread_id 
        }
    
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    