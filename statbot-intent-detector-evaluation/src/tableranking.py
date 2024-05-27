import random

LANGUAGES = ["en","de"]

class TableRanker:
    def __init__(self,tables):
        self._tables = tables
                            
    def train(self,queries):
        pass
        
    def rank(self,query,lang):
        return sorted([(random.random(),table.name) for table in self._tables],reverse=True)
        
class LanguageDetector:
    def __init__(self,tables):
        self._tables = tables
        
    def train(self,queries):
        pass
        
    def lang(self,query):
        return random.choice(LANGUAGES)

class OracleLanguageDetector(LanguageDetector):
    def __init__(self,tables):
        super().__init__(tables)
        
    def lang(self,query):
        for table in self._tables:
            if query in table.queries:
                return table.lang
        raise Exception(f"Error: OracleLanguageDetector requires a known query. (Input Query: \"{query}\")")
        
class EnsembleLanguageDetector(LanguageDetector):
    def __init__(self,tables,detectors=None):
        super().__init__(tables)
        self._detectors = [detector(tables,**params) for detector,params in detectors]
        try:
            self._detectors[0]
        except:
            raise Exception("Error: No language detectors provided to EnsembleLanguageDetector")
        
    def train(self,queries):
        for detector in self._detectors:
            detector.train(queries)
           
    def lang(self,query):
        votes = {lang:0 for lang in LANGUAGES}
        for detector in self._detectors:
            votes[detector.lang(query)] += 1
        return sorted(votes.items(),key=lambda x:x[1],reverse=True)[0][0]