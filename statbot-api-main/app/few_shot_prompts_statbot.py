from langchain import PromptTemplate


def few_shot_template_baby_names():

    prompt = '''
    This is a task converting text into SQL statement.
    We will first given the dataset schema and then ask a question in text. 
    You are asked to generate SQL statement.
    For counting use sum(amount) every time.

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the ORDER BY and LIMIT commands which depends on the question.

    [Examples]:

    [Q]: What were the most commonly given first names to baby girls in canton bern in the year 2010?
    [SQL]: SELECT bnff.first_name, bnff.amount
            FROM baby_names_favorite_firstname as bnff JOIN spatial_unit as su ON bnff.spatialunit_uid = su.spatialunit_uid
            WHERE su.canton = True and bnff.year=2010 and su.name ilike '%bern' and bnff.gender='girl'
            ORDER BY bnff.amount DESC
            LIMIT 100

    [Q]: What are the most commonly given first names to baby boy in zurich for each year?
    [SQL]:  SELECT bnff.first_name,bnff.year, sum(bnff.amount)
            FROM baby_names_favorite_firstname AS bnff
            JOIN spatial_unit AS su ON bnff.spatialunit_uid = su.spatialunit_uid
            WHERE su.name ilike '%zurich'
            AND bnff.gender='girl'
            Group BY bnff.first_name,bnff.year, bnff.amount
            ORDER BY bnff.amount DESC
            LIMIT 10
    
    [Q]: Show me all top-1 ranked boy names for in each canton in year 2014.
    [SQL]: SELECT bnff.first_name, su.name
            FROM baby_names_favorite_firstname as bnff
            JOIN spatial_unit as su ON bnff.spatialunit_uid = su.spatialunit_uid
            WHERE su.canton = True and bnff.gender = 'boy' and bnff.year = 2014 and bnff.rank = 1;

    [Q]: Show me all amount of baby names in all municipalities.
    [SQL]: SELECT bnff.first_name, bnff.gender, su.spatialunit_ontology, sum(bnff.amount)
            FROM baby_names_favorite_firstname as bnff
            JOIN spatial_unit as su ON bnff.spatialunit_uid = su.spatialunit_uid
            WHERE su.municipal = True
            Group by bnff.first_name, bnnf.gender, su.spatialunit_ontology
    
    Only use the tables listed in the Database Schema information.

    [Database Schema]:\n{table_info}
    [Q]: {input}
    [SQL]: 
    '''
    few_shot_prompt_template = PromptTemplate(
        input_variables=["input", "table_info"],
        template=prompt,
    )
    return few_shot_prompt_template

def few_shot_template_stock_vehicles():
    prompt = '''
    This is a task converting text into SQL statement.
    We will first given the dataset schema and then ask a question in text. 
    You are asked to generate SQL statement.
    For counting use sum(amount) every time.

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the ORDER BY and LIMIT commands which depends on the question.

    [Examples]:

    [Q]: What type of vehicle is the most frequent in the canton of Basel?
    [SQL]: SELECT  vehicle_type, SUM(amount) AS total_amount 
        FROM spatial_unit su INNER JOIN stock_vehicles sv ON su.spatialunit_uid = sv.spatialunit_uid
        WHERE su.canton = true AND su.name ILIKE '%basel%'
        GROUP BY vehicle_type
        ORDER BY   total_amount DESC
        LIMIT 5

    [Q]: Give me the total number of passenger cars that are using diesel in each canton?
    [SQL]: SELECT S.name, S.spatialunit_ontology, T.fuel_type, sum(T.amount) as amount from stock_vehicles as T
            JOIN spatial_unit as S on T.spatialunit_uid = S.spatialunit_uid
            WHERE  S.canton=True and T.fuel_type ilike '%diesel%' and T.vehicle_type ='passenger_cars'
            GROUP BY S.spatialunit_ontology, S.name,T.fuel_type

    [Q]: Show me the number of hybrid cars in the city of basel on 2017?
    [SQL]: SELECT S.name, S.spatialunit_ontology,T.fuel_type, sum(T.amount) as amount from stock_vehicles as T
            JOIN spatial_unit as S on T.spatialunit_uid = S.spatialunit_uid
            WHERE S.name ilike '%basel'  and S.municipal=True and T.fuel_type ilike '%hybrid%' and T.year=2017
            GROUP BY S.spatialunit_ontology, S.name,T.fuel_type
    
    [Q]: How many vehicles do we have in city of zurich in 2013?
    [SQL]: SELECT S.name, sum(T.amount) as amount from stock_vehicles as T
            JOIN spatial_unit as S on T.spatialunit_uid = S.spatialunit_uid
            WHERE S.name ilike '%Z_rich'  and T.year=2020 and S.municipal=True
            GROUP BY S.name

    Only use the tables listed in the Database Schema information.

    [Database Schema]:\n{table_info}
    [Q]: {input}
    [SQL]: 
    '''
    few_shot_prompt_template = PromptTemplate(
        input_variables=["input", "table_info"],
        template=prompt,
    )
    return few_shot_prompt_template

def few_shot_template_marriage_citizenship():
    prompt = '''
    This is a task converting text into SQL statement.
    We will first given the dataset schema and then ask a question in text. 
    You are asked to generate SQL statement.
    For counting use sum(amount) every time.
    Always exclude 'Citizenship of wife - total' and 'Citizenship of husband - total' from counting.
    
    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the ORDER BY and LIMIT commands which depends on the question.


    [Examples]:

    [Q]: Which five cantons have the highest number of marriages between Swiss men and foreign women on 2011?
    [SQL]: SELECT T2.name, T1.citizenship_category_husband , T1.citizenship_category_wife, T1.amount 
        FROM marriage_citizenship as T1 JOIN spatial_unit T2 on T1.spatialunit_uid = T2.spatialunit_uid 
        WHERE T2.canton=True AND T1.year=2011 AND T1.citizenship_category_husband ='Switzerland' and T1.citizenship_category_wife ='Foreign country' 
        ORDER BY T1.amount DESC LIMIT 5

    [Q]: How many marriages occurred in Reiden in 1999 with a wife who held Swiss citizenship?
    [SQL]: SELECT T1.citizenship_category_wife, T1.citizenship_category_husband,  T2.name,T1.year, T1.amount 
        FROM marriage_citizenship as T1 JOIN spatial_unit T2 on T1.spatialunit_uid = T2.spatialunit_uid 
        WHERE T2.name ilike '%Reiden%' and T1.year= 1999 and T1.citizenship_category_wife='Switzerland' and T1.citizenship_category_husband = 'Citizenship of husband - total'

    [Q]: How many marriages occurred in switzerland in the year 2010? Give me based on nationalities?
    [SQL]: SELECT T2.name,T1.citizenship_category_wife,T1.citizenship_category_husband,T1.year, T1.amount 
        FROM marriage_citizenship as T1 JOIN spatial_unit T2 on T1.spatialunit_uid = T2.spatialunit_uid 
        WHERE T2.country=True and T1.year=2010 and T1.citizenship_category_wife !='Citizenship of wife - total' and T1.citizenship_category_husband !='Citizenship of husband - total'

    [Q]: Give me the 5 highest numbers of marriages that occurred at the canton level in 2010, where both the wife and husband were citizens of foreign countries?
    [SQL]: SELECT T2.name, T1.amount 
        FROM marriage_citizenship as T1 
        JOIN spatial_unit T2 on T1.spatialunit_uid = T2.spatialunit_uid 
        WHERE T2.canton = True AND T1.year = 2010 AND T1.citizenship_category_husband = 'Foreign country' AND T1.citizenship_category_wife ='Foreign country' ORDER BY T1.amount DESC LIMIT 5

    Only use the tables listed in the Database Schema information.

    [Database Schema]:\n{table_info}
    [Q]: {input}
    [SQL]: 
    '''

    few_shot_prompt_template = PromptTemplate(
        input_variables=["input", "table_info"],
        template=prompt,
    )
    return few_shot_prompt_template

def few_shot_template_resident_population_birthplace_citizenship_type():
    prompt = '''
    This is a task converting text into SQL statement.
    We will first given the dataset schema and then ask a question in text. 
    You are asked to generate SQL statement.
    For counting use sum(amount) every time. Use country names for citizenship.

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the ORDER BY and LIMIT commands which depends on the question.
            
    [Examples]:

    [Q]: How many of Swiss residence were born within the country and had Turkish Citizenship on 2018?
    [SQL]: SELECT T1.year, T1.population_type, T1.place_of_birth, T1.citizenship, T1.amount 
        from resident_population_birthplace_citizenship_type AS T1 JOIN spatial_unit AS T2 ON T1.spatialunit_uid = T2.spatialunit_uid 
        WHERE T2.country=True AND T1.year=2018 AND T1.place_of_birth ='Switzerland' AND T1.citizenship ilike '%Turky%'

    [Q]: How many of the permanent population of Switzerland have been born Aborad on the year of 2020?
    [SQL]: SELECT T1.year, T1.population_type,T1.place_of_birth,T1.citizenship, T1.amount 
        from resident_population_birthplace_citizenship_type AS T1 JOIN spatial_unit AS T2 ON T1.spatialunit_uid = T2.spatialunit_uid 
        WHERE T2.country=True AND T1.year=2020 AND T1.population_type ='Permanent resident population' AND T1.place_of_birth ='Abroad' AND T1.citizenship='Citizenship - total'

    [Q]: How many of the people were born abroad in municipality level had the permanent residenship on 2010?
    [SQL]: SELECT T1.year, T2.spatialunit_ontology, T2.name, T1.population_type,T1.place_of_birth, T1.amount 
        from resident_population_birthplace_citizenship_type AS T1 
        JOIN spatial_unit AS T2 ON T1.spatialunit_uid = T2.spatialunit_uid 
        WHERE T2.municipal=True AND T1.year=2010 AND T1.population_type ='Permanent resident population' AND T1.place_of_birth ='Abroad' AND T1.citizenship='Citizenship - total'
   
    [Q]:  How many individuals born abroad in canton zurich hold citizenship from Brazil? 
    [SQL]: SELECT T2.name, T1.place_of_birth, T1.citizenship, Sum(T1.amount) 
        from resident_population_birthplace_citizenship_type AS T1 
        JOIN spatial_unit AS T2 ON T1.spatialunit_uid = T2.spatialunit_uid 
        WHERE T2.canton=True AND T2.name ilike '%Z_rich%' AND T1.place_of_birth ='Abroad' AND T1.citizenship ilike '%Brazil%' GROUP BY T2.name, T1.place_of_birth, T1.citizenship
    
    Only use the tables listed in the Database Schema information.

    [Database Schema]:\n{table_info}
    [Q]: {input}
    [SQL]: 
    '''
    few_shot_prompt_template = PromptTemplate(
        input_variables=["input", "table_info"],
        template=prompt,
    )
    return few_shot_prompt_template

def few_shot_template_divorces_duration_of_marriage_citizenship_categories():
    prompt = '''
    This is a task converting text into SQL statement.
    We will first given the dataset schema and then ask a question in text. 
    You are asked to generate SQL statement.
    For counting use sum(amount) every time. Use country names for citizenship.

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the ORDER BY and LIMIT commands which depends on the question.
            


    [Examples]:

    [Q]: In 1995, which municipality had the highest number of divorces between Swiss couples who were married for 10-14 years?
    [SQL]: SELECT su.name, SUM(amount) AS total_divorces 
        FROM divorces_duration_of_marriage_citizenship_categories d JOIN spatial_unit su ON d.spatialunit_uid = su.spatialunit_uid 
        WHERE duration_of_marriage = '10-14 years' AND year = 1995 AND su.municipal = True AND citizenship_category_husband = 'Switzerland' AND citizenship_category_wife = 'Switzerland' 
        GROUP BY su.name ORDER BY total_divorces DESC LIMIT 1

    [Q]: What are the top 5 cantons with the highest number of divorces in 1994 for Swiss couples?
    [SQL]: SELECT su.name, SUM(div.amount) as total 
        FROM divorces_duration_of_marriage_citizenship_categories div JOIN spatial_unit su on div.spatialunit_uid = su.spatialunit_uid 
        WHERE div.year = 1994 AND div.duration_of_marriage = 'Duration of marriage - total' AND div.citizenship_category_husband = 'Switzerland' AND div.citizenship_category_wife = 'Switzerland' AND su.Canton = True 
        GROUP BY su.name ORDER BY total DESC LIMIT 5

    [Q]: Which municipality had the highest number of divorces in 1995 between Swiss couples?
    [SQL]: SELECT su.name, d.year, SUM(d.amount) as total_divorces 
        FROM divorces_duration_of_marriage_citizenship_categories d 
        JOIN spatial_unit su ON d.spatialunit_uid = su.spatialunit_uid 
        WHERE d.year = 1995 AND su.municipal = True AND d.duration_of_marriage = 'Duration of marriage - total' AND d.citizenship_category_husband = 'Switzerland' AND d.citizenship_category_wife = 'Switzerland' 
        GROUP BY su.name, d.year ORDER BY total_divorces DESC LIMIT 1

    Only use the tables listed in the Database Schema information.

    [Database Schema]:\n{table_info}
    [Q]: {input}
    [SQL]: 
    '''
    few_shot_prompt_template = PromptTemplate(
        input_variables=["input", "table_info"],
        template=prompt,
    )
    return few_shot_prompt_template

def few_shot_template_divorces_duration_of_marriage_age_classes():
    prompt = '''
    This is a task converting text into SQL statement.
    We will first given the dataset schema and then ask a question in text. 
    You are asked to generate SQL statement.
    For counting use sum(amount) every time. Use country names for citizenship.

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the ORDER BY and LIMIT commands which depends on the question.

    [Examples]:

    [Q]: Which Kanton had the most divorces after only a very long marriage in 2016?
    [SQL]: SELECT S.name, T.duration_of_marriage, SUM(T.amount) AS total_divorces 
    FROM spatial_unit AS S INNER JOIN divorces_duration_of_marriage_age_classes AS T ON S.spatialunit_uid = T.spatialunit_uid 
    WHERE T.year = 2016 AND T.duration_of_marriage='20 years or more' AND T.age_class_husband='Age class of husband - total' AND T.age_class_wife='Age class of wife - total' AND S.canton 
    GROUP BY S.name, T.duration_of_marriage 
    ORDER BY total_divorces D
    ESC LIMIT 1

    Only use the tables listed in the Database Schema information.

    [Database Schema]:\n{table_info}
    [Q]: {input}
    [SQL]: 
    '''
    few_shot_prompt_template = PromptTemplate(
        input_variables=["input", "table_info"],
        template=prompt,
    )
    return few_shot_prompt_template

def zero_shot_template():
    prompt = '''
    This is a task converting text into SQL statement.
    We will first given the dataset schema and then ask a question in text. 
    Translate the question into the language of the database schema when the languages of the question and the database schema differ.
    You are asked to generate SQL statement.
    For counting use sum(amount) every time.

    [Database Schema]:\n{table_info}
    [Q]: {input}
    [SQL]: 
    '''
    zero_shot_prompt_template = PromptTemplate(
        input_variables=["input", "table_info"],
        template=prompt,
    )
    return zero_shot_prompt_template
