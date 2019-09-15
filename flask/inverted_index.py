import csv
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
import re
import json
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

firebase_credentials = credentials.Certificate('../serviceAccountKey.json')

firebase = firebase_admin.initialize_app(firebase_credentials, {
'databaseURL': 'https://htn2019-e1074.firebaseio.com'
})

stopwords = set(stopwords.words('english'))

inverted_index = {}

bi_word_inverted_index = {}

def remove_stopwords(tokens):
    tokens_wo_stopwords = []
    for i in range(0,len(tokens)):
        if tokens[i].lower() not in stopwords:
            tokens_wo_stopwords.append(tokens[i].lower())
    return tokens_wo_stopwords

def get_pos_tag(token):
    pos_tag = nltk.pos_tag([token])[0][1]
    if pos_tag.startswith('N'):
        return wordnet.NOUN
    elif pos_tag.startswith('V'):
        return wordnet.VERB
    elif pos_tag.startswith('J'):
        return wordnet.ADJ
    elif pos_tag.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN

def lemmatize(tokens):
    lemmatizer = WordNetLemmatizer()
    for i in range(0,len(tokens)):
        tokens[i] = lemmatizer.lemmatize(tokens[i],pos=str(get_pos_tag(tokens[i])))
    return tokens

def add_to_inverted_index(tokens,data):
    for i in range(0,len(tokens)):
        if tokens[i] not in inverted_index:
            inverted_index[tokens[i]] = [data]
        else:
            inverted_index[tokens[i]].append(data)

def listener(event):
    value = event.data
    for key in list(value.keys()):
        for i in range(0, len(value[key]['frame_features'])):
            value[key]['frame_features'][i].pop('color', None)
            value[key]['frame_features'][i].pop('faces', None)
            value[key]['frame_features'][i].pop('image_type', None)
            value[key]['frame_features'][i].pop('metadata', None)
            value[key]['frame_features'][i].pop('request_id', None)
            value[key]['frame_features'][i]['frame_no'] = i
            if 'tags' in value[key]['frame_features'][i]:
                for tag in value[key]['frame_features'][i]['tags']:
                    add_to_inverted_index([tag['name']], {
                    'confidence': tag['confidence'],
                    'video': key,
                    'frame_no': i + 1
                    })
    save(inverted_index, 'inverted_index.json')

def search(inverted_index, word):
    print(inverted_index)
    if word in inverted_index:
        result = {}
        for doc in inverted_index[word]:
            if doc['video'] in result:
                result[doc['video']].append({
                'confidence': doc['confidence'],
                'frame_no': doc['frame_no']
                })
            else:
                result[doc['video']] = [{
                'confidence': doc['confidence'],
                'frame_no': doc['frame_no']
                }]
        return result
    return None

def save(inverted_index,filename):
    with open(filename, 'w') as file:
        json.dump(inverted_index, file)

def read_index_file(index_file_name):
    with open('./'+index_file_name,'r') as file:
        inverted_index = json.load(file)

if os.path.exists('inverted_index.json'):
    print('here')
    read_index_file('inverted_index.json')
else:
    db.reference('/').listen(listener)
