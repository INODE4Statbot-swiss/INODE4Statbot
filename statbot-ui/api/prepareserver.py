import nltk
nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("averaged_perceptron_tagger")
    
import sqlite3

logdb = sqlite3.connect("userdata/backendlog.db")
crcurs = logdb.cursor()
crcurs.execute("create table if not exists intentlog(query,method,response,user,time);")
crcurs.execute("create table if not exists translatelog(query_id,query,selected_table,system,processing_time,token_count,sql_response,explanation_response,user,time);")
crcurs.execute("create table if not exists intentfeedback(query,method,value,correct,user,time);")
crcurs.execute("create table if not exists intentcorrections(query,value,user,time);")
crcurs.execute("create table if not exists translatefeedback(query_id,query,selected_table,system,value,correct,user,time);")
crcurs.execute("create table if not exists translatecorrections(query_id,query,selected_table,system,value,user,time);")
logdb.commit()
crcurs.close()
logdb.close()
userdb = sqlite3.connect("userdata/users.db")
crcurs = userdb.cursor()
crcurs.execute("create table if not exists users(name,password);")
crcurs.execute("create table if not exists whitelist(name);")
res = crcurs.execute("select name from whitelist where name = 'admin'")
if not res.fetchall():
    crcurs.execute("insert into whitelist values ('admin');")
userdb.commit()
crcurs.close()
userdb.close()