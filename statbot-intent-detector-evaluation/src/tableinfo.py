import json
from collections import defaultdict

class TableInfo:
    def __init__(self,dbid,name,lang,title,desc,engtitle,engdesc,cols,queries):
        self.dbid = dbid
        self.name = name
        self.lang = lang
        self.title = title
        self.desc = desc
        self.engtitle = engtitle
        self.engdesc = engdesc
        self.cols = cols
        self.queries = queries
        
    def tojson(self):
        return {"dataset_id":self.dbid,"table_name":self.name,"language":self.lang,"title":self.title,"description":self.desc,"title_en":self.engtitle,"description_en":self.engdesc,
                "column_info":[col.tojson() for col in self.cols],"sample_queries":self.queries}
    
    @staticmethod
    def fromjson(j):
        return TableInfo(j["dataset_id"],j["table_name"],j["language"],j["title"],j["description"],j["title_en"],j["description_en"],[ColumnInfo.fromjson(c) for c in j["column_info"]],j["sample_queries"])
    
    def todocument(self,lang=None,name=True,title=True,desc=True,cols=True,queries=True,values=True,colnames=True,coltitles=True,queryfilter=None):
        if not lang:
            lang = self.lang
        docsegments = []
        if name:
            docsegments.append(self.name.replace("_"," "))
        if title:
            if lang == "en" and self.lang != "en":
                docsegments.append(self.engtitle)
            else:
                docsegments.append(self.title)
        if desc:
            if lang == "en" and self.lang != "en":
                docsegments.append(self.engdesc)
            else:
                docsegments.append(self.desc)
        if queries:
            for query in self.queries:
                if queryfilter and query in queryfilter:
                    continue
                docsegments.append(query)
        if cols:
            for col in self.cols:
                docsegments.extend(col.todocsegments(lang=lang,values=values,name=colnames,title=coltitles))
        document = ""
        for docsegment in docsegments:
            docsegment = docsegment.strip()
            if not docsegment:
                continue
            if docsegment[-1] not in ".!?":
                docsegment += "."
            document += docsegment + " "
        return document.rstrip()
    
class ColumnInfo:
    def __init__(self,dtype,lang,name,title,engtitle,vals):
        self.dtype = dtype
        self.lang = lang
        self.name = name
        self.title = title
        self.engtitle = engtitle
        self.vals = vals

    def tojson(self):
        return {"data_type":self.dtype,"language":self.lang,"column_name":self.name,"title":self.title,"title_en":self.engtitle,"example_values":self.vals}

    @staticmethod
    def fromjson(j):
        return ColumnInfo(j["data_type"],j["language"],j["column_name"],j["title"],j["title_en"],j["example_values"])
        
    def todocsegments(self,lang=None,name=True,title=True,values=True):
        if not lang:
            lang = self.lang
        docsegments = []
        if name:
            docsegments.append(self.name.replace("_"," "))
        if title:
            if lang == "en" and self.lang != "en":
                docsegments.append(self.engtitle)
            else:
                docsegments.append(self.title)
        if values and self.dtype != "numeric":
            docsegments.append(", ".join([pt.strip() for pt in self.vals.split(",")]))
        return docsegments
        
        
if __name__ == "__main__":
    from pprint import pprint
    from pathlib import Path
    import json
    datadir = Path(__file__).parent.parent/"data"
    
    with open(datadir/"tableinfo.json","r",encoding="utf-8") as fl:
        tables = [TableInfo.fromjson(table) for table in json.load(fl)]
    for table in tables:
        table.todocument()        

