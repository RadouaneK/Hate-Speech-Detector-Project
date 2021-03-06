
import pandas as pd
import numpy as np
from sklearn import model_selection, preprocessing, linear_model, naive_bayes, metrics, svm
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from keras.preprocessing import text, sequence
from keras import layers, models, optimizers
from sklearn.linear_model import LogisticRegression
import keras
import urllib
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score
import re
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer



print('=========================== Data Preparation =====================')

# download annotated comments and annotations for toxicity dataset:

ANNOTATED_COMMENTS_URL = 'https://ndownloader.figshare.com/files/7554634' 
ANNOTATIONS_URL = 'https://ndownloader.figshare.com/files/7554637' 


def download_file(url, fname):
    urllib.request.urlretrieve(url, fname)

                
download_file(ANNOTATED_COMMENTS_URL, 'toxicity_annotated_comments.tsv')
download_file(ANNOTATIONS_URL, 'toxicity_annotations.tsv')

# Read data files
comments = pd.read_csv('toxicity_annotated_comments.tsv', sep = '\t', index_col = 0)
annotations = pd.read_csv('toxicity_annotations.tsv',  sep = '\t')
#download word embedding vector manually using the link :
#wiki_link='https://s3-us-west-1.amazonaws.com/fasttext-vectors/wiki-news-300d-1M.vec.zip'

# labels a comment as an atack if the majority of annoatators did so
labels = annotations.groupby('rev_id')['toxicity'].mean() > 0.5
# join labels and comments
comments['toxicity'] = labels

print('=========================== Data Cleaning =====================')
# clean the text
comments['comment'] = comments['comment'].apply(lambda x: x.replace("NEWLINE_TOKEN", " "))
comments['comment'] = comments['comment'].apply(lambda x: x.replace("TAB_TOKEN", " "))
comments['comment'] = comments['comment'].apply(lambda x: x.lower())
comments['comment'] = comments['comment'].apply((lambda x: re.sub('.,[^a-zA-z0-9\s]','',x)))
comments['comment'] = comments['comment'].apply((lambda x: re.sub('[/(){}\[\]\|@,;]','',x)))
comments['comment'] = comments['comment'].apply((lambda x: re.sub(' +',' ',x)))
comments['comment'] = comments['comment'].apply((lambda x: re.sub(':',' ',x)))
comments['comment'] = comments['comment'].apply((lambda x: re.sub('`',' ',x)))
comments['comment'] = comments['comment'].apply((lambda x: re.sub('>',' ',x)))
comments['comment'] = comments['comment'].apply((lambda x: re.sub('<',' ',x)))

# keeping only training and test sets
train_comments = comments.query("split=='train'")
valid_comments = comments.query("split=='test'")

# split the dataset into training and validation datasets 
train_x, valid_x = train_comments['comment'], valid_comments['comment'], 
train_y, valid_y = train_comments['toxicity'], valid_comments['toxicity']
# label encode the target variable 
encoder = preprocessing.LabelEncoder()
train_y = encoder.fit_transform(train_y)
valid_y = encoder.fit_transform(valid_y)


print('===========================  Creating Vectorizers for data =====================')

# create a count vectorizer object 
count_vect = CountVectorizer(analyzer='word', token_pattern=r'\w{1,}')
# word level tf-idf
tfidf_vect = TfidfVectorizer(analyzer='word', token_pattern=r'\w{1,}', max_features=5000)
# ngram level tf-idf 
tfidf_vect_ngram = TfidfVectorizer(analyzer='word', token_pattern=r'\w{1,}', ngram_range=(2,3), max_features=5000)
# characters level tf-idf
tfidf_vect_ngram_chars = TfidfVectorizer(analyzer='char', token_pattern=r'\w{1,}', ngram_range=(2,3), max_features=5000)

##### Word Embedding Matrix #####

# load the pre-trained word-embedding vectors 
embeddings_index = {}
for i, line in enumerate(open('data/wiki-news-300d-1M.vec', encoding="utf8")):
    values = line.split()
    embeddings_index[values[0]] = np.asarray(values[1:], dtype='float32')

# create a tokenizer 
token = text.Tokenizer()
token.fit_on_texts(comments['comment'])
word_index = token.word_index

# convert text to sequence of tokens and pad them to ensure equal length vectors 
train_seq_x = sequence.pad_sequences(token.texts_to_sequences(train_x), maxlen=70)
valid_seq_x = sequence.pad_sequences(token.texts_to_sequences(valid_x), maxlen=70)

# create token-embedding mapping
embedding_matrix = np.zeros((len(word_index) + 1, 300))
for word, i in word_index.items():
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector
        
print('===========================  Building Pipelines for Data Classification and Prediction =====================')

print('===========================   Naive Bayes =====================')


vectorizers=[(count_vect,'count_vectorizer'),(tfidf_vect,'tfidf_vectorizer_word'),(tfidf_vect_ngram,'tfidf_vectorizer_ngram'),(tfidf_vect_ngram_chars,'tfidf_vectorizer_ngram_chars')]

######
#Naive Bayes for all features:
for vectorizer in vectorizers:
  print(vectorizer[1])
  clf = Pipeline([
    ('vect',vectorizer[0]),
    ('clf', naive_bayes.MultinomialNB()),
  ])
  clf = clf.fit(train_comments['comment'], train_comments['toxicity'])
  # show accuracy Measure
  auc = roc_auc_score(valid_comments['toxicity'], clf.predict_proba(valid_comments['comment'])[:, 1])
  print('Test ROC AUC for '+vectorizer[1]+': %.3f' %auc)
  #testing a sentence:
  print("test for sentence :  == whoa == you are a big fat idot stop spamming my userspace")
  print(clf.predict([' == whoa == you are a big fat idot stop spamming my userspace']))
  print('\n')
    

### Results:
# ===========================   Naive Bayes =====================
# count_vectorizer
# Test ROC AUC for count_vectorizer: 0.891
# test for sentence :   you are a coward and a fool.
# [ True]


# tfidf_vectorizer_word
# Test ROC AUC for tfidf_vectorizer_word: 0.953
# test for sentence :   you are a coward and a fool.
# [ True]


# tfidf_vectorizer_ngram
# Test ROC AUC for tfidf_vectorizer_ngram: 0.876
# test for sentence :   you are a coward and a fool.
# [ True]


# tfidf_vectorizer_ngram_chars
# Test ROC AUC for tfidf_vectorizer_ngram_chars: 0.925
# test for sentence :   you are a coward and a fool.
# [False]


print('===========================   Linear Classifier =====================')


# Linear Classifier Pipeline

#Linear Classifier for all features:
for vectorizer in vectorizers:
  print(vectorizer[1])
  clf = Pipeline([
    ('vect',vectorizer[0]),
    ('clf', linear_model.LogisticRegression()),
  ])
  clf = clf.fit(train_comments['comment'], train_comments['toxicity'])
  # show accuracy Measure
  auc = roc_auc_score(valid_comments['toxicity'], clf.predict_proba(valid_comments['comment'])[:, 1])
  
  print('Test ROC AUC for '+vectorizer[1]+': %.3f' %auc)
  #testing a sentence:
  print("test for sentence : == whoa == you are a big fat idot stop spamming my userspace")
  print(clf.predict(['== whoa == you are a big fat idot stop spamming my userspace']))
  print('\n')

#Results:

# Test ROC AUC for count_vectorizer: 0.953
# test for sentence :   you are a coward and a fool.
# [ True]


# tfidf_vectorizer
# Test ROC AUC for tfidf_vectorizer_word: 0.966
# test for sentence :   you are a coward and a fool.
# [ True]

# tfidf_vectorizer_ngram
# Test ROC AUC for tfidf_vectorizer_ngram: 0.882
# test for sentence :   you are a coward and a fool.
# [ True]

# tfidf_vectorizer_ngram_chars
#Test ROC AUC for tfidf_vectorizer_ngram_chars: 0.964
# test for sentence :   you are a coward and a fool.
# [ True]

print('========================= . SVM  Classifier ==================')

#### SVM on count vectors:
# SVM Classifier Pipeline
#on word count vector

clf = Pipeline([
    ('vect',count_vect),
    ('clf', svm.SVC(gamma='scale',probability=True)
),
])
#SVM SVC Classifier for all features:
for vectorizer in vectorizers:
  print(vectorizer[1])
  clf = Pipeline([
    ('vect',vectorizer[0]),
    ('clf', svm.SVC(gamma='scale',probability=True)),
  ])
  clf = clf.fit(train_comments['comment'], train_comments['toxicity'])
  # show accuracy Measure
  auc = roc_auc_score(valid_comments['toxicity'], clf.predict_proba(valid_comments['comment'])[:, 1])
  
  print('Test ROC AUC for '+vectorizer[1]+': %.3f' %auc)
  #testing a sentence:
  print("test for sentence : you are a coward and a fool")
  print(clf.predict(['you are a coward and a fool']))
  print('\n') dataset:
