import torch
from torch import nn
from transformers import BertTokenizer,BertModel
        
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

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)
    BERTClassifier("bert-base-multilingual-cased",10).to(device)
    BertTokenizer.from_pretrained("bert-base-multilingual-cased")