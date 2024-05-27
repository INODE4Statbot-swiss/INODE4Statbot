from fastapi import FastAPI
import torch
from torch import cuda, bfloat16

import csv, os, re
from tqdm import tqdm
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig, BitsAndBytesConfig
import json
import pandas as pd
import uvicorn
from pydantic import BaseModel
from typing import Union
from llama_call import  llama_model_call
from torch import cuda, bfloat16
import time

app = FastAPI()

tic = time.perf_counter()
print("GPU:",torch.cuda.is_available())
device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

# 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
model_name = "meta-llama/Llama-2-7b-chat-hf" # <-- You can switch to other models like "NumbersStation/nsql-6B" # nsql-llama-2-7B
version = model_name.split("/")[-1]

# set quantization configuration to load large model with less GPU memory
# # this requires the `bitsandbytes` library
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=bfloat16
)

hf_auth='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'
# model_config=AutoConfig.from_pretrained(model_name,use_auth_token=hf_token)
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_auth)
model_config = AutoConfig.from_pretrained(
    model_name,
    use_auth_token=hf_auth
)
max_memory = f'{40960}MB'
n_gpus = torch.cuda.device_count()
print(n_gpus)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    config=model_config,
    trust_remote_code=True,
    quantization_config=bnb_config,
    device_map='auto',
    use_auth_token=hf_auth,
    max_memory = {i: max_memory for i in range(n_gpus)},
)
model.eval()

print(f"Model loaded on {device}")
toc = time.perf_counter()
process_time=toc-tic
print(f"Process Time= {process_time:0.4f} second")


class QueryItem(BaseModel):
    id: Union [int, None] = None
    question: str
    

@app.put("/statbot-api/{db_id}")
async def read_query(db_id, query:QueryItem):
    
    ### change the dummy function to the function we need
    
    return await call_llama(db_id, query)


async def call_llama(db_id, query:QueryItem):
    
    output=llama_model_call(query.question,db_id, model, tokenizer)

    return {"message": {
        "db_id": db_id,
        "id":query.id,
        "generated_query": output["generated_query"],
        "full_output": output["full_output"],
        "question": query.question,
         "time":output["time"],
        "num_tokens":output["num_tokens"],
        "prompt":output["prompt"]
    }}

if __name__ == '__main__':

    uvicorn.run(app, port=5000, host='0.0.0.0')