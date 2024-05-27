
general_prompt='''if there is "switzerland" in the question, put "country=True" from the "spatial_unit" table in WHERE clause.
if there is  "canton" in the question, put "canton=True" from the "spatial_unit" table in WHERE clause.
if there is  "city" in the question, put "municipal=True" from the "spatial_unit" table in WHERE clause.
If the query does not specify either a city or a canton, put "municipal=True or canton=True" from the "spatial_unit" table in WHERE clause.
'''
def prompt_template_baby_names(db_schema):

    prompt = f'''You are an assistant that is an expert in generating SQL queries. Having the access to database content, generate a correct SQL query for the given question.
    For counting use sum(amount) every time.
    {general_prompt}

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the WHERE, ORDER BY and LIMIT commands which depends on the question.

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
    
    Only use the tables listed in the Database content below.

    ### Database content ###:\n\n{db_schema}
    '''
    
    return prompt

def prompt_template_stock_vehicles(db_schema):
    prompt = f'''You are an assistant that is an expert in generating SQL queries. Having the access to database content, generate a correct SQL query for the given question.
    For counting use sum(amount) every time.
    {general_prompt}

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the WHERE, ORDER BY and LIMIT commands which depends on the question.

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

    Only use the tables listed in the Database content below.

    ### Database content ###:\n\\n{db_schema}
    '''
    
    return prompt

def prompt_template_marriage_citizenship(db_schema):
    prompt = f'''You are an assistant that is an expert in generating SQL queries. Having the access to database content, generate a correct SQL query for the given question.
    For counting use sum(amount) every time.
    {general_prompt}
    Always exclude 'Citizenship of wife - total' and 'Citizenship of husband - total' from counting.
  
    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the WHERE, ORDER BY and LIMIT commands which depends on the question.


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

    Only use the tables listed in the Database content below.

    ### Database content ###:\n\n{db_schema}
    '''
   
    return prompt

def prompt_template_resident_population_birthplace_citizenship_type(db_schema):
    prompt = f'''You are an assistant that is an expert in generating SQL queries. Having the access to database content, generate a correct SQL query for the given question.
    For counting use sum(amount) every time. 
    {general_prompt}
    Use country names for citizenship.
    

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the WHERE, ORDER BY and LIMIT commands which depends on the question.
            
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
    
    Only use the tables listed in the Database content below.

    ### Database content ###:\n\n{db_schema}
    '''
   
    return prompt

def prompt_template_divorces_duration_of_marriage_citizenship_categories(db_schema):
    prompt = f'''You are an assistant that is an expert in generating SQL queries. Having the access to database content, generate a correct SQL query for the given question.
    For counting use sum(amount) every time. 
    {general_prompt}
    Use country names for citizenship.

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the WHERE, ORDER BY and LIMIT commands which depends on the question.

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

    Only use the tables listed in the Database content below.

    ### Database content ###:\n\n{db_schema}
    '''
    
    return prompt

def prompt_template_divorces_duration_of_marriage_age_classes(db_schema):
    prompt = f'''You are an assistant that is an expert in generating SQL queries. Having the access to database content, generate a correct SQL query for the given question.
    For counting use sum(amount) every time. 
    {general_prompt}
    Use country names for citizenship.

    Please include the following examples for better understanding. 
    Stick to the format of the answer as shown in the Examples below, except for the WHERE, ORDER BY and LIMIT commands which depends on the question.

    [Examples]:

    [Q]: Which Kanton had the most divorces after only a very long marriage in 2016?
    [SQL]: SELECT S.name, T.duration_of_marriage, SUM(T.amount) AS total_divorces 
    FROM spatial_unit AS S INNER JOIN divorces_duration_of_marriage_age_classes AS T ON S.spatialunit_uid = T.spatialunit_uid 
    WHERE T.year = 2016 AND T.duration_of_marriage='20 years or more' AND T.age_class_husband='Age class of husband - total' AND T.age_class_wife='Age class of wife - total' AND S.canton 
    GROUP BY S.name, T.duration_of_marriage 
    ORDER BY total_divorces D
    ESC LIMIT 1

    Only use the tables listed in the Database content below.

    ### Database content ###:\n\n{db_schema}
    '''
   
    return prompt

def zero_shot_prompt_template(db_schema):
    prompt = f'''You are an assistant that is an expert in generating SQL queries. Having the access to database content, generate a correct SQL query for the given question.
    Translate the question into the language of the database content when the languages of the question and the database content differ.
    For counting use sum(amount) every time. 
    {general_prompt}
    Use country names for citizenship.
    Only use the tables listed in the Database content below.

    ### Database content ###:\n\n{db_schema}
    '''
   
    return prompt

'''
To translate a question to an SQL query, you can follow these steps:

Identify the key elements of the question:
Try to break down the question into its essential components, such as the tables involved, the relationships between them, and the action or operation being performed.
Example: If the question is "What is the total cost of all products sold by a particular seller on an e-commerce platform?", the key elements are the tables involved (products, sellers), the relationship between them (a seller can sell multiple products), and the action or operation being performed (calculating the total cost).
Determine the appropriate SQL query syntax:
Depending on the database management system (DBMS) you are using, there may be different syntax for writing SQL queries. However, most SQL queries follow a similar structure: SELECT statements to retrieve data, FROM clauses to specify the tables involved, WHERE clauses to filter data based on conditions, and ORDER BY clauses to sort data.
Example (MySQL): "SELECT SUM(cost) FROM products WHERE seller_id = 10;".
Use logical operators and conditions:
Logical operators such as AND, OR, and NOT can be used to build complex conditions in your SQL query. These operators allow you to combine multiple conditions to filter or manipulate data.
Example: "SELECT * FROM products WHERE (price > 100 AND seller_id = 10) OR (inventory > 100);".
Use aggregation functions:
Aggregation functions such as COUNT, SUM, AVG, and MIN/MAX can be used to perform calculations on large datasets. These functions can help you summarize and analyze data in your SQL query.
Example: "SELECT AVG(price) FROM products WHERE seller_id = 10;".
Optimize your query:
Depending on the complexity of your query, there may be ways to optimize it for better performance. This can involve things like indexing columns, using subqueries instead of joins, or rearranging the order of conditions.
Example: "SELECT * FROM products ORDER BY seller_id, price;".
By following these steps, you can translate a question into a well-formulated SQL query that retrieves the desired data from a database
'''


'''
However, here is a general guide to help you translate a question into an SQL query:

Understand the Question:

Read the question carefully to understand what information is being requested. Identify the key components of the question, such as the tables involved, conditions, and the desired output.
Identify the Tables:

Determine which database tables contain the relevant data for answering the question. You'll need to know the names of these tables.
Select the Columns:

Identify the columns (attributes) from the tables that are needed to answer the question. These columns will appear in the SELECT clause of your SQL query.
Define Filters (WHERE Clause):

Determine any conditions or filters that need to be applied to the data. These conditions should be specified in the WHERE clause of your SQL query. Use operators like =, <, >, LIKE, AND, OR, etc., as needed.
Determine Sorting (ORDER BY Clause):

Decide if the results should be sorted in a particular order. If so, specify the sorting criteria in the ORDER BY clause of your SQL query. You can sort in ascending (ASC) or descending (DESC) order.
Grouping and Aggregation (GROUP BY and HAVING Clauses, if needed):

If the question involves aggregation functions like COUNT, SUM, AVG, etc., or requires grouping data by certain columns, use the GROUP BY clause. Additionally, if you want to filter aggregated results, you can use the HAVING clause.
Joining Tables (if multiple tables are involved):

If the question involves data from multiple tables, you'll likely need to perform JOIN operations to combine them. Use JOIN, LEFT JOIN, RIGHT JOIN, or INNER JOIN clauses to connect tables based on common keys.
Write the SQL Query:

Now that you've gathered all the necessary information, write the SQL query. Start with the SELECT clause, followed by the FROM clause (specifying the tables), then add the WHERE clause (if needed), GROUP BY (if needed), HAVING (if needed), and finally, the ORDER BY clause.
'''

'''
Question: Start by presenting the question you want to translate into an SQL query. Be as specific and clear as possible about what information you need from the database.

Context (if applicable): Provide any necessary context or information about the database schema, relevant tables, and columns. This helps ChatGPT understand the data source.

Desired Output: Explain what you want the SQL query to retrieve or accomplish. This helps clarify the goal of the query.

Additional Instructions (if needed): If there are specific conditions, sorting requirements, or other constraints, specify them here. You can also specify the database system you're using (e.g., MySQL, PostgreSQL, SQLite) if it's relevant.

Here's an example instruction:

"
Question: Retrieve the names and ages of all customers who made a purchase in the last month from the "Customers" and "Orders" tables.

Context: The database contains two tables, "Customers" and "Orders." The "Customers" table has columns: CustomerID, FirstName, LastName, and Age. The "Orders" table has columns: OrderID, CustomerID, OrderDate.

Desired Output: I want to see a list of customer names and ages for those who made a purchase in the last month.

Additional Instructions: Please use SQL syntax compatible with PostgreSQL.
"
By providing a clear question, context, desired output, and any additional instructions, you help ChatGPT generate a more accurate SQL query tailored to your specific needs. This structured approach improves the chances of getting a relevant and correct SQL query as a response, whether you're using llam2 or any other AI model.

'''

'''
I have some texts along with their corresponding scores. The texts are arranged in ascending order
based on their scores, where higher scores indicate better quality.

text:
"To translate a question to an SQL query, you can follow these steps:
Identify the key elements of the question:
Try to break down the question into its essential components, such as the tables involved, the relationships between them, and the action or operation being performed.
Example: If the question is "What is the total cost of all products sold by a particular seller on an e-commerce platform?", the key elements are the tables involved (products, sellers), the relationship between them (a seller can sell multiple products), and the action or operation being performed (calculating the total cost).
Determine the appropriate SQL query syntax:
Depending on the database management system (DBMS) you are using, there may be different syntax for writing SQL queries. However, most SQL queries follow a similar structure: SELECT statements to retrieve data, FROM clauses to specify the tables involved, WHERE clauses to filter data based on conditions, and ORDER BY clauses to sort data.
Example (MySQL): "SELECT SUM(cost) FROM products WHERE seller_id = 10;".
Use logical operators and conditions:
Logical operators such as AND, OR, and NOT can be used to build complex conditions in your SQL query. These operators allow you to combine multiple conditions to filter or manipulate data.
Example: "SELECT * FROM products WHERE (price > 100 AND seller_id = 10) OR (inventory > 100);".
Use aggregation functions:
Aggregation functions such as COUNT, SUM, AVG, and MIN/MAX can be used to perform calculations on large datasets. These functions can help you summarize and analyze data in your SQL query.
Example: "SELECT AVG(price) FROM products WHERE seller_id = 10;".
Optimize your query:
Depending on the complexity of your query, there may be ways to optimize it for better performance. This can involve things like indexing columns, using subqueries instead of joins, or rearranging the order of conditions.
Example: "SELECT * FROM products ORDER BY seller_id, price;".
By following these steps, you can translate a question into a well-formulated SQL query that retrieves the desired data from a database"

score:
73

text:
"To translate a question to an SQL query, you can follow these steps,
Here is a general guide to help you translate a question into an SQL query:
-Understand the Question:
Read the question carefully to understand what information is being requested. Identify the key components of the question, such as the tables involved, conditions, and the desired output.
-Identify the Tables:
Determine which database tables contain the relevant data for answering the question. You'll need to know the names of these tables.
-Select the Columns:
Identify the columns (attributes) from the tables that are needed to answer the question. These columns will appear in the SELECT clause of your SQL query.
-Define Filters (WHERE Clause):
Determine any conditions or filters that need to be applied to the data. These conditions should be specified in the WHERE clause of your SQL query. Use operators like =, <, >, LIKE, AND, OR, etc., as needed.
-Determine Sorting (ORDER BY Clause):
Decide if the results should be sorted in a particular order. If so, specify the sorting criteria in the ORDER BY clause of your SQL query. You can sort in ascending (ASC) or descending (DESC) order.
-Grouping and Aggregation (GROUP BY and HAVING Clauses, if needed):
If the question involves aggregation functions like COUNT, SUM, AVG, etc., or requires grouping data by certain columns, use the GROUP BY clause. Additionally, if you want to filter aggregated results, you can use the HAVING clause.
-Joining Tables (if multiple tables are involved):
If the question involves data from multiple tables, you'll likely need to perform JOIN operations to combine them. Use JOIN, LEFT JOIN, RIGHT JOIN, or INNER JOIN clauses to connect tables based on common keys.
-Write the SQL Query:
Now that you've gathered all the necessary information, write the SQL query. Start with the SELECT clause, followed by the FROM clause (specifying the tables), then add the WHERE clause (if needed), GROUP BY (if needed), HAVING (if needed), and finally, the ORDER BY clause."

score:
80

The following exemplar show how to apply your text: you need to generate another instruction and replace <INSTRUCTION> in each input with your
text, then read the input and give an output. We say your output is wrong if your output is different
from the given output, and we say your output is correct if they are the same.

input:
Q:What were the most commonly given first names to baby girls in canton bern in the year 2010?

A: <INSTRUCTION>

ouput:SELECT bnff.first_name, bnff.amount
        FROM baby_names_favorite_firstname as bnff JOIN spatial_unit as su ON bnff.spatialunit_uid = su.spatialunit_uid
        WHERE su.canton = True and bnff.year=2010 and su.name ilike '%bern' and bnff.gender='girl'
        ORDER BY bnff.amount DESC
        LIMIT 100;


        
Write your new text that is different from the old ones and has a score as high as possible. Write the
text in square brackets.
'''