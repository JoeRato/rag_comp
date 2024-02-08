from fastapi import FastAPI
from src.rag import open_ai_acpr_rag
import os

vector_db_path = os.path.join('.','data',os.environ['VECTOR_DB'])
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/open_ai_acpr_rag")
async def open_ai_rag(question):
    reponse = open_ai_acpr_rag(vector_db_path, question)
    return {"reponse": reponse}


