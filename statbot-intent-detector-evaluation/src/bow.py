import math,numpy as np

from tableranking import TableRanker,LanguageDetector

class BM25TableRanker(TableRanker):
    _K1 = 1.3
    _B = 0.75
    def __init__(self,tables,tokenisers,**params):
        super().__init__(tables)
        self._tokenisers = tokenisers
        self._params = params
        self.train([])
        
    def train(self,queries):
        self._tabletokens = {table.name:self._tokenisers[table.lang].counttokens(table.todocument(queryfilter=[query for query in table.queries if query not in queries],**self._params)) for table in self._tables}
        def _idf(token):
            return math.log(((len(self._tables)-len([1 for table in self._tables if token in self._tabletokens[table.name]])+0.5)/(len([1 for table in self._tables if token in self._tabletokens[table.name]])+0.5))+1,2)
        self._idfs = {token:_idf(token) for token in {t for table in self._tables for t in self._tabletokens[table.name]}}
        self._doclens = {table.name:sum([ct for t,ct in self._tabletokens[table.name].items()]) for table in self._tables}
        self._avgdoclen = sum(self._doclens.values())/len(self._tables)
        deviations = {tablename:(self._doclens[tablename]-self._avgdoclen)**2 for tablename in self._doclens}
        sd = math.sqrt(sum(deviations.values())/len(deviations))
        for tablename in self._doclens:
            if self._doclens[tablename] > self._avgdoclen+(2*sd):
               self._doclens[tablename] = self._avgdoclen+(2*sd)
            elif self._doclens[tablename] < self._avgdoclen-(2*sd):
               self._doclens[tablename] = self._avgdoclen-(2*sd)
        self._avgdoclen = sum(self._doclens.values())/len(self._tables)
        def _tokenbm25(token,ct,tablename):
            return self._idfs[token]*((ct*(self._K1+1))/(ct+(self._K1*(1-self._B+(self._B*(self._doclens[tablename]/self._avgdoclen))))))
        self._tablebm25factors = {table.name:{token:_tokenbm25(token,ct,table.name) for token,ct in self._tabletokens[table.name].items()} for table in self._tables}
            
    def _bm25(self,querytokens,tablename):
        return sum([self._tablebm25factors[tablename].get(t,0.0)*ct for t,ct in querytokens.items()])
        
    def rank(self,query,lang):
        querytokens = self._tokenisers[lang].counttokens(query)
        return sorted([(self._bm25(querytokens,table.name),table.name) for table in self._tables if table.lang == lang],reverse=True)
             
        
class RocchioLanguageDetector(LanguageDetector):
    def __init__(self,tables,tokenisers,**params):
        super().__init__(tables)
        self._tokenisers = tokenisers
        self._params = params
        self.train([])
        
    def train(self,queries):
        self._tabletokens = {table.name:self._tokenisers[table.lang].counttokens(table.todocument(queryfilter=[query for query in table.queries if query not in queries],**self._params)) for table in self._tables}
        self._tokenids = {t:i for i,t in enumerate({t for table in self._tables for t in self._tabletokens[table.name]})}
        def _idf(token):
            return math.log(((len(self._tables)-len([1 for table in self._tables if token in self._tabletokens[table.name]])+0.5)/(len([1 for table in self._tables if token in self._tabletokens[table.name]])+0.5))+1,2)
        self._idfs = {token:_idf(token) for token in self._tokenids}
        tablevecs = {table.name:np.zeros(len(self._tokenids)) for table in self._tables}
        for tablename,tokens in self._tabletokens.items():
            for token,ct in tokens.items():
                tablevecs[tablename][self._tokenids[token]] = ct*self._idfs[token]
        self._langvecs = {lang:np.sum([tablevecs[table.name] for table in self._tables if table.lang == lang],axis=0) for lang in ["en","de"]}
        
    def _vectorisequery(self,query):
        entokens,detokens = self._tokenisers["en"].counttokens(query),self._tokenisers["de"].counttokens(query)
        v = np.zeros(len(self._tokenids))
        for token,ct in entokens.items():
            if token not in self._tokenids:
                continue
            v[self._tokenids[token]] += ct*self._idfs[token]
        for token,ct in detokens.items():
            if token not in self._tokenids:
                continue
            v[self._tokenids[token]] += ct*self._idfs[token]
        return v
        
    def lang(self,query): 
        def _sim(v1,v2):
            n1,n2 = np.linalg.norm(v1),np.linalg.norm(v2)
            if not n1 or not n2:
                return 0.0
            return np.dot(v1,v2)/(n1*n2)
        v = self._vectorisequery(query)
        return sorted([(_sim(v,self._langvecs[lang]),lang) for lang in self._langvecs],reverse=True)[0][1]
        

        
if __name__ == "__main__":
    import json
    from pathlib import Path
    from tableinfo import TableInfo
    datadir = Path(__file__).parent.parent/"data"
    with open(datadir/"tableinfo.json","r",encoding="utf-8") as fl:
        tables = [TableInfo.fromjson(table) for table in json.load(fl)]
       
    from preprocessing import Tokeniser
    tokenisers = {lang:Tokeniser(lang=lang) for lang in ["en","de"]}
        
    queries = [query for table in tables for query in table.queries]
    querytables = {query:table.name for table in tables for query in table.queries}

    langdetector = RocchioLanguageDetector(tables,tokenisers)
    langdetector.train(queries) 
    bm25 = BM25TableRanker(tables,tokenisers)
    bm25.train(queries)
    res = [querytables[query]==bm25.rank(query,langdetector.lang(query))[0][1] for query in queries]
    print(sum(res)/len(res))

    print("Test passed.")
            