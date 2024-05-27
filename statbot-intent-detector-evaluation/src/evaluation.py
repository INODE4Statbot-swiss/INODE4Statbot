from pprint import pprint
from pathlib import Path
import json
from tqdm import tqdm
import random,sys
from pytablewriter import MarkdownTableWriter

from tableinfo import TableInfo
from tableranking import OracleLanguageDetector,EnsembleLanguageDetector,TableRanker
from preprocessing import Tokeniser
from bow import BM25TableRanker,RocchioLanguageDetector
from ml import LangdetectLanguageDetector,LangidLanguageDetector,BERTTableRanker


datadir = Path(__file__).parent.parent/"data"


def mean(xs,zero=True): return (sum(xs)/len(xs)) if len(xs) or not zero else 0.0
        
class ResultAnalyser:
    def __init__(self,tables,tableranker,rankerparams,langdetector,langparams):
        self._tables = tables
        self._tableranker = tableranker
        self._rankerparams = rankerparams
        self._langdetector = langdetector
        self._langparams = langparams
        self._runs = []

    def run(self,*args,**kwargs):
        raise Exception(f"Error: {type(self).__name__}.run() method not implemented.")
        
    def _newrun(self,trainqueries,evalqueries):
        run = ResultRun(self._tables,trainqueries,evalqueries,self._tableranker,self._rankerparams,self._langdetector,self._langparams)
        run.run()
        self._runs.append(run)
                
    def results(self):
        def _meanerrorbar(xs):
            meanv = mean(xs)
            if not xs: return meanv,0
            return meanv,max(meanv-min(xs),max(xs)-meanv)
        tres = self.tableresults()
        return {"langaccuracy":_meanerrorbar([run.langaccuracy() for run in self._runs]),
                "enlangaccuracy":_meanerrorbar([run.langaccuracy("en") for run in self._runs]),
                "delangaccuracy":_meanerrorbar([run.langaccuracy("de") for run in self._runs]),
                "enratio":_meanerrorbar([run.enratio() for run in self._runs]),
                "enrecall@1":_meanerrorbar([run.recallat(1,"en") for run in self._runs]),
                "enrecall@3":_meanerrorbar([run.recallat(3,"en") for run in self._runs]),
                "enrecall@5":_meanerrorbar([run.recallat(5,"en") for run in self._runs]),
                "derecall@1":_meanerrorbar([run.recallat(1,"de") for run in self._runs]),
                "derecall@3":_meanerrorbar([run.recallat(3,"de") for run in self._runs]),
                "derecall@5":_meanerrorbar([run.recallat(5,"de") for run in self._runs]),
                "recall@1":_meanerrorbar([run.recallat(1) for run in self._runs]),
                "recall@3":_meanerrorbar([run.recallat(3) for run in self._runs]),
                "recall@5":_meanerrorbar([run.recallat(5) for run in self._runs])}
                
    def tableresults(self):
        return {t.name:{"queriescovered":mean([len(run.tablequeries()[t.name]) for run in self._runs]),
                        "accuracy":mean([run.tableaccuracy()[t.name] for run in self._runs]),
                        "precision":mean([run.tableprecrecf1()[t.name]["precision"] for run in self._runs]),
                        "recall":mean([run.tableprecrecf1()[t.name]["recall"] for run in self._runs]),
                        "f1":mean([run.tableprecrecf1()[t.name]["f1"] for run in self._runs])}
                for t in self._tables}
                
    def langresults(self,correct=None):
        return [run.langresults(correct) for run in self._runs]
        
    def intentresults(self,correct=None):
        return [run.intentresults(correct) for run in self._runs]

class TrainEvalResultAnalyser(ResultAnalyser):
    def __init__(self,tables,trainqueries,evalqueries,tableranker,rankerparams,langdetector,langparams):
        super().__init__(tables,tableranker,rankerparams,langdetector,langparams)
        self._trainqueries = trainqueries
        self._evalqueries = evalqueries
        
    def run(self):
        self._newrun(self._trainqueries,self._evalqueries)

class CrossEvaluationResultAnalyser(ResultAnalyser):
    def __init__(self,tables,nfolds,tableranker,rankerparams,langdetector,langparams):
        super().__init__(tables,tableranker,rankerparams,langdetector,langparams)
        self._nfolds = nfolds

    def run(self,nruns=1,progress=True):
        allqueries = [query for table in self._tables for query in table.queries]
        querytables = {query:table.name for table in self._tables for query in table.queries}
        for _ in (tqdm(range(nruns)) if progress else range(nruns)):
            random.shuffle(allqueries)
            for i in (tqdm(range(self._nfolds),leave=False) if progress else range(self._nfolds)):
                testqueries = allqueries[(len(allqueries)*i)//self._nfolds:(len(allqueries)*(i+1))//self._nfolds]
                trainqueries = [query for query in allqueries if query not in testqueries]
                self._newrun({query:querytables[query] for query in trainqueries},{query:querytables[query] for query in testqueries})                
       
class ResultRun:
    def __init__(self,tables,trainqueries,evalqueries,tableranker,rankerparams,langdetector,langparams):
        self._tables = tables
        self._trainqueries = trainqueries
        self._evalqueries = evalqueries
        self._evalanswers = {query:[table for table in self._tables if query in table.queries][0] for query in self._evalqueries}
        self._tableranker = tableranker
        self._rankerparams = rankerparams
        self._langdetector = langdetector
        self._langparams = langparams
        self._results = []
       
    def accuracy(self):
        return mean([result.correct() for result in self._results])
        
    def splitaccuracy(self,lang):
        return mean([result.correct() for result in self._results if result.table.lang == lang])
        
    def langaccuracy(self,lang=None):
        if not lang:
            return mean([result.langcorrect() for result in self._results])
        else:
            return mean([result.langcorrect() for result in self._results if result.table.lang == lang])
        
    def enratio(self):
        return mean([result.table.lang == "en" for result in self._results])
        
    def recallat(self,n=1,lang=None):
        return mean([result.recallat(n) for result in self._results if not lang or result.table.lang == lang])
        
    def tableaccuracy(self):
        tableaccs = {table.name:[] for table in self._tables}
        for result in self._results:
            tableaccs[result.table.name].append(result.correct())
        return {k:mean(v) if v else 1.0 for k,v in tableaccs.items()}
        
    def tablequeries(self):
        return {table.name:[query for query in self._evalanswers if self._evalanswers[query].name == table.name] for table in self._tables}
        
    def tableprecrecf1(self):
        tablepreds = {table.name:{"tp":[],"fp":[],"fn":[]} for table in self._tables}
        for result in self._results:
            if result.correct():
                tablepreds[result.table.name]["tp"].append(result)
        for table in self._tables:
            for result in self._results:
                if not result.correct():
                    if result.chosentable() == table.name:
                        tablepreds[table.name]["fp"].append(result)
                    elif result.table.name == table.name:
                        tablepreds[table.name]["fn"].append(result)
        return {t:{"precision":len(vs["tp"])/(len(vs["tp"])+len(vs["fp"])) if len(vs["tp"])+len(vs["fp"]) else (0.0 if [q for qs in vs.values() for q in qs] else 1.0),
                   "recall":len(vs["tp"])/(len(vs["tp"])+len(vs["fn"])) if len(vs["tp"])+len(vs["fn"]) else (0.0 if [q for qs in vs.values() for q in qs] else 1.0),
                   "f1":(len(vs["tp"])*2)/((len(vs["tp"])*2)+len(vs["fp"])+len(vs["fn"])) if [q for qs in vs.values() for q in qs] else 1.0} for t,vs in tablepreds.items()}
                   
    def langresults(self,correct=None):
        return [{"query":res.query,"predicted":res.langresult,"truevalue":res.table.lang} for res in self._results if correct is None or res.langcorrect() == correct]
        
    def intentresults(self,correct=None):
        return [{"query":res.query,"predicted":res.chosentable(),"truevalue":res.table.name} for res in self._results if correct is None or res.correct() == correct]
        
    def run(self):
        tr = self._tableranker(self._tables,**self._rankerparams)
        ld = self._langdetector(self._tables,**self._langparams)
        tr.train(self._trainqueries)
        ld.train(self._trainqueries)
        for query in self._evalqueries:
            lang = ld.lang(query)
            rank = tr.rank(query,lang)
            self._results.append(QueryResult(query,self._evalanswers[query],rank,lang))
                
class QueryResult:
    def __init__(self,query,table,tablerank,langresult):
        self.query = query
        self.table = table
        self.tablerank = tablerank
        self.langresult = langresult
    
    def chosentable(self):
        return self.tablerank[0][1]
    
    def correct(self):
        return self.table.name == self.chosentable()
        
    def recallat(self,n=1):
        return self.table.name in [t for _,t in self.tablerank[:n]]
        
    def langcorrect(self):
        return self.table.lang == self.langresult
            

if __name__ == "__main__":     
    with open(datadir/"tableinfo.json","r",encoding="utf-8") as fl:
        tables = [TableInfo.fromjson(table) for table in json.load(fl)]
    
    with open(datadir/"devqueries.json","r",encoding="utf-8") as fl:
        devqueries = json.load(fl)
    with open(datadir/"trainqueries.json","r",encoding="utf-8") as fl:
        trainqueries = json.load(fl)
    with open(datadir/"testqueries.json","r",encoding="utf-8") as fl:
        testqueries = json.load(fl)

    for qgroup in [devqueries,trainqueries,testqueries]:
        for query,table in list(qgroup.items()):
            if not any([ttable.name==table for ttable in tables]):
                del qgroup[query]
            elif not any([query==tquery for ttable in tables for tquery in ttable.queries]):
                del qgroup[query]
                
    def results(tableranker,rankerparams,langdetector,langparams,nfolds=10,nruns=10,progress=True):
        if progress:
            print("Running dev evaluation...")
        dev = TrainEvalResultAnalyser(tables,trainqueries,devqueries,tableranker,rankerparams,langdetector,langparams)
        dev.run()
        if progress:
            print("Running test evaluation...")
        test = TrainEvalResultAnalyser(tables,trainqueries,testqueries,tableranker,rankerparams,langdetector,langparams)
        test.run()
        if progress:
            print(f"Running {nfolds}-fold cross-evaluation for {nruns} random runs...")
        crosseval = CrossEvaluationResultAnalyser(tables,nfolds,tableranker,rankerparams,langdetector,langparams)
        crosseval.run(nruns=nruns,progress=progress)
        return {"crosseval":crosseval.results(),"dev":dev.results(),"test":test.results()}
        
    tokenisers = {lang:Tokeniser(lang=lang) for lang in ["en","de"]}
        
    langdetectors = {"langdetect":(LangdetectLanguageDetector,dict()),
                     "langid":(LangidLanguageDetector,dict()),
                     "rocchio":(RocchioLanguageDetector,dict(tokenisers=tokenisers)),
                     "ensemble":(EnsembleLanguageDetector,dict(detectors=[(LangdetectLanguageDetector,dict()),(LangidLanguageDetector,dict()),(RocchioLanguageDetector,dict(tokenisers=tokenisers))]))}
    
    print("Evaluating language detectors...")
    langres = {}
    for name,(langdetector,params) in langdetectors.items():
        print(f"Evaluating \"{name}\"...")
        langres[name] = results(TableRanker,dict(),langdetector,params)

    tablerankers = {"bm25":(BM25TableRanker,dict(tokenisers=tokenisers)),
                    "bert":(BERTTableRanker,dict())}

    print("Evaluating table classifiers...")
    res = {}
    for name,(tableranker,params) in tablerankers.items():
        print(f"Evaluating \"{name}\"...")
        res[name] = results(tableranker,params,OracleLanguageDetector,dict())
        
    vmat = []
    for name,scs in langres.items():
        vmat.append([name]+[f'{scs[k][kk+"langaccuracy"][0]:5.4f}'+(f' (+/- {scs[k][kk+"langaccuracy"][1]:5.4f})' if k == "crosseval" else "") for k in ["dev","test","crosseval"] for kk in ["en","de",""]])
    MarkdownTableWriter(table_name="Language Detector Results",
                        headers=[""]+[ss+": "+s for ss in ["dev","test","crosseval"] for s in ["English","German","Overall"]],
                        value_matrix=vmat).write_table()
        
    vmat = []
    for name,scs in res.items():
        for i in [1,3,5]:
            vmat.append([name+f" (r@{i})"]+[f'{scs[k][kk+f"recall@{i}"][0]:5.4f}'+(f' (+/- {scs[k][kk+f"recall@{i}"][1]:5.4f})' if k == "crosseval" else "") for k in ["dev","test","crosseval"] for kk in ["en","de",""]])
    MarkdownTableWriter(table_name="Table Classifier Results",
                        headers=[""]+[ss+": "+s for ss in ["dev","test","crosseval"] for s in ["English","German","Overall"]],
                        value_matrix=vmat).write_table()
                        