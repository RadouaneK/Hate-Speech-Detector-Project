import pandas as pd
import urllib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import re
from Data_prep import *
from negationClass import *
from randomArticle import *


########## 2.a Negation of attack, Toxicity and aggression ####### 
### load data
##Attack
attack_comments = pd.read_csv('attack_annotated_comments.tsv', sep = '\t', index_col = 0)
attack_annotations = pd.read_csv('attack_annotations.tsv',  sep = '\t')
## Toxicity
tox_comments = pd.read_csv('toxicity_annotated_comments.tsv', sep = '\t', index_col = 0)
tox_annotations = pd.read_csv('toxicity_annotations.tsv',  sep = '\t')
## Aggression
agg_comments = pd.read_csv('aggression_annotated_comments.tsv', sep = '\t', index_col = 0)
agg_annotations = pd.read_csv('aggression_annotations.tsv',  sep = '\t')

# labels a comment as an atack if the majority of annoatators did so
attack_labels = attack_annotations.groupby('rev_id')['attack'].mean() > 0.5
tox_labels = tox_annotations.groupby('rev_id')['toxicity'].mean() > 0.5
agg_labels = agg_annotations.groupby('rev_id')['aggression'].mean() > 0.5

# join labels and comments
attack_comments['attack'] = attack_labels
tox_comments['attack'] = tox_labels
agg_comments['attack'] = agg_labels

## take just the attack labeled sentence so to negate them:
attack=attack_comments
toxicity=tox_comments
aggression=agg_comments

### Cleaning
attack=clean_text(attack)
toxicity=clean_text(toxicity)
aggression=clean_text(aggression)

### Negating
outputs=[[attack,'negated_attack.csv'],[toxicity,'negated_toxicity.csv'],[aggression,'negated_aggression.csv']]
for output in outputs:
	with open(output[1],'w') as file:
	    for i in range(len(output[0])):
	        line=sent_negation(output[0].values[i][0])
	        file.write((line.encode('ascii','ignore')).decode('utf-8'))
	        file.write('\n')

########## 2.b Generating random sentences from Wikipedia ####### 
## it takes time to generate thousands of sentences, since it require connection for each sentence.
#number_sents=10000
#random_dataset=random_sent(number_sents)



