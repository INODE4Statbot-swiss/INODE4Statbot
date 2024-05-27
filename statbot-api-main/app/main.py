from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import Union
from gpt_call import  open_ai_call

import os
from dotenv import load_dotenv
# Load environment variables from the .env file
load_dotenv()
# Get the Hugging Face API key from environment variables

API_KEY = os.getenv('OPENAI_API_KEY')
app = FastAPI()

class QueryItem(BaseModel):
    id: Union [int, None] = None
    question: str
    

@app.put("/statbot-api/{db_id}")
async def read_query(db_id, query:QueryItem):
    
    ### change the dummy function to the function we need

    return await call_openai(db_id, query)


async def call_openai(db_id, query:QueryItem):
    
    output=open_ai_call(query.question,db_id, api_key=API_KEY)
    return {"message": {
        "db_id": db_id,
        "id":query.id,
        "generated_query": output["generated_query"],
        "prompt": output["prompt"],
        "question": query.question,
        "time":output["time"],
        "num_tokens":output["num_tokens"],
    }}

if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')