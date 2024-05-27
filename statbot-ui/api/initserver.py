import os
import sqlite3

if os.path.exists("logins.db"):
    os.remove("logins.db")
logindb = sqlite3.connect("logins.db")
crcurs = logindb.cursor()
crcurs.execute("create table if not exists logins(name,time,sessionid,expires);")
logindb.commit()
crcurs.close()
logindb.close()