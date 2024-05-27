from tqdm import tqdm
from py3langid.langid import LanguageIdentifier,MODEL_FILE
import langdetect
import torch
import random
import numpy as np
_SEED = 0
langdetect.DetectorFactory.seed = _SEED
random.seed(_SEED)
np.random.seed(_SEED)
torch.manual_seed(_SEED)
torch.cuda.manual_seed_all(_SEED)
from torch import nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from transformers import BertTokenizer,BertModel,get_linear_schedule_with_warmup

from tableranking import TableRanker,LanguageDetector,LANGUAGES


class LangdetectLanguageDetector(LanguageDetector):
    def __init__(self,tables):
        super().__init__(tables)
        
    def lang(self,query):
        lang = langdetect.detect(query)
        return lang if lang in LANGUAGES else "en"
        
class LangidLanguageDetector(LanguageDetector):
    def __init__(self,tables):
        super().__init__(tables)
        self._detector = LanguageIdentifier.from_pickled_model(MODEL_FILE)
        self._detector.set_languages(LANGUAGES)
        
    def lang(self,query):
        return self._detector.classify(query)[0]

class BERTClassifier(nn.Module):
    def __init__(self,modelname,nclasses):
        super().__init__()
        self.bert = BertModel.from_pretrained(modelname)
        self.dropout = nn.Dropout(0.1)
        self.fc = nn.Linear(self.bert.config.hidden_size,nclasses)

    def forward(self,input_ids,attention_mask):
        outputs = self.bert(input_ids=input_ids,attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        x = self.dropout(pooled_output)
        logits = self.fc(x)
        return logits

class BERTTableRanker(TableRanker):
    def __init__(self,tables,modelname="bert-base-multilingual-cased",maxlen=128):
        super().__init__(tables)
        random.seed(_SEED)
        np.random.seed(_SEED)
        torch.manual_seed(_SEED)
        torch.cuda.manual_seed_all(_SEED)
        self._tablenums = {table.name:i for i,table in enumerate(tables)}
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model = BERTClassifier(modelname,len(tables)).to(self._device)
        self._tokeniser = BertTokenizer.from_pretrained(modelname)
        self._maxlen = maxlen
        
    def _tokenise(self,query):
        return self._tokeniser(query,return_tensors='pt',max_length=self._maxlen,padding='max_length',truncation=True)
        
    def train(self,queries,numsteps=300,batchsize=32,learningrate=2e-5,progress=True):
        dset = []
        for query,tablename in queries.items():
            encoding = self._tokenise(query)
            dset.append({'input_ids':encoding['input_ids'].flatten(),'attention_mask':encoding['attention_mask'].flatten(),'label':torch.tensor(self._tablenums[tablename])})
        optimiser = AdamW(self._model.parameters(),lr=learningrate)
        scheduler = get_linear_schedule_with_warmup(optimiser,num_warmup_steps=0,num_training_steps=numsteps)
        for _ in (tqdm(range((numsteps*batchsize)//len(dset)),leave=False) if progress else range((numsteps*batchsize)//len(dset))):
            self._model.train()
            dataloader = DataLoader(dset,batch_size=batchsize,shuffle=True)
            for batch in dataloader:
                optimiser.zero_grad()
                outputs = self._model(input_ids=batch['input_ids'].to(self._device),attention_mask=batch['attention_mask'].to(self._device))
                loss = nn.CrossEntropyLoss()(outputs,batch['label'].to(self._device))
                loss.backward()
                optimiser.step()
                scheduler.step()
                
    def savemodel(self,path):
        torch.save(self._model.state_dict(),path)
        
    def rank(self,query,lang=""):
        self._model.eval()
        encoding = self._tokeniser(query,return_tensors='pt',max_length=self._maxlen,padding='max_length',truncation=True)
        with torch.no_grad():
            outputs = self._model(input_ids=encoding['input_ids'].to(self._device),attention_mask=encoding['attention_mask'].to(self._device))
            return sorted([(sc.item(),self._tables[i].name) for i,sc in enumerate(outputs.flatten())],reverse=True)
        
        
if __name__ == "__main__":
    import json,random
    from pathlib import Path
    from tableinfo import TableInfo
    datadir = Path(__file__).parent.parent/"data"
    with open(datadir/"tableinfo.json","r",encoding="utf-8") as fl:
        tables = [TableInfo.fromjson(table) for table in json.load(fl)]
        
    ld = LangdetectLanguageDetector(tables)
    lid = LangidLanguageDetector(tables)
    ldres,lidres = [],[]
    for table in tables:
        for query in table.queries:
            ldres.append(table.lang==ld.lang(query))
            lidres.append(table.lang==lid.lang(query))
    
    btr = BERTTableRanker(tables)
    trainqueries = [(query,table.name) for table in tables for query in table.queries]
    random.shuffle(trainqueries)
    trainqueries,testquery = trainqueries[:100],trainqueries[100]
    btr.train(dict(trainqueries),numepochs=1,progress=False)
    btr.rank(testquery[0])
    
    print("Test passed.")