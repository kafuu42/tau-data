# -*- coding: utf-8 -*-
"""
Created on Wed Mar 28 11:25:43 2019
@author: Taufik Sutanto
taufik@tau-data.id
https://tau-data.id

~~Perjanjian Penggunaan Materi & Codes (PPMC) - License:~~
* Modul Python dan gambar-gambar (images) yang digunakan adalah milik dari berbagai sumber sebagaimana yang telah dicantumkan dalam masing-masing license modul, caption atau watermark.
* Materi & Codes diluar point (1) (i.e. "taudata.py" ini & semua slide ".ipynb)) yang digunakan di pelatihan ini dapat digunakan untuk keperluan akademis dan kegiatan non-komersil lainnya.
* Untuk keperluan diluar point (2), maka dibutuhkan izin tertulis dari Taufik Edy Sutanto (selanjutnya disebut sebagai pengarang).
* Materi & Codes tidak boleh dipublikasikan tanpa izin dari pengarang.
* Materi & codes diberikan "as-is", tanpa warranty. Pengarang tidak bertanggung jawab atas penggunaannya diluar kegiatan resmi yang dilaksanakan pengarang.
* Dengan menggunakan materi dan codes ini berarti pengguna telah menyetujui PPMC ini.
"""

import warnings; warnings.simplefilter('ignore')
from nltk.tokenize import TweetTokenizer; Tokenizer = TweetTokenizer(reduce_len=True)
from sklearn.feature_extraction.text import CountVectorizer
from textblob import TextBlob
from bs4 import BeautifulSoup as bs
from sklearn.decomposition import LatentDirichletAllocation as LDA
import re, networkx as nx, matplotlib.pyplot as plt, operator, numpy as np, os, csv, community
from twython import Twython, TwythonRateLimitError
import json, pandas as pd, itertools, time
from html import unescape
from nltk import sent_tokenize
from unidecode import unidecode
from tqdm import tqdm, trange
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from geopy.geocoders import Yandex; geolocator = Yandex(lang='en_US')
from twython import TwythonStreamer


def streamTwitter(topicS, lang, fileHasil, maxTweet, Ck, Cs, At, As):
    f = open(fileHasil, 'w')
    class MyStreamer(TwythonStreamer):
        def on_success(self, data):
            global count
            f.write(json.dumps(data)+'\n')
            count+=1;print("\rNbr of Tweets captured: {}".format(count), end="")
            if count==maxTweet:
                print('\nFinished Recording %.0f tweets' %(maxTweet)); self.disconnect()
        def on_error(self, status_code, data):
            print('Error Status = %s' %status_code); self.disconnect()

    print('Start Streaming Data, Please Wait ... ')
    while count<maxTweet:
        stream = MyStreamer(Ck, Cs, At, As)
        stream.statuses.filter(track=topicS)
    f.close()
    print('Finished, file saved to: ', fileHasil)

def twitter_html2csv(fData, fHasil):
    urlPattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    print('Loading Data: ', flush = True)
    Tweets, Username, waktu, replies, retweets, likes, Language, urlStatus =  [], [], [], [], [], [], [], []
    soup = bs(open(fData,encoding='utf-8', errors = 'ignore', mode='r'),'html.parser')
    data = soup.find_all('li', class_= 'stream-item')
    for i,t in tqdm(enumerate(data)):
        T = t.find_all('p',class_='TweetTextSize')[0] # Loading tweet
        Tweets.append(bs(str(T),'html.parser').text)
        U = t.find_all('span',class_='username')
        Username.append(bs(str(U[0]),'html.parser').text)
        T = t.find_all('a',class_='tweet-timestamp')[0]# Loading Time
        waktu.append(bs(str(T),'html.parser').text)
        RP = t.find_all('span',class_='ProfileTweet-actionCountForAria')[0]# Loading reply, retweet & Likes
        replies.append(int((bs(str(RP), "lxml").text.split()[0]).replace('.','').replace(',','')))
        RT = t.find_all('span',class_='ProfileTweet-actionCountForAria')[1]
        RT = int((bs(str(RT), "lxml").text.split()[0]).replace('.','').replace(',',''))
        retweets.append(RT)
        L  = t.find_all('span',class_='ProfileTweet-actionCountForAria')[2]
        likes.append(int((bs(str(L), "lxml").text.split()[0]).replace('.','').replace(',','')))
        try:# Loading Bahasa
            L = t.find_all('span',class_='tweet-language')
            Language.append(bs(str(L[0]), "lxml").text)
        except:
            Language.append('')
        url = str(t.find_all('small',class_='time')[0])
        try:
            url = re.findall(urlPattern,url)[0]
        except:
            try:
                mulai, akhir = url.find('href="/')+len('href="/'), url.find('" title=')
                url = 'https://twitter.com/' + url[mulai:akhir]
            except:
                url = ''
        urlStatus.append(url)
    print('Saving Data to "%s" ' %fHasil, flush = True)
    dfile = open(fHasil, 'w', encoding='utf-8', newline='')
    dfile.write('Time, Username, Tweet, Replies, Retweets, Likes, Language, urlStatus\n')
    with dfile:
        writer = csv.writer(dfile)
        for i,t in enumerate(Tweets):
            writer.writerow([waktu[i],Username[i],t,replies[i],retweets[i],likes[i],Language[i],urlStatus[i]])
    dfile.close()
    print('All Finished', flush = True)

def twitter_connect(Ck, Cs, At, As):
    try:
        twitter = Twython(Ck, Cs, At, As)
        user = twitter.verify_credentials()
        print('Welcome "%s" you are now connected to twitter server' %user['name'])
        return twitter
    except:
        print("Connection failed, please check your API keys or connection")
        
def twitter_connect2(id_=0):
    if id_ == 11:
        Ck = 'F74Vecnd3NLbs3dcFnbnMYrAB'
        Cs = '1l7pEWdN9TdYz5FC2Ban9LjgTAiioqJEk5H4dqBitGYasGzAhX'
        At = '2214118411-6Uemjx0DtUIgyYDZBpcXpini9p9UxZCeHx489Qt'
        As = 'fXArJ8hPbD2TXW8stF8kWCwMh321euPx97HvS4Lb6mSQF'
    elif id_==12:
        Ck = 'gYuM7dXtw2TbzPYSQOCp37cgm'
        Cs = 'jSEFVIQN7zSrE5jzyBDJoDup630WWZZeNWYUW8kJ6QXzY22xAd'
        At = '2214118411-IpDBJa7y3tG5Ve5pmaj9qt6ua8cgu60lp3pTmK7'
        As = 'Q9sLFX8FSLaRZBaVqJJYeLbrKE4NksJKb0DRSuhp48x9e'
    elif id_==13:
        Ck = 'tGWVzZ6fpP7YbjsecrMwBWgCC'
        Cs = '7V3EhVafpsnORX9AqFJBH9J9qptjc7eQSjOn9jn869NfYpKCVc'
        At = '2214118411-XXclCrcEH5G66gXCt7bZiEI0Zmv5cvXsK1xxt0R'
        As = 'tjzOxA78cOxJcA3dGs0BE7tAZG0VOnVVizHxW6qPBhN97'
    elif id_==14:
        Ck = 'gSkWEs0G5sRiwUi69RSOdhNQZ'
        Cs = 'n5iJsw4dK89u5BA3fXk2Zc5k6rhUm9JjTUxeDymIujKAjjWioK'
        At = '2214118411-nCBaWVU20Y7Q89X3eHAjiG9OGv7whSnbhHByYRb'
        As = 'SfuaHaeKAD2dk6xKuMCuOho781v7L4HOekqWhNnt5Ucyv'
    elif id_==15:
        Ck = 'rxdGBPxLO4u88rWOSY4cyQH3d'
        Cs = 'dkrUTiviKdcrp95gPBFkwGI9AmHB1Kxo7S7oRkfYKw7ADAWaz8'
        At = '2214118411-IyChkDouq0PEGBoxlbx4gf4oyQHiQXOCsSla7hW'
        As = 'RJtAs4hxOMv2IE2SxsO58EFhv9P7Y5JICNktzIMgjkF3a'
    elif id_==16:
        Ck = 'fgcmWgt48KfEm93vtsEBqyFAr'
        Cs = 'MdLQrEh3LL2g3lFIIeZ0qIfG1PH8qzGHjHKmeceoItPYw0JkoE'
        At = '2214118411-zalXyYnx7hItb40QIMVlXBOvH3scDYiMsXjxuQ7'
        As = 'aAIOm4YrjMqYbDZkMpviwgeg1KjVIvM6pJpKdq4gx21rx'
    else:
        return None
    try:
        twitter = Twython(Ck, Cs, At, As)
        user = twitter.verify_credentials()
        print('Welcome "%s" you are now connected to twitter server' %user['name'])
        return twitter, Ck, Cs, At, As
    except:
        print("Connection failed, please check your API keys or connection")

def getTweets(twitter, topic, N = 100, lan = None):
    Tweets, MAX_ATTEMPTS, count, dBreak, next_max_id = [], 3, 0, False, 0
    for i in range(MAX_ATTEMPTS):
        if(count>=N or dBreak):
            print('\nFinished importing %.0f' %count);break
        if(i == 0):
            if lan:
                results=twitter.search(q=topic, lang=lan, count=100, tweet_mode = 'extended')
            else:
                results=twitter.search(q=topic, count=100, tweet_mode = 'extended')

            Tweets.extend(results['statuses'])
            count += len(results['statuses'])
            if count>N:
                print("\rNbr of Tweets captured: {}".format(N), end="")
                Tweets = Tweets[:N]
                dBreak = True; break
            else:
                print("\rNbr of Tweets captured: {}".format(count), end="")

        else:
            try:
                if lan:
                    results=twitter.search(q=topic,include_entities='true',max_id=next_max_id, lang=lan, count=100, tweet_mode = 'extended')
                else:
                    results=twitter.search(q=topic,include_entities='true',max_id=next_max_id, count=100, tweet_mode = 'extended')

                Tweets.extend(results['statuses'])
                count += len(results['statuses'])
                if count>N:
                    print("\rNbr of Tweets captured: {}".format(N), end="")
                    Tweets = Tweets[:N]
                    dBreak = True; break
                else:
                    print("\rNbr of Tweets captured: {}".format(count), end="")

                try:
                    next_results_url_params=results['search_metadata']['next_results']
                    next_max_id=next_results_url_params.split('max_id=')[1].split('&')[0]
                except:
                    print('\nFinished, no more tweets available for query "%s"' %str(topic), flush = True)
                    dBreak = True; break

            except TwythonRateLimitError:
                print('\nRate Limit reached ... sleeping for 15 Minutes', flush = True)
                for itr in trange(15*60):
                    time.sleep(1)
            except:
                print('\nSomething is not right, retrying ... (attempt = {}/{})'.format(i+1,MAX_ATTEMPTS), flush = True)
    return Tweets

def saveTweets(Tweets,file='Tweets.json', plain = False): #in Json Format
    with open(file, 'w') as f:
        for T in Tweets:
            if plain:
                f.write(T+'\n')
            else:
                try:
                    f.write(json.dumps(T)+'\n')
                except:
                    pass

def loadTweets(file='Tweets.json'):
    f=open(file,encoding='utf-8', errors ='ignore', mode='r');T=f.readlines();f.close()
    for i,t in enumerate(T):
        T[i] = json.loads(t.strip())
    return T

def crawlFiles(dPath,types=None): # dPath ='C:/Temp/', types = 'pdf'
    if types:
        return [dPath+f for f in os.listdir(dPath) if f.endswith('.'+types)]
    else:
        return [dPath+f for f in os.listdir(dPath)]

def LoadDocuments(dPath=None,types=None, file = None): # types = ['pdf','doc','docx','txt','bz2']
    Files, Docs = [], []
    if types:
        for tipe in types:
            Files += crawlFiles(dPath,tipe)
    if file:
        Files = [file]
    if not types and not file: # get all files regardless of their extensions
        Files += crawlFiles(dPath)
    for f in Files:
        if f[-3:].lower() in ['txt', 'dic','py', 'ipynb']:
            try:
                df=open(f,"r",encoding="utf-8", errors='replace')
                Docs.append(df.readlines());df.close()
            except:
                print('error reading{0}'.format(f))
        elif f[-3:].lower()=='csv':
            Docs.append(pd.read_csv(f))
        else:
            print('Unsupported format {0}'.format(f))
    if file:
        Docs = Docs[0]
    return Docs, Files

def LoadStopWords(lang='en'):
    L = lang.lower().strip()
    if L == 'en' or L == 'english' or L == 'inggris':
        from spacy.lang.en import English as lemmatizer
        #lemmatizer = spacy.lang.en.English
        lemmatizer = lemmatizer()
        #lemmatizer = spacy.load('en')
        stops =  set([t.strip() for t in LoadDocuments(file = 'data/stopwords_eng.txt')[0]])
    elif L == 'id' or L == 'indonesia' or L=='indonesian':
        from spacy.lang.id import Indonesian
        #lemmatizer = spacy.lang.id.Indonesian
        lemmatizer = Indonesian()
        stops = set([t.strip() for t in LoadDocuments(file = 'data/stopwords_id.txt')[0]])
    else:
        print('Warning, language not recognized. Empty StopWords Given')
        stops = set(); lemmatizer = None
    return stops, lemmatizer

def cleanText(T, fix={}, lemma=None, stops = set(), symbols_remove = True, min_charLen = 2, fixTag= True):
    # lang & stopS only 2 options : 'en' atau 'id'
    # symbols ASCII atau alnum
    pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    t = re.sub(pattern,' ',T) #remove urls if any
    pattern = re.compile(r'ftp[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    t = re.sub(pattern,' ',t) #remove urls if any
    t = unescape(t) # html entities fix
    if fixTag:
        t = fixTags(t) # fix abcDef
    t = t.lower().strip() # lowercase
    t = unidecode(t)
    t = ''.join(''.join(s)[:2] for _, s in itertools.groupby(t)) # remove repetition
    t = t.replace('\n', ' ').replace('\r', ' ')
    t = sent_tokenize(t) # sentence segmentation. String to list
    for i, K in enumerate(t):
        if symbols_remove:
            K = re.sub(r'[^.,_a-zA-Z0-9 \.]',' ',K)
        if lemma:
            listKata = lemma(K)
        else:
            listKata = TextBlob(K).words
        cleanList = []
        for token in listKata:
            if lemma:
                if str(token.text) in fix.keys():
                    token = fix[str(token.text)]
                try:
                    token = token.lemma_
                except:
                    token = lemma(token)[0].lemma_
            else:
                if str(token) in fix.keys():
                    token = fix[str(token)]
            if stops:
                if len(token)>=min_charLen and token not in stops:
                    cleanList.append(token)
            else:
                if len(token)>=min_charLen:
                    cleanList.append(token)
        t[i] = ' '.join(cleanList)
    return ' '.join(t) # Return kalimat lagi

def strip_non_ascii(string,symbols):
    ''' Returns the string without non ASCII characters''' #isascii = lambda s: len(s) == len(s.encode())
    stripped = (c for c in string if 0 < ord(c) < 127 and c not in symbols)
    return ''.join(stripped)

def adaAngka(s):
    return any(i.isdigit() for i in s)

def fixTags(t):
    getHashtags = re.compile(r"#(\w+)")
    pisahtags = re.compile(r'[A-Z][^A-Z]*')
    tagS = re.findall(getHashtags, t)
    for tag in tagS:
        if len(tag)>0:
            tg = tag[0].upper()+tag[1:]
            proper_words = []
            if adaAngka(tg):
                tag2 = re.split('(\d+)',tg)
                tag2 = [w for w in tag2 if len(w)>0]
                for w in tag2:
                    try:
                        _ = int(w)
                        proper_words.append(w)
                    except:
                        w = w[0].upper()+w[1:]
                        proper_words = proper_words+re.findall(pisahtags, w)
            else:
                proper_words = re.findall(pisahtags, tg)
            proper_words = ' '.join(proper_words)
            t = t.replace('#'+tag, proper_words)
    return t

def cleanTweets(Tweets):
    factory = StopWordRemoverFactory(); stopwords = set(factory.get_stop_words()+['twitter','rt','pic','com','yg','ga','https'])
    factory = StemmerFactory(); stemmer = factory.create_stemmer()
    for i,tweet in enumerate(tqdm(Tweets)):
        txt = tweet['fullTxt'] # if you want to ignore retweets  ==> if not re.match(r'^RT.*', txt):
        txt = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',' ',txt)# clean urls
        txt = txt.lower() # Lowercase
        txt = Tokenizer.tokenize(txt)
        symbols = set(['@']) # Add more if you want
        txt = [strip_non_ascii(t,symbols) for t in txt] #remove all non ASCII characters
        txt = ' '.join([t for t in txt if len(t)>1])
        Tweets[i]['cleanTxt'] = txt # this is not a good Python practice, only for learning.
        txt = stemmer.stem(txt).split()
        Tweets[i]['nlp'] = ' '.join([t for t in txt if t not in stopwords])
    return Tweets

def translate(txt, language='en'): # txt is a TextBlob object
    try:
        return txt.translate(to=language)
    except:
        return txt

"""
def sentiment(D, tweets = None): #need a clean tweets
    print("Calculating Sentiment and Subjectivity Score: ... ")
    if tweets:
        Z = [t['full_text'] for t in tweets]
    else:
        Z = D
    T = [] # T = [SenSubModMood_ID(t) for t in tqdm(D)]
    for t in tqdm(D):
        try:
            T.append(SenSubModMood_ID(t))
            time.sleep(0.1)
        except:
            pass
    pol = [t[0] for t in T]
    sub = [t[1] for t in T]
    mod = [t[2] for t in T]
    mood = [t[3] for t in T]
    label_se = ['Positif','Negatif', 'Netral']
    score_se = [len([True for t in pol[0] if t=='pos']),len([True for t in pol[0] if t=='neg']),len([True for t in pol[0] if t=='net'])]
    PieChart(score_se,label_se)
    label_su = ['Subjektif','Objektif']
    score_su = [len([True for t in sub[0] if t=='sub']),len([True for t in sub[0] if t=='obj'])]
    PieChart(score_su,label_su)
    label_mod = ['Yakin', 'Ragu']
    score_mod = [len([True for t in mod[0] if t=='Yakin']), len([True for t in mod[0] if t=='Ragu'])]
    PieChart(score_mod,label_mod)
    lblMood = list(set(mood))
    score_mood = [len([True for t in mood if t==label]) for label in lblMood]
    PieChart(score_mood,lblMood)
    pol = [t[1] for t in pol]
    Sen = [(s,t) for s,t in zip(pol,Z)]
    Sen.sort(key=lambda tup: tup[0])
    sub = [s[1] for s in sub]
    Sub = [(s,t) for s,t in zip(sub,Z)]
    Sub.sort(key=lambda tup: tup[0])
    mod = [m[1] for m in mod]
    Mod = [(s,t) for s,t in zip(mod,Z)]
    Mod.sort(key=lambda tup: tup[0])

    return Sen, Sub, Mod, mood
"""

def sentiment(Tweets): #need a clean tweets
    print("Calculating Sentiment and Subjectivity Score: ... ")
    T = [translate(TextBlob(tweet['full_text'])) for tweet in tqdm(Tweets)]
    Sen = [tweet.sentiment.polarity for tweet in tqdm(T)]
    Sub = [float(tweet.sentiment.subjectivity) for tweet in tqdm(T)]
    Se, Su = [], []
    for score_se, score_su in zip(Sen,Sub):
        if score_se>0.1:
            Se.append('pos')
        elif score_se<-0.05: #I prefer this
            Se.append('neg')
        else:
            Se.append('net')
        if score_su>0.5:
            Su.append('Subjektif')
        else:
            Su.append('Objektif')
    label_se = ['Positif','Negatif', 'Netral']
    score_se = [len([True for t in Se if t=='pos']),len([True for t in Se if t=='neg']),len([True for t in Se if t=='net'])]
    label_su = ['Subjektif','Objektif']
    score_su = [len([True for t in Su if t=='Subjektif']),len([True for t in Su if t=='Objektif'])]
    PieChart(score_se,label_se); PieChart(score_su,label_su)
    Sen = [(s,t['full_text']) for s,t in zip(Sen,Tweets)]
    Sen.sort(key=lambda tup: tup[0])
    Sub = [(s,t['full_text']) for s,t in zip(Sub,Tweets)]
    Sub.sort(key=lambda tup: tup[0])
    return (Sen, Sub)

def printSA(SA, N = 2, emo = 'positif'):
    Sen, Sub = SA
    e = emo.lower().strip()
    if e=='positif' or e=='positive':
        tweets = Sen[-N:]
    elif e=='negatif' or e=='negative':
        tweets = Sen[:N]
    elif e=='netral' or e=='neutral':
        net = [(abs(score),t) for score,t in Sen if abs(score)<0.01]
        net.sort(key=lambda tup: tup[0])
        tweets = net[:N]
    elif e=='subjektif' or e=='subjective':
        tweets = Sub[-N:]
    elif e=='objektif' or e=='objective':
        tweets = Sub[:N]
    else:
        print('Wrong function input parameter = "{0}"'.format(emo)); tweets=[]
    print('"{0}" Tweets = '.format(emo))
    for t in tweets:
        print(t)

def PieChart(score,labels):
    fig1 = plt.figure(); fig1.add_subplot(111)
    plt.pie(score, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal');plt.show()
    return None

def drawGraph(G, Label, layOut='spring', graphStyle=False, K = 200):
    #fig3 = plt.figure(); fig3.add_subplot(111)
    if graphStyle:
        ranking = nx.degree_centrality(G)
        warna = list(ranking.values())
        d = nx.degree(G)
        d = [d[node]*K for node in G.nodes()]
        pos = nx.spring_layout(G) # Spring LayOut
        nx.draw_networkx_nodes(G,pos, node_color=warna,node_size=d) # Gambar Vertex
        nx.draw_networkx_edges(G,pos,width=2,alpha=0.1) # Gambar edges
        nx.draw_networkx_labels(G,pos) #Gambar Label Nodes
        plt.show() # Show the graph
    else:
        if layOut.lower()=='spring':
            pos = nx.spring_layout(G)
        elif layOut.lower()=='circular':
            pos=nx.circular_layout(G)
        elif layOut.lower()=='random':
            pos = nx.random_layout(G)
        elif layOut.lower()=='shells':
            shells = [G.core_nodes,sorted(G.major_building_routers, key=lambda n: nx.degree(G.topo, n)) + G.distribution_routers + G.server_nodes,G.hosts + G.minor_building_routers]
            pos = nx.shell_layout(G, shells)
        elif layOut.lower()=='spectral':
            pos=nx.spectral_layout(G)
        else:
            print('Graph Type is not available.')
            return
        nx.draw_networkx_nodes(G,pos, alpha=0.2,node_color='blue',node_size=600)
        if Label:
            nx.draw_networkx_labels(G,pos)
        nx.draw_networkx_edges(G,pos,width=4)
        plt.show()

def Graph(Tweets, Label = False, layOut='spring'): # Need the Tweets Before cleaning
    print("Please wait, building Graph .... ")
    G=nx.Graph()
    for tweet in tqdm(Tweets):
        if tweet['user']['screen_name'] not in G.nodes():
            G.add_node(tweet['user']['screen_name'])
        mentionS =  re.findall("@([a-zA-Z0-9]{1,15})", tweet['full_text'])
        for mention in mentionS:
            if "." not in mention: #skipping emails
                usr = mention.replace("@",'').strip()
                if usr not in G.nodes():
                    G.add_node(usr)
                G.add_edge(tweet['user']['screen_name'],usr)
    Nn, Ne = G.number_of_nodes(), G.number_of_edges()
    drawGraph(G, Label, layOut)
    print('Finished. There are %d nodes and %d edges in the Graph.' %(Nn,Ne))
    return G

def Centrality(G, N=10, method='katz', outliers=False, Label = True, layOut='shells'):

    if method.lower()=='katz':
        phi = 1.618033988749895 # largest eigenvalue of adj matrix
        ranking = nx.katz_centrality_numpy(G,1/phi)
    elif method.lower() == 'degree':
        ranking = nx.degree_centrality(G)
    elif method.lower() == 'eigen':
        ranking = nx.eigenvector_centrality_numpy(G)
    elif method.lower() =='closeness':
        ranking = nx.closeness_centrality(G)
    elif method.lower() =='betweeness':
        ranking = nx.betweenness_centrality(G)
    elif method.lower() =='harmonic':
        ranking = nx.harmonic_centrality(G)
    elif method.lower() =='percolation':
        ranking = nx.percolation_centrality(G)
    else:
        print('Error, Unsupported Method.'); return None

    important_nodes = sorted(ranking.items(), key=operator.itemgetter(1))[::-1]#[0:Nimportant]
    data = np.array([n[1] for n in important_nodes])
    dnodes = [n[0] for n in important_nodes][:N]
    if outliers:
        m = 1 # 1 standard Deviation CI
        data = data[:N]
        out = len(data[abs(data - np.mean(data)) > m * np.std(data)]) # outlier within m stDev interval
        if out<N:
            dnodes = [n for n in dnodes[:out]]

    print('Influencial Users: {0}'.format(str(dnodes)))
    print('Influencial Users Scores: {0}'.format(str(data[:len(dnodes)])))
    Gt = G.subgraph(dnodes)
    return Gt

def Community(G):
    part = community.best_partition(G)
    values = [part.get(node) for node in G.nodes()]
    mod, k = community.modularity(part,G), len(set(part.values()))
    print("Number of Communities = %d\nNetwork modularity = %.2f" %(k,mod)) # https://en.wikipedia.org/wiki/Modularity_%28networks%29
    fig2 = plt.figure(); fig2.add_subplot(111)
    nx.draw_shell(G, cmap = plt.get_cmap('gist_ncar'), node_color = values, node_size=30, with_labels=False)
    plt.show
    return values

def print_Topics(model, feature_names, Top_Topics, n_top_words):
    for topic_idx, topic in enumerate(model.components_[:Top_Topics]):
        print("Topic #%d:" %(topic_idx+1))
        print(" ".join([feature_names[i]
                        for i in topic.argsort()[:-n_top_words - 1:-1]]))

def getTopics(Txt,n_topics=5, Top_Words=7):
    tf_vectorizer = CountVectorizer(strip_accents = 'unicode', token_pattern = r'\b[a-zA-Z]{3,}\b', max_df = 0.95, min_df = 2)
    dtm_tf = tf_vectorizer.fit_transform(Txt)
    tf_terms = tf_vectorizer.get_feature_names()
    lda_tf = LDA(n_components=n_topics, learning_method='online', random_state=0).fit(dtm_tf)
    vsm_topics = lda_tf.transform(dtm_tf); doc_topic =  [a.argmax()+1 for a in tqdm(vsm_topics)] # topic of docs
    print('In total there are {0} major topics, distributed as follows'.format(len(set(doc_topic))))
    fig4 = plt.figure(); fig4.add_subplot(111)
    plt.hist(np.array(doc_topic), alpha=0.5); plt.show()
    print('Printing top {0} Topics, with top {1} Words:'.format(n_topics, Top_Words))
    print_Topics(lda_tf, tf_terms, n_topics, Top_Words)
    return lda_tf, dtm_tf, tf_vectorizer

def get_nMax(arr, n):
    indices = arr.ravel().argsort()[-n:]
    indices = (np.unravel_index(i, arr.shape) for i in indices)
    return [(arr[i], i) for i in indices]

def filter_for_tags(tagged, tags=['NN', 'JJ', 'NNP']):
    return [item for item in tagged if item[1] in tags]

def normalize(tagged):
    return [(item[0].replace('.', ''), item[1]) for item in tagged]

def unique_everseen(iterable, key=None):
    "List unique elements, preserving order. Remember all elements ever seen."
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in itertools.ifilterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element

def lDistance(firstString, secondString):
    "Function to find the Levenshtein distance between two words/sentences - gotten from http://rosettacode.org/wiki/Levenshtein_distance#Python"
    if len(firstString) > len(secondString):
        firstString, secondString = secondString, firstString
    distances = range(len(firstString) + 1)
    for index2, char2 in enumerate(secondString):
        newDistances = [index2 + 1]
        for index1, char1 in enumerate(firstString):
            if char1 == char2:
                newDistances.append(distances[index1])
            else:
                newDistances.append(1 + min((distances[index1], distances[index1+1], newDistances[-1])))
        distances = newDistances
    return distances[-1]

def buildGraph(nodes):
    "nodes - list of hashables that represents the nodes of the graph"
    gr = nx.Graph() #initialize an undirected graph
    gr.add_nodes_from(nodes)
    nodePairs = list(itertools.combinations(nodes, 2))

    #add edges to the graph (weighted by Levenshtein distance)
    for pair in nodePairs:
        firstString = pair[0]
        secondString = pair[1]
        levDistance = lDistance(firstString, secondString)
        gr.add_edge(firstString, secondString, weight=levDistance)

    return gr