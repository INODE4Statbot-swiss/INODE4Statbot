from flask import Flask,jsonify,request,Response
app = Flask(__name__)
from flask_cors import CORS
CORS(app)
import os
from dotenv import load_dotenv
import sqlparse
import sys,time
import psycopg2 as pgr
import requests
import sqlite3
import uuid
import bcrypt
from datetime import datetime,timedelta

from tableselector import tableranker


REQUIRE_FULL_LOGIN = False
REQUIRE_GPT_LOGIN = True
DUMMY_TRANSLATOR = False
DUMMY_DATABASE = False
FAKE_LOADING = False

def validsession(sessionid):
    logindb = sqlite3.connect("logins.db",detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    crcurs = logindb.cursor()
    crcurs.execute('select expires as "[timestamp]" from logins where sessionid = ?',(sessionid,))
    res = crcurs.fetchall()
    crcurs.close()
    logindb.close()
    if not res:
        return False
    return res[0][0] > datetime.now()
    
def userfromsessionid(sessionid):
    userdb = sqlite3.connect("logins.db")
    crcurs = userdb.cursor()
    crcurs.execute("select name from logins where sessionid = ?",(sessionid,))
    res = crcurs.fetchall()
    if not res:
        crcurs.close()
        userdb.close()
        return None
    crcurs.close()
    userdb.close()
    return res[0][0]

def optionsresp():
    resp = Response()
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/api/feedback",methods=["POST"])
def feedbacktable():
    if request.method == "OPTIONS":
        return optionsresp()
    feedbackdb = sqlite3.connect("userdata/backendlog.db")
    crcurs = feedbackdb.cursor()
    res = crcurs.execute("""select feedback.query,
                            feedback.selected_table,
                            feedback.system,
                            feedback.value as original_sql,
                            feedback.correct,
                            corrections.value as corrected_sql,
                            log.explanation_response as explanation,
                            log.token_count,
                            printf("%.4f",log.processing_time) as execution_time,
                            log.user
                            from translatefeedback as feedback
                            left join translatecorrections as corrections
                                on feedback.query_id=corrections.query_id
                            left join translatelog as log
                                on feedback.query_id=log.query_id""")
    res = res.fetchall()
    cols = [description[0] for description in crcurs.description]
    crcurs.close()
    feedbackdb.close()
    return jsonify({"rows":res,"colnames":cols})

@app.route("/api/admin",methods=["POST"])
def whladmin():
    if request.method == "OPTIONS":
        return optionsresp()
    adminpass,username,func = request.json.get("password",None),request.json.get("username",None),request.json.get("command",None)
    if adminpass is None or username is None or func is None:
        return "Bad request: not all parameters present",400
    if username == "admin" or username == "":
        return jsonify({"status":"ERROR","error":"FORBIDDEN"})
    userdb = sqlite3.connect("userdata/users.db")
    crcurs = userdb.cursor()
    res = crcurs.execute("select password from users where users.name = ?;",("admin",))
    res = res.fetchone()
    crcurs.close()
    userdb.close()
    if not bcrypt.checkpw(adminpass.encode("utf-8"),res[0]):
        return jsonify({"status":"ERROR","error":"INVALID_PASSWORD"})
    if func == "add":
        userdb = sqlite3.connect("userdata/users.db")
        crcurs = userdb.cursor()
        crcurs.execute("insert into whitelist values (?);",(username,))
        userdb.commit()
        crcurs.close()
        userdb.close()
        return jsonify({"status":"OK"})
    if func == "remove":
        userdb = sqlite3.connect("userdata/users.db")
        crcurs = userdb.cursor()
        crcurs.execute("delete from whitelist where name = ?;",(username,))
        userdb.commit()
        crcurs.close()
        userdb.close()
        return jsonify({"status":"OK"})
    if func == "reset":
        userdb = sqlite3.connect("userdata/users.db")
        crcurs = userdb.cursor()
        crcurs.execute("delete from users where name = ?;",(username,))
        userdb.commit()
        crcurs.close()
        userdb.close()
        return jsonify({"status":"OK"})
    return jsonify({"status":"ERROR","error":"UNKNOWN_OPERATION"})

@app.route("/api/login",methods=["POST"])
def loginreq():
    if request.method == "OPTIONS":
        return optionsresp()
    username,password = request.json.get("username",None),request.json.get("password",None)
    if not username or not password:
        return "Bad Request: Username or Password Not Present",400
    userdb = sqlite3.connect("userdata/users.db")
    crcurs = userdb.cursor()
    res = crcurs.execute("select password from users where users.name = ?;",(username,))
    res = res.fetchone()
    isinwhitelist = crcurs.execute("select name from whitelist where name = ?;",(username,))
    isinwhitelist = bool(isinwhitelist.fetchall())
    crcurs.close()
    userdb.close()
    if not res:
        return jsonify({"status":"ERROR","error":"USER_DOES_NOT_EXIST"})
    if not bcrypt.checkpw(password.encode("utf-8"),res[0]):
        return jsonify({"status":"ERROR","error":"INVALID_PASSWORD"})
    if not isinwhitelist:
        return jsonify({"status":"ERROR","error":"ACCESS_DENIED"})
    sessionid = str(uuid.uuid4())
    userdb = sqlite3.connect("logins.db")
    crcurs = userdb.cursor()
    crcurs.execute("insert into logins values (?,?,?,?);",(username,datetime.now(),sessionid,datetime.now()+timedelta(hours=1)))
    userdb.commit()
    crcurs.close()
    userdb.close()
    return jsonify({"status":"OK","sessionid":sessionid})
    
@app.route("/api/createaccount",methods=["POST"])
def createaccount():
    if request.method == "OPTIONS":
        return optionsresp()
    username,password = request.json.get("username",None),request.json.get("password",None)
    if not username or not password:
        return "Bad Request: Username or Password Not Present",400
    userdb = sqlite3.connect("userdata/users.db")
    crcurs = userdb.cursor()
    res = crcurs.execute("select password from users where users.name = ?;",(username,))
    res = res.fetchone()
    crcurs.close()
    userdb.close()
    if res:
        return jsonify({"status":"ERROR","error":"USER_ALREADY_EXISTS"})
    pwhash = bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt())
    userdb = sqlite3.connect("userdata/users.db")
    crcurs = userdb.cursor()
    crcurs.execute("insert into users values (?,?);",(username,pwhash))
    userdb.commit()
    crcurs.close()
    userdb.close()
    return jsonify({"status":"OK"})
    
@app.route("/api/logout",methods=["POST"])
def logoutreq():
    if request.method == "OPTIONS":
        return optionsresp()
    sessionid = request.json.get("sessionid",None)
    if not sessionid:
        return jsonify({"status":"OK"}) 
    username = userfromsessionid(sessionid)
    if not username:
        return jsonify({"status":"OK"}) 
    userdb = sqlite3.connect("logins.db")
    crcurs = userdb.cursor()
    crcurs.execute("delete from logins where name = ?;",(username,))
    userdb.commit()
    crcurs.close()
    userdb.close()
    return jsonify({"status":"OK"})
        
@app.route("/api/tableintent",methods=["POST"])
def tableintent():
    if request.method == "OPTIONS":
        return optionsresp()
    sessionid = request.json.get("sessionid",None)
    if REQUIRE_FULL_LOGIN and (sessionid is None or not validsession(sessionid)):
        return jsonify({"status":"ERROR","error":"INVALID_SESSION_ID"})
    qry = request.json.get("query","")
    if not qry:
        return "Bad Request: No Query Present",400
    tblrank = tableranker.rank(qry)
    tblrank = [(nm,sc/(tblrank[0][0] if tblrank[0][0] else 1.0)) for sc,nm in tblrank]
    logdb = sqlite3.connect("userdata/backendlog.db")
    curs = logdb.cursor()
    curs.execute("insert into intentlog values (?,?,?,?,?);",(qry,"basic",tblrank[0][0],userfromsessionid(sessionid),datetime.now()))
    logdb.commit()
    curs.close()
    logdb.close()
    sys.stderr.write(f"[TableSelector] Query: \"{qry}\"; Method: {'basic'}; Answer: {tblrank[0][0]}\n")
    with open("data/log.txt","a",encoding="utf-8") as fl:
        fl.write(f"[TableSelector] Query: \"{qry}\"; Method: {'basic'}; Answer: {tblrank[0][0]}\n")
    return jsonify({"status":"OK","tables":[{"name":tbl,"score":sc} for tbl,sc in tblrank]})

@app.route("/api/nltosql",methods=["POST"])
def translatequery():
    if request.method == "OPTIONS":
        return optionsresp()
    sessionid = request.json.get("sessionid",None)
    if REQUIRE_FULL_LOGIN and (sessionid is None or not validsession(sessionid)):
        return jsonify({"status":"ERROR","error":"INVALID_SESSION_ID"})
    if REQUIRE_GPT_LOGIN and request.json.get("system","") == "chatgpt" and (sessionid is None or not validsession(sessionid)):
        return jsonify({"status":"ERROR","error":"INVALID_SESSION_ID"})
    qry,tbl,sysname = request.json.get("query",""),request.json.get("table",""),request.json.get("system","")
    sys.stderr.write(f"[QueryTranslator] Query: \"{qry}\"; Table: {tbl}; System: {sysname}\n")
    if not qry:
        return "Bad Request: No Query Present",400
    if not tbl:
        return "Bad Request: No Table Present",400
    if not sysname:
        return "Bad Request: No System Name Present",400
    if sysname == "chatgpt":
        translateserver = gpttranslateserver
    elif sysname == "llama7b":
        translateserver = llama7btranslateserver
    elif sysname == "llama70b":
        translateserver = llama70btranslateserver
    else:
        return "Bad Request: Unknown System",400
    queryid = str(uuid.uuid4())
    if DUMMY_TRANSLATOR:
        if FAKE_LOADING:
            time.sleep(3)
        return jsonify({"status":"OK","sql":sqlparse.format("select * from stock_vehicles limit 100",reindent=True,keyword_case='upper'),"explanation":"blah blah\n\nijodjwodj\ndjwojdwjdowjdiejdowjedowijwoiejdowijd oiwjdowoidjwoijdoiej wiowdiwojdiowjdj\n\n\neoijdw","execution_time":1.0009,"token_count":998,"status_code":200,"message":"OK","query_id":queryid})
    try:
        r = requests.put(translateserver+tbl,headers={"Content-Type":"application/json"},json={"question":qry,"id":0})
    except Exception as e:
        sys.stderr.write(f"[QueryTranslator] CONNECTION ERROR (Query: \"{qry}\"; Table: {tbl}; System: {sysname})\n")
        return jsonify({"status":"ERROR","error":"CONNECTION_ERROR","sql":"---Error connecting to Translation Server","query_id":queryid,"explanation":"","execution_time":-1,"token_count":-1,"status_code":500,"message":str(e)})
    if r.status_code != 200:
        sys.stderr.write(f"[QueryTranslator] TRANSLATION ERROR (Query: \"{qry}\"; Table: {tbl}; System: {sysname}; Code: {r.status_code})\n")
        return jsonify({"status":"ERROR","error":"TRANSLATION_ERROR","sql":"---Error retrieving SQL translation","query_id":queryid,"explanation":"","execution_time":-1,"token_count":-1,"status_code":r.status_code,"message":r.text})
    proctime,numtokens = r.json()["message"].get("time",-1),r.json()["message"].get("num_tokens",-1)
    explanation = r.json()["message"].get("full_output","")
    logdb = sqlite3.connect("userdata/backendlog.db")
    curs = logdb.cursor()
    curs.execute("insert into translatelog values (?,?,?,?,?,?,?,?,?,?);",(queryid,qry,tbl,sysname,proctime,numtokens,r.json()["message"]["generated_query"],explanation,userfromsessionid(sessionid),datetime.now()))
    logdb.commit()
    curs.close()
    logdb.close()
    sys.stderr.write(f"[QueryTranslator] Query: \"{qry}\"; Table: {tbl}; System: {sysname}; Time: {proctime}; Tokens: {numtokens}; Result: {r.json()['message']['generated_query']}; Explanation: {explanation}\n")
    return jsonify({"status":"OK","query_id":queryid,"sql":sqlparse.format(r.json()["message"]["generated_query"],reindent=True,keyword_case='upper'),"explanation":explanation,"execution_time":proctime,"token_count":numtokens,"status_code":200,"message":"OK"})

@app.route("/api/sqlresults",methods=["POST"])
def sqlresults():
    if request.method == "OPTIONS":
        return optionsresp()
    global dbconn
    sessionid = request.json.get("sessionid",None)
    if REQUIRE_FULL_LOGIN and (sessionid is None or not validsession(sessionid)):
        return jsonify({"status":"ERROR","error":"INVALID_SESSION_ID"})
    qry = request.json.get("query","")
    sys.stderr.write(f"[SQLExecutor] Query: \"{qry}\"\n")
    if DUMMY_DATABASE:
        if FAKE_LOADING:
            time.sleep(3)
        return jsonify({"status":"OK","message":"","rows":[[*range(5)] for _ in range(20)],"columnnames":["COL_"+str(i) for i in range(5)]})
    try:
        with dbconn:
            pass
    except:
        try:
            dbconn.close()
        except:
            pass
        dbconn = pgr.connect(dbname="postgres",user="dbadmin@sdbpstatbot01",password="579fc314a8f73e881a9146901971d5b9",host="160.85.252.201",port="18001",options="-c search_path=public,experiment")
        dbconn.set_session(readonly=True)
    with dbconn:
        with dbconn.cursor() as curs:
            try:
                curs.execute(qry)
                res = [rw for rw in curs.fetchall()]
                colnames = [desc.name for desc in curs.description]
                sys.stderr.write(f"[SQLExecutor] Done.\n")
                if res and colnames:
                    return jsonify({"status":"OK","columnnames":colnames,"rows":res,"message":""})
                else:
                    return jsonify({"status":"EMPTY","columnnames":colnames,"rows":[],"message":""})
            except Exception as e:
                return jsonify({"status":"ERROR","error":"DATABASE_ERROR","columnnames":[],"rows":[],"message":f"{type(e).__name__}: {e}"})

@app.route("/api/intentfeedback",methods=["POST"])
def intentfeedback():
    if request.method == "OPTIONS":
        return optionsresp()
    sessionid = request.json.get("sessionid",None)
    if REQUIRE_FULL_LOGIN and (sessionid is None or not validsession(sessionid)):
        return jsonify({"status":"ERROR","error":"INVALID_SESSION_ID"})
    query,method,value,correct = request.json.get("query",None),request.json.get("method",None),request.json.get("value",None),request.json.get("correct",None)
    if query is None or method is None or value is None or correct is None:
        return "Bad Request: Not all parameters present",400
    correct = True if correct == "true" or correct else False
    try:
        logdb = sqlite3.connect("userdata/backendlog.db")
        curs = logdb.cursor()
        curs.execute("insert into intentfeedback values (?,?,?,?,?,?);",(query,method,value,correct,userfromsessionid(sessionid),datetime.now()))
        logdb.commit()
        curs.close()
        logdb.close()
    except Exception as e:
        sys.stderr.write(f"[IntentFeedback] Error writing to LogDB: {e}\n")
        return jsonify({"status":"ERROR","error":"LOGGING_ERROR"})
    sys.stderr.write(f"[IntentFeedback] Feedback on query \"{query}\" with method {method}: Result \"{value}\" is {'' if correct else 'in'}correct.\n")
    return jsonify({"status":"OK"})

@app.route("/api/translationfeedback",methods=["POST"])
def translationfeedback():
    if request.method == "OPTIONS":
        return optionsresp()
    sessionid = request.json.get("sessionid",None)
    if REQUIRE_FULL_LOGIN and (sessionid is None or not validsession(sessionid)):
        return jsonify({"status":"ERROR","error":"INVALID_SESSION_ID"})
    query,table,value,correct,system,queryid = request.json.get("query",None),request.json.get("table",None),request.json.get("value",None),request.json.get("correct",None),request.json.get("system",None),request.json.get("query_id",None)
    if query is None or table is None or value is None or correct is None or system is None or queryid is None:
        return "Bad Request: Not all parameters present",400
    correct = True if correct == "true" or correct else False
    try:
        logdb = sqlite3.connect("userdata/backendlog.db")
        curs = logdb.cursor()
        curs.execute("insert into translatefeedback values (?,?,?,?,?,?,?,?);",(queryid,query,table,system,value,correct,userfromsessionid(sessionid),datetime.now()))
        logdb.commit()
        curs.close()
        logdb.close()
    except Exception as e:
        sys.stderr.write(f"[TranslationFeedback] Error writing to LogDB: {e}\n")
        return jsonify({"status":"ERROR","error":"LOGGING_ERROR"})
    sys.stderr.write(f"[TranslationFeedback] Feedback on query \"{query}\" on table {table}: Result \"{value}\" is {'' if correct else 'in'}correct.\n")
    return jsonify({"status":"OK"})
        
@app.route("/api/intentcorrections",methods=["POST"])
def intentcorrections():
    if request.method == "OPTIONS":
        return optionsresp()
    sessionid = request.json.get("sessionid",None)
    if REQUIRE_FULL_LOGIN and (sessionid is None or not validsession(sessionid)):
        return jsonify({"status":"ERROR","error":"INVALID_SESSION_ID"})
    query,value = request.json.get("query",None),request.json.get("value",None)
    if query is None or value is None:
        return "Bad Request: Not all parameters present",400
    try:
        logdb = sqlite3.connect("userdata/backendlog.db")
        curs = logdb.cursor()
        curs.execute("insert into intentcorrections values (?,?,?,?);",(query,value,userfromsessionid(sessionid),datetime.now()))
        logdb.commit()
        curs.close()
        logdb.close()
    except Exception as e:
        sys.stderr.write(f"[IntentCorrections] Error writing to LogDB: {e}\n")
        return jsonify({"status":"ERROR","error":"LOGGING_ERROR"})
    sys.stderr.write(f"[IntentCorrections] Correction for intent of query \"{query}\": {value}.\n")
    return jsonify({"status":"OK"})
        
@app.route("/api/translationcorrections",methods=["POST"])
def translationcorrections():
    if request.method == "OPTIONS":
        return optionsresp()
    sessionid = request.json.get("sessionid",None)
    if REQUIRE_FULL_LOGIN and (sessionid is None or not validsession(sessionid)):
        return jsonify({"status":"ERROR","error":"INVALID_SESSION_ID"})
    query,table,value,system,queryid = request.json.get("query",None),request.json.get("table",None),request.json.get("value",None),request.json.get("system",None),request.json.get("query_id",None)
    if query is None or table is None or value is None or system is None or queryid is None:
        return "Bad Request: Not all parameters present",400
    try:
        logdb = sqlite3.connect("userdata/backendlog.db")
        curs = logdb.cursor()
        curs.execute("insert into translatecorrections values (?,?,?,?,?,?,?);",(queryid,query,table,system,value,userfromsessionid(sessionid),datetime.now()))
        logdb.commit()
        curs.close()
        logdb.close()
    except Exception as e:
        sys.stderr.write(f"[TranslationCorrections] Error writing to LogDB: {e}\n")
        return jsonify({"status":"ERROR","error":"LOGGING_ERROR"})
    sys.stderr.write(f"[TranslationCorrections] Correction for translation of query \"{query}\" on table {table}: {value}.\n")
    return jsonify({"status":"OK"})
    

load_dotenv()
gpttranslateserver = "http://"+os.getenv("GPTSERVER")+"/statbot-api/"
llama7btranslateserver = "http://"+os.getenv("LLAMA7BSERVER")+"/statbot-api/"
llama70btranslateserver = ""#"http://"+os.getenv("LLAMA70BSERVER")+"/statbot-api/"
if not DUMMY_DATABASE:
    dbconn = pgr.connect(dbname=os.getenv("DB_SCHEMA"),user=os.getenv("DB_USERNAME"),password=os.getenv("DB_PASS"),host=os.getenv("DB_HOST"),port=os.getenv("DB_PORT"),options="-c search_path="+os.getenv("DB_DATABASE"))
    dbconn.set_session(readonly=True)
else:
    dbconn = None