import sys,os
from pathlib import Path
import csv,json
import psycopg2 as pgr
from git import Repo,rmtree
from dotenv import load_dotenv
from unidecode import unidecode
from tqdm import tqdm

from tableinfo import TableInfo,ColumnInfo

datadir = Path(__file__).parent.parent/"data"
if not datadir.exists():
    datadir.mkdir()


if __name__ == "__main__":    
    
    sys.stderr.write("Retrieving Statbot metadata...\n")
    
    try:
        load_dotenv()
        giturl = os.environ["STATBOT_REPO"]
    except:
        sys.stderr.write("\nStatbot repository not provided. Include \"STATBOT_REPO=[GitHub URL]\" in .env\n")
        exit(1)
    
    repodir = datadir/"statbotrepo"

    if os.path.exists(repodir):
        rmtree(repodir)
        
    Repo.clone_from(giturl,repodir)
    
    sys.stderr.write("Done.\n")

    sys.stderr.write("Reading metadata and queries...\n")
    
    if not os.path.exists(repodir/"pipelines"):
        sys.stderr.write("Error: could not find /pipelines in Statbot repository.\n")
        exit(0)
            
    tables = []
    for foldername in (repodir/"pipelines").glob("*"):
        if not os.path.exists(foldername/"metadata_tables.csv") or not os.path.exists(foldername/"metadata_table_columns.csv") or not os.path.exists(foldername/"queries.sql"):
            sys.stderr.write(f"Warning: incomplete metadata for table {foldername.name}. Skipping table.\n")
            continue
        with open(foldername/"metadata_tables.csv","r",encoding="utf-8") as fl:
            details = [*csv.DictReader(fl,delimiter=";")][0]
        with open(foldername/"metadata_table_columns.csv","r",encoding="utf-8") as fl:
            columns = [*csv.DictReader(fl,delimiter=";")]
        with open(foldername/"queries.sql","r",encoding="utf-8") as fl:
            queries = [ln.split("--")[1].strip() for ln in fl if ln.startswith("--")]
        tables.append(TableInfo(foldername.name,details["name"],details["language"],details.get("title",""),details.get("description",""),details.get("title_en",""),details.get("description_en"),
                                [ColumnInfo(col["data_type"],details["language"],col["name"],col.get("title",""),
                                            col.get("title_en",""),"")
                                 for col in columns],
                                queries))
    
    sys.stderr.write("Done.\n")
    
    sys.stderr.write("Retrieving values from database...\n")
    
    for k in ["DB_SCHEMA","DB_USERNAME","DB_PASS","DB_HOST","DB_PORT","DB_DATABASE"]:
        try:
            os.getenv(k)
        except:
            sys.stderr.write(f"Error: missing {k} in .env\n")
            exit(0)
        
    dbconn = pgr.connect(dbname=os.getenv("DB_SCHEMA"),user=os.getenv("DB_USERNAME"),password=os.getenv("DB_PASS"),host=os.getenv("DB_HOST"),port=os.getenv("DB_PORT"),options="-c search_path="+os.getenv("DB_DATABASE"))
    dbconn.set_session(readonly=True)

    with dbconn:
        for table in (bar:=tqdm(tables)):
            bar.set_description(table.name)
            for col in (cbar:=tqdm(table.cols,leave=False)):
                cbar.set_description(col.name)
                if col.dtype != "categorical":
                    continue
                with dbconn.cursor() as curs:
                    curs.execute(f"select distinct {col.name} from {table.name}")
                    res = [r[0] for r in curs.fetchall() if r[0]]
                    col.vals = ",".join(res)

    sys.stderr.write("Done.\n")
        
    with open(datadir/"tableinfo.json","w",encoding="utf-8") as fl:
        json.dump([table.tojson() for table in tables],fl,indent=4)

        