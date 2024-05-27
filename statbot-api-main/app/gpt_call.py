
import time

import os
from sqlalchemyWrapper import *
from langchain import OpenAI
from few_shot_prompts_statbot import *
from langchain import LLMChain
import tiktoken



def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def find_template(table_name):
    
    if table_name=="baby_names_favorite_firstname":
        return few_shot_template_baby_names()
    elif table_name =="divorces_duration_of_marriage_citizenship_categories":
        return few_shot_template_divorces_duration_of_marriage_citizenship_categories()
    elif table_name =="stock_vehicles":
        return few_shot_template_stock_vehicles()
    elif table_name =="divorces_duration_of_marriage_age_classes":
        return few_shot_template_divorces_duration_of_marriage_age_classes()
    elif table_name == "marriage_citizenship":
        return few_shot_template_marriage_citizenship()
    elif table_name =="resident_population_birthplace_citizenship_type":
        return few_shot_template_resident_population_birthplace_citizenship_type()
    else:
        return zero_shot_template()
    
    


def open_ai_call(question, table_name, api_key):
    os.environ["OPENAI_API_KEY"] = api_key
    prompt_template = find_template(table_name)  # divorces_duration_of_marriage_age_classes.json

    model_name = "gpt-3.5-turbo-16k"

    llm = OpenAI(temperature=0,
                 model_name= model_name,
                 n = 1,
                 stream = False,
                 max_tokens = 1500,
                 top_p = 1.0,
                 frequency_penalty=0.0,
                 presence_penalty=0.0)
    tic = time.perf_counter()
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)
    sql = None

    ddl = schema_db_postgres_statbot_zhaw(include_tables=['spatial_unit', table_name],
                             sample_number=5)
    llm_inputs = {
        "input": question,
        # "top_k": args.sample_rows,
        "table_info": ddl,
    }

    prompts = llm_chain.prep_prompts([llm_inputs])
    prompt_strings = [p.to_string() for p in prompts[0]]

    # check the length:
    # Write function to take string input and return number of tokens
    num_tokens = num_tokens_from_string(prompt_strings[0], model_name)

    print(f"Starting  generation: #input-tokens {num_tokens}")
    while sql is None:
        try:
            sql = llm_chain.run(**llm_inputs)
            print(f"Question: {question}")
            print(f"sql: {sql}")
        except Exception as e:
            print(str(e))
            time.sleep(3)
            pass
    ## time ###
    toc = time.perf_counter()
    
    process_time=toc-tic
    print(f"Process Time= {process_time:0.4f} second")
    r = {
        "question": question,
        "db_id": table_name,
        "generated_query": sql.replace("\n", " ").replace("\n\n", " ").replace(" ", " ").replace("  ", " "),
        "prompt": prompt_strings,
        "num_tokens":num_tokens,
        "time":process_time
    }
    return r




# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#    open_ai_call(question="Give me the babay names in canton zurich 0n 2020",table_name="baby_names_favorite_firstname")

