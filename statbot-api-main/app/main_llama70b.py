from fastapi import FastAPI

import csv, os, re
from tqdm import tqdm

import json
import pandas as pd
import uvicorn
from pydantic import BaseModel
from typing import Union
from utility import *
from sqlalchemyWrapper import schema_db_postgres_statbot_zhaw
import time
from text_generation import Client
from transformers import AutoTokenizer


hf_auth='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'
# model_config=AutoConfig.from_pretrained(model_name,use_auth_token=hf_token)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-70b-chat-hf", use_auth_token=hf_auth)


app = FastAPI()

client = Client("https://dgxnoor.cloudlab.zhaw.ch")


class QueryItem(BaseModel):
    id: Union [int, None] = None
    question: str
    

@app.put("/statbot-api/{db_id}")
async def read_query(db_id, query:QueryItem):
    
    ### change the dummy function to the function we need
    
    return await call_llama(db_id, query)


async def call_llama(db_id, query:QueryItem):
    tic = time.perf_counter()
    print (db_id, query)
    
    '''
    curl dgx-a100.cloudlab.zhaw.ch:9175/generate \                     
    -X POST \
    -d '{"inputs":"What is Deep Learning?","parameters":{"max_new_tokens":20}}' \
    -H 'Content-Type: application/json'
    '''
    
    ###
    table_name=db_id
    db_schema = schema_db_postgres_statbot_zhaw(include_tables=[table_name,'spatial_unit'], sample_number=5)

    system_prompt = find_template(table_name,db_schema)
    chat_history=[]
    input_nl2sql = get_prompt(query.question, chat_history=chat_history, system_prompt=system_prompt)
    length = get_input_token_length(tokenizer,query.question, chat_history=chat_history, system_prompt=system_prompt)

    text = ""
    for response in client.generate_stream(input_nl2sql, max_new_tokens=500,  do_sample=False ):
        if not response.token.special:
            text += response.token.text
    sql=extractSQLpart(text)
    sql= sql if sql.upper().startswith("SELECT") else "SELECT " + sql
    
    toc = time.perf_counter()
    process_time=toc-tic
    print(f"Process Time= {process_time:0.4f} second")

    return {"message": {
        "db_id": db_id,
        "id":query.id,
        "generated_query": sql,
        "full_output": text,
        "question": query.question,
         "time":process_time,
        "num_tokens":length,
       "prompt":input_nl2sql
    }}

if __name__ == '__main__':
    uvicorn.run(app, port=8001, host='0.0.0.0')