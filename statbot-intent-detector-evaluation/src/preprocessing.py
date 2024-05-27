import nltk
from nltk.tokenize import word_tokenize as tokenise
try:
    tokenise("Is the tokeniser downloaded?")
except:
    nltk.download("punkt")
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
try:
    stopwords.words("english")
except:
    nltk.download("stopwords")
from unidecode import unidecode
import string
from collections import defaultdict

enswset = set(stopwords.words("english"))
deswset = set(stopwords.words("german"))
enstem = SnowballStemmer("english").stem
destem = SnowballStemmer("german").stem
punctset = set(string.punctuation)

def donothing(x): return x


class Tokeniser:
    def __init__(self,lang="en",stemming=True,normalise_accents=True,unhyphenate=True,filterstopwords=True,filterpunct=True,filternumeric=True):
        self._lang = lang
        self._stemming = stemming
        self._stem = enstem if lang == "en" else destem
        self._normalise_accents = normalise_accents
        self._stripaccents = unidecode if normalise_accents else donothing
        self._unhyphenate = unhyphenate
        self._filterstopwords = filterstopwords
        self._swset = enswset if lang == "en" else deswset
        self._filterpunct = filterpunct
        self._filternumeric = filternumeric

    def getparams(self):
        return dict(lang=self._lang,stemming=self._stemming,normalise_accents=self._normalise_accents,unhyphenate=self._unhyphenate,
                    filterstopwords=self._filterstopwords,filterpunct=self._filterpunct,filternumeric=self._filternumeric)

    def _transformabletoken(self,t):
        try:
            float(t)
            if self._filternumeric:
                return False
            raise Exception
        except:
            return (not self._filterstopwords or t.lower() not in self._swset) and (not self._filterpunct or not all([c in punctset for c in t]))

    def _proctoken(self,t):
        if self._stemming:
            t = self._stem(t)
        else:
            t = t.lower()
        return self._stripaccents(t)

    def rawtokens(self,s):
        if self._unhyphenate:
            s = s.replace("-"," ")
        return [self._proctoken(t) for t in tokenise(s) if self._transformabletoken(t)]

    def counttokens(self,s):
        ctokens = defaultdict(int)
        for t in self.rawtokens(s):
            ctokens[t] += 1
        return dict(ctokens)


if __name__ == "__main__":
    from tableinfo import TableInfo
    from pprint import pprint
    from pathlib import Path
    import json
    datadir = Path(__file__).parent.parent/"data"
        
    entokenisers,detokenisers = [],[]
    with open(datadir/"tableinfo.json","r",encoding="utf-8") as fl:
        tables = [TableInfo.fromjson(table) for table in json.load(fl)]
    for table in tables:
        params = dict(stemming=False,normalise_accents=False,unhyphenate=False,filterstopwords=False,filterpunct=False,filternumeric=False)
        doc = table.todocument()
        Tokeniser(lang=table.lang,**params).counttokens(doc)
        for param in params:
            params[param] = True
            Tokeniser(lang=table.lang,**params).counttokens(doc)
            
    print("Test passed.")