import csv, os, re
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig, BitsAndBytesConfig
import json
import pandas as pd
from sqlalchemyWrapper import schema_db_postgres_statbot_zhaw
from torch import cuda, bfloat16
import time
from utility import *




def llama_model_call(question, table_name, model,tokenizer):
   
    #db_schema = get_schema_info_prostgres(db_info=DB_INFO, include_tables=['spatial_unit', table_name], sample_number=0)
    db_schema = schema_db_postgres_statbot_zhaw(include_tables=[table_name,'spatial_unit'], sample_number=5)

    system_prompt = find_template(table_name,db_schema)

    ###
    params={
            # "top_k":5,
            #"temperature":0.01,
            "do_sample":False,
            "num_return_sequences":1,
            "top_p":1.0,
            "max_new_tokens":1000,
            "repetition_penalty":1.1,
            "eos_token_id":tokenizer.eos_token_id,
            }

    tic = time.perf_counter()
    chat_history=[]
    input_nl2sql = get_prompt( question, chat_history=chat_history, system_prompt=system_prompt)
    length = get_input_token_length(tokenizer,question, chat_history=chat_history, system_prompt=system_prompt)
    
    print('###################### First Generation ####################################')

    #res = generate_text2text(input_nl2sql)
    input_ids = tokenizer(input_nl2sql, return_tensors="pt").input_ids
    input_ids = input_ids.to('cuda')
    generated_ids = model.generate(input_ids,**params)
    llam_output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    print(llam_output)
    
    llam_output = llam_output.split('[/INST]')[-1]
   
    ## time ###
    toc = time.perf_counter()
    
    process_time=toc-tic
    print(f"Process Time= {process_time:0.4f} second")
     ## time ###
    SQL=f'SELECT {extractSQLpart(llam_output)}'

    print(f"Generated SQL: {SQL}")
    r = {
        "question": question,
        "db_id": table_name,
        "time":process_time,
        "num_tokens":length,
        "generated_query": SQL.replace("\n", " ").replace("\n\n", " ").replace(" ", " ").replace("  ", " "),
        "full_output": llam_output,
        "prompt":input_nl2sql,
    }
    return r




# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#    open_ai_call(question="Give me the babay names in canton zurich 0n 2020",table_name="baby_names_favorite_firstname")

