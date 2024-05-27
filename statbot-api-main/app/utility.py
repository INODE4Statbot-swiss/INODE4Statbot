import re
from prompts_statbot_llama import *
from sqlalchemyWrapper import schema_db_postgres

def get_prompt(message: str, chat_history: list[tuple[str, str]],
               system_prompt: str) -> str:
    texts = [f'<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n']
    # The first user input is _not_ stripped
    do_strip = False
    for user_input, response in chat_history:
        user_input = user_input.strip() if do_strip else user_input
        do_strip = True
        texts.append(f'{user_input} [/INST] {response.strip()} </s><s>[INST] ')
    message = message.strip() if do_strip else message
    texts.append(f'{message} [/INST]')
    return ''.join(texts)

def get_input_token_length(tokenizer, message: str, chat_history: list[tuple[str, str]], system_prompt: str) -> int:
    prompt = get_prompt(message, chat_history, system_prompt)
    input_ids = tokenizer([prompt], return_tensors='np', add_special_tokens=False)['input_ids']
    return input_ids.shape[-1]

def extractSQLpart(llm_output):

    #pattern = r'select(.*?)(?:;|```|$|Explanation)'
    pattern = r'(?:.*?)(SQL query|the query|way to do it|Here\'s|SQL statement|query|```|[SQL]|\s*)(.*?)\s*SELECT(.*?)(?:;|```|$|Explanation|Here\'s|This query|\n\n)'

    # Use re.search to find the match
    match = re.search(pattern, llm_output, re.DOTALL | re.IGNORECASE)

    pattern_ = r'```sql(.*?)```'

    # # Use re.search to find the match
    # match_ = re.search(pattern_, llm_output, re.DOTALL | re.IGNORECASE)

    # Check if a match is found
    if match:
        # Extract the matched string
        selected_string = match.group(3).strip()
    # else:
        # if match_:
        #     # Extract the matched string
        #     selected_string = match_.group(1).strip()+";"
    else:
        selected_string=""
        print(f"Not Found: {llm_output}")
    return selected_string

def find_template(table_name,db_schema):
    
    if table_name=="baby_names_favorite_firstname":
        return prompt_template_baby_names(db_schema)
    elif table_name =="divorces_duration_of_marriage_citizenship_categories":
        return prompt_template_divorces_duration_of_marriage_citizenship_categories(db_schema)
    elif table_name =="stock_vehicles":
        return prompt_template_stock_vehicles(db_schema)
    elif table_name =="divorces_duration_of_marriage_age_classes":
        return prompt_template_divorces_duration_of_marriage_age_classes(db_schema)
    elif table_name == "marriage_citizenship":
        return prompt_template_marriage_citizenship(db_schema)
    elif table_name =="resident_population_birthplace_citizenship_type":
        return prompt_template_resident_population_birthplace_citizenship_type(db_schema)
    else:
        return zero_shot_prompt_template(db_schema)
