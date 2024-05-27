from pprint import pprint
from nltk.tokenize import sent_tokenize as sentences, word_tokenize as tokenise
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from nltk.tag import pos_tag
import csv,json
from tqdm import tqdm
import random,math,string,sys
from unidecode import unidecode
from collections import defaultdict

BM25_K1 = 1.3
BM25_B = 0.75

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
    
    def alltokens(self,method="basic",enstemming=True,destemming=False,normalise_accents=True,lang="en",
                  name=True,title=True,desc=True,cols=True,queries=True,envalues=False,devalues=True,colnames=True,coltitles=True,queryfilter=None,tokenfilter=None):
        tokens = defaultdict(int)
        if name:
            for t,ct in tokensproc(self.name.replace("_"," "),method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                tokens[t] += ct
        if title:
            if 1:#lang == "en" and self.lang != "en":
                for t,ct in tokensproc(self.engtitle,method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                    tokens[t] += ct
            if 1:#else:
                for t,ct in tokensproc(self.title,method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                    tokens[t] += ct
        if desc:
            if 1:#lang == "en" and self.lang != "en":
                for t,ct in tokensproc(self.engdesc,method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                    tokens[t] += ct
            if 1:#else:
                for t,ct in tokensproc(self.desc,method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                    tokens[t] += ct
        if queries:
            for query in self.queries:
                if queryfilter and query in queryfilter:
                    continue
                for t,ct in tokensproc(query,method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                    tokens[t] += ct
        if cols:
            for col in self.cols:
                for t,ct in col.alltokens(method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang,envalues=envalues,devalues=devalues,name=colnames,title=coltitles).items():
                    tokens[t] += ct
        if tokenfilter:
            for t in tokenfilter:
                if t in tokens:
                    del tokens[t]
        return tokens
        
    def vectorise(self,tokenids,idfs,**kwargs):
        if "lang" not in kwargs:
            kwargs["lang"] = self.lang
        v = [0.0 for _ in tokenids]
        for t,ct in self.alltokens(**kwargs).items():
            if t not in tokenids:
                continue
            v[tokenids[t]] = idfs[t] * ct
        return v
    
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
        
    def alltokens(self,method="basic",enstemming=True,destemming=False,normalise_accents=True,lang="en",name=True,title=True,envalues=False,devalues=True):
        tokens = defaultdict(int)
        if name:
            for t,ct in tokensproc(self.name.replace("_"," "),method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                tokens[t] += ct
        if title:
            if 1:#lang == "en" and self.lang != "en":
                for t,ct in tokensproc(self.engtitle,method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                    tokens[t] += ct
            if 1:#else:
                for t,ct in tokensproc(self.title,method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                    tokens[t] += ct
        if ((envalues and self.lang=="en") or (devalues and self.lang=="de")) and self.dtype != "numeric":
            for t,ct in tokensproc(self.vals.replace(","," ").replace('"'," "),method=method,enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents,lang=lang):
                tokens[t] += ct
        return tokens
        
class TableRanker:
    def __init__(self,tables,queryfilter=None,rankf="rocchio",idff="simple",**params):
        self.tables = tables
        self.rankf = rankf
        self.idff = idff
        self.params = params
        self.tabletokens = {table.name:table.alltokens(lang=table.lang,queryfilter=queryfilter,**params) for table in tables}
        self.tokenids = {t:i for i,t in enumerate({t for table in tables for t in self.tabletokens[table.name]})}
        if idff == "simple":
            self.idfs = {token:math.log(len([1 for table in tables if token in self.tabletokens[table.name]])*1.0/len(tables),2) for token in self.tokenids}
        else:
            self.idfs = {token:math.log(((len(tables)-len([1 for table in tables if token in self.tabletokens[table.name]])+0.5)/(len([1 for table in tables if token in self.tabletokens[table.name]])+0.5))+1,2) for token in self.tokenids}
        self.tablevecs = {table.name:table.vectorise(self.tokenids,self.idfs,queryfilter=queryfilter,**params) for table in tables}
        self.langvecs = {lang:[sum([self.tablevecs[table.name][i] for table in tables if table.lang == lang]) for i in range(len(self.tokenids))] for lang in ["en","de"]}
            
    def vectorisequery(self,q,lang=None):
        v = [0.0 for _ in self.tokenids]
        if lang is None or lang == "en":
            for t,ct in tokensproc(q,**self.params):
                if t not in self.tokenids:
                    continue
                v[self.tokenids[t]] += self.idfs[t]*ct
        if lang is None or lang == "de":
            for t,ct in tokensproc(q,lang="de",**self.params):
                if t not in self.tokenids:
                    continue
                v[self.tokenids[t]] += self.idfs[t]*ct
        return v
        
    def tokenisequery(self,q,lang=None):
        tokens = []
        if lang is None or lang == "en":
            for t,ct in tokensproc(q,**self.params):
                for _ in range(ct):
                    tokens.append(t)
        if lang is None or lang == "de":
            for t,ct in tokensproc(q,lang="de",**self.params):
                for _ in range(ct):
                    tokens.append(t)
        return tokens
        
    def tablequeryjoin(self,table,q):
        join = defaultdict(float)
        for token in self.tokenisequery(q,lang=table.lang):
            if token not in self.tabletokens[table.name]:
                continue
            join[token] += self.tablevecs[table.name][self.tokenids[token]]
        return dict(join)
        
    def rank(self,query):
        lang = self.querylang(query)
        if self.rankf == "rocchio":
            v = self.vectorisequery(query,lang=lang)
            return sorted([(sim(v,self.tablevecs[table.name]),table.name) for table in self.tables],key=lambda x:x[0],reverse=True)
        elif self.rankf == "bm25":
            return sorted([(bm25(dict(tokensproc(query,lang=lang,**self.params)),self.tabletokens[table.name],self.idfs),table.name) for table in self.tables],key=lambda x:x[0],reverse=self.idff!="simple")
        else:
            raise Exception(f"Invalid ranking function \"{self.rankf}\".")
        
    def querylang(self,query):
        v = self.vectorisequery(query,lang=None)
        return sorted([(sim(v,self.langvecs[lang]),lang) for lang in self.langvecs],key=lambda x:x[0],reverse=True)[0][1]
        
METHODS = ["basic","wordnet"]
        
def sim(v1,v2):
    if sum(v1) == 0 or sum(v2) == 0:
        return 0.0
    return sum([v1[i]*v2[i] for i,_ in enumerate(v1)])/(math.sqrt(sum([v**2 for v in v1]))*math.sqrt(sum([v**2 for v in v2])))

def bm25(querytokens,documenttokens,idfs):
    doclen = sum([ct for t,ct in documenttokens.items()])
    return sum([idfs.get(t,0.0)*((documenttokens.get(t,0)*(BM25_K1+1))/(documenttokens.get(t,0)+(BM25_K1*(1-BM25_B+(BM25_B*(doclen/AVERAGE_DOCUMENT_LENGTH)))))) for t,ct in querytokens.items()])

def tagger(tokens): return pos_tag(tokens,tagset="universal",lang="eng")

def wnpos(upos): return upos[0].lower() if upos[0] in "VNR" else ("a" if upos[0] == "J" else "")

def transformabletoken(t,lang="en"):
    try:
        float(t)
        return False
    except:
        return t.lower() not in swset(lang=lang) and not all([c in punctset for c in t])

def tonouns(token,pos,lang="en",enstemming=True,destemming=False,normalise_accents=True):
    pos = wnpos(pos)
    res = [stem(token,lang="en") if (lang=="en" and enstemming) or (lang=="de" and destemming) else token.lower()]
    if pos:
        for syn in wn.synsets(token,pos=pos):
            for lem in syn.lemmas():
                for derv in lem.derivationally_related_forms():
                    if derv.synset().name().split(".")[1] == "n":
                        res.append(stem(derv.name(),lang="en") if (lang=="en" and enstemming) or (lang=="de" and destemming) else derv.name().lower())
    return set([((unidecode if normalise_accents else donothing)(t),1) for t in res])

def tokensproc(s,method="basic",enstemming=True,destemming=False,normalise_accents=True,lang="en",**kwargs):
    tokens = tokenise(s.replace("-"," "))
    res = []
    if method == "basic" or lang != "en":
        for token in tokens:
            if transformabletoken(token,lang=lang):
                res.append(((unidecode if normalise_accents else donothing)(stem(token,lang=lang) if (lang=="en" and enstemming) or (lang=="de" and destemming) else token.lower()),1))
    elif method == "wordnet":
        for token,ct in [n for t,pos in tagger(tokens) for n in tonouns(t,pos,lang="en",enstemming=enstemming,destemming=destemming,normalise_accents=normalise_accents) if transformabletoken(t)]:
            res.append((token,ct))
    dres = {}
    for t,ct in res:
        if t not in dres:
            dres[t] = ct
        else:
            dres[t] += ct
    return list(dres.items())

enswset = set(stopwords.words("english"))
deswset = set(stopwords.words("german"))
enstem = SnowballStemmer("english").stem
destem = SnowballStemmer("german").stem
punctset = set(string.punctuation)

def stem(t,lang="en"): return (enstem if lang == "en" else destem)(t)
def swset(lang="en"): return enswset if lang  == "en" else deswset

def donothing(x): return x

def mean(xs,zero=True): return (sum(xs)*1.0/len(xs)) if len(xs) or not zero else 0.0

def tableclass(name,tables): return [table for table in tables if table.name == name][0]


class ResultAnalyser:
    def __init__(self,tables,nfolds,**params):
        self.tables = tables
        self.nfolds = nfolds
        self.params = params
        self.runs = []
        
    def newrun(self):
        allqueries = [query for table in self.tables for query in table.queries]
        random.shuffle(allqueries)
        run = ResultRun(self.tables,allqueries,self.nfolds,**self.params)
        run.run()
        self.runs.append(run)
        
    def meanresults(self):
        tres = self.tableresults()
        return {"accuracy":mean([run.accuracy() for run in self.runs]),
                "enaccuracy":mean([run.splitaccuracy("en") for run in self.runs]),
                "deaccuracy":mean([run.splitaccuracy("de") for run in self.runs]),
                "langaccuracy":mean([run.langaccuracy() for run in self.runs]),
                "enlangaccuracy":mean([run.langaccuracy("en") for run in self.runs]),
                "delangaccuracy":mean([run.langaccuracy("de") for run in self.runs]),
                "enratio":mean([run.enratio() for run in self.runs]),
                "precision_weighted":sum([tres[t]["precision"]*len(tableclass(t,self.tables).queries) for t in tres])/sum([len(t.queries) for t in self.tables]),
                "recall_weighted":sum([tres[t]["recall"]*len(tableclass(t,self.tables).queries) for t in tres])/sum([len(t.queries) for t in self.tables]),
                "f1_weighted":sum([tres[t]["f1"]*len(tableclass(t,self.tables).queries) for t in tres])/sum([len(t.queries) for t in self.tables]),
                "precision_raw":mean([tres[t]["precision"] for t in tres]),
                "recall_raw":mean([tres[t]["recall"] for t in tres]),
                "f1_raw":mean([tres[t]["f1"] for t in tres])}
                
    def tableresults(self):
        return {t.name:{"queries":len(t.queries),
                        "accuracy":mean([run.tableaccuracy()[t.name] for run in self.runs]),
                        "precision":mean([run.tableprecrecf1()[t.name]["precision"] for run in self.runs]),
                        "recall":mean([run.tableprecrecf1()[t.name]["recall"] for run in self.runs]),
                        "f1":mean([run.tableprecrecf1()[t.name]["f1"] for run in self.runs])}
                for t in self.tables}
                
    def detailedresults(self):
        res = []
        for run in self.runs:
            res.append({"accuracy":run.accuracy(),"enaccuracy":run.splitaccuracy("en"),"deaccuracy":run.splitaccuracy("de"),"langaccuracy":run.langaccuracy(),"enratio":run.enratio(),"tableresults":run.tableresults()})
        return res
        
class ResultRun:
    def __init__(self,tables,allqueries,nfolds,**params):
        self.tables = tables
        self.allqueries = allqueries
        self.nfolds = nfolds
        self.params = params
        self.results = []
       
    def accuracy(self):
        return mean([result.correct() for result in self.results])
        
    def splitaccuracy(self,lang):
        return mean([result.correct() for result in self.results if result.table.lang == lang])
        
    def langaccuracy(self,lang=None):
        if not lang:
            return mean([result.langcorrect() for result in self.results])
        else:
            return mean([result.langcorrect() for result in self.results if result.table.lang == lang])
        
    def enratio(self):
        return mean([result.table.lang == "en" for result in self.results])
        
    def tableaccuracy(self):
        tableaccs = {table.name:[] for table in self.tables}
        for result in self.results:
            tableaccs[result.table.name].append(result.correct())
        return {k:mean(v) for k,v in tableaccs.items()}
        
    def tableprecrecf1(self):
        tablepreds = {table.name:{"tp":[],"fp":[],"fn":[]} for table in self.tables}
        for result in self.results:
            if result.correct():
                tablepreds[result.table.name]["tp"].append(result)
        for table in self.tables:
            for result in self.results:
                if not result.correct():
                    if result.chosentable() == table.name:
                        tablepreds[table.name]["fp"].append(result)
                    elif result.table.name == table.name:
                        tablepreds[table.name]["fn"].append(result)
        return {t:{"precision":len(tablepreds[t]["tp"])*1.0/(len(tablepreds[t]["tp"])+len(tablepreds[t]["fp"])) if len(tablepreds[t]["tp"])+len(tablepreds[t]["fp"]) else 0.0,
                   "recall":len(tablepreds[t]["tp"])*1.0/(len(tablepreds[t]["tp"])+len(tablepreds[t]["fn"])) if len(tablepreds[t]["tp"])+len(tablepreds[t]["fn"]) else 0.0,
                   "f1":(len(tablepreds[t]["tp"])*2.0)/((len(tablepreds[t]["tp"])*2.0)+len(tablepreds[t]["fp"])+len(tablepreds[t]["fn"])) if tableclass(t,self.tables).queries else 1.0} for t in tablepreds}
    
    def tableresults(self):
        tableaccs = self.tableaccuracy()
        res = {table.name:{"lang":table.lang,"accuracy":tableaccs[table.name],"tokens":[result for result in self.results if result.table.name == table.name][0].tabletokens,"queries":[]} for table in self.tables}
        for result in self.results:
            res[result.table.name]["queries"].append({"query":result.query,"correct":result.correct(),"langcorrect":result.langcorrect(),"chosentable":result.chosentable(),"chosenlang":result.langresult,
                                                      "truetokens":result.truetokens,"predtokens":result.predtokens,"truetablejoin":result.truetablejoin,"predtablejoin":result.predtablejoin})
        return res
        
    def run(self):
        answers = {query:table for table in self.tables for query in table.queries}
        for i in range(self.nfolds):
            testqueries = self.allqueries[(len(self.allqueries)*i)//self.nfolds:(len(self.allqueries)*(i+1))//self.nfolds]
            tr = TableRanker(self.tables,queryfilter=testqueries,**self.params)
            for query in testqueries:
                rank,lang = tr.rank(query),tr.querylang(query)
                self.results.append(QueryResult(query,answers[query],rank,lang,tr.tokenisequery(query,lang=answers[query].lang),tr.tokenisequery(query,lang=lang),
                                                tr.tablequeryjoin(answers[query],query),tr.tablequeryjoin(tableclass(rank[0][1],self.tables),query),
                                                {token:tr.tablevecs[answers[query].name][tr.tokenids[token]] for token in tr.tabletokens[answers[query].name]}))
                
class QueryResult:
    def __init__(self,query,table,tablerank,langresult,truetokens,predtokens,truetablejoin,predtablejoin,tabletokens):
        self.query = query
        self.table = table
        self.tablerank = tablerank
        self.langresult = langresult
        self.truetokens = truetokens
        self.predtokens = predtokens
        self.truetablejoin = truetablejoin
        self.predtablejoin = predtablejoin
        self.tabletokens = tabletokens
    
    def chosentable(self):
        return self.tablerank[0][1]
    
    def correct(self):
        return self.table.name == self.chosentable()
        
    def langcorrect(self):
        return self.table.lang == self.langresult
            

with open("data/locations.json","r",encoding="utf-8") as fl:
    locs = {pt for t in json.load(fl).keys() for pt in [t.lower(),stem(t,lang="en").lower(),stem(t,lang="de").lower()]}

PARAMS = dict(tokenfilter=locs,devalues=True,envalues=False,enstemming=True,destemming=True)
 
with open("data/tableinfo.json","r",encoding="utf-8") as fl:
    tables = [TableInfo.fromjson(table) for table in json.load(fl)]
AVERAGE_DOCUMENT_LENGTH = mean([sum([ct for t,ct in table.alltokens(**PARAMS).items()]) for table in tables])

tableranker = TableRanker(tables,queryfilter=None,rankf="bm25",idff="simple",**PARAMS)

if __name__ == "__main__":
    print("Running evaluation...")
    results = ResultAnalyser(tables,10,rankf="bm25",idff="simple",**PARAMS)
    for i in tqdm(range(10)):
        results.newrun()
    pprint(results.tableresults())
    pprint(results.meanresults())