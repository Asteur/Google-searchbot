# -*- coding:utf-8 -*-

import csv
import random
import time

import nltk
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer

import scrapy
from scrapy.http import Request
from scrapy.spiders import CrawlSpider, BaseSpider, Rule, Spider
from scrapy.selector import Selector

from newspaper import Article

from googlesearch.items import GoogleSearchItem
from googlesearch.user_agent import get_random_user_agent

lemmatizer = WordNetLemmatizer()


class GoogleSearchSpider(CrawlSpider):
    name = 'googlesearch'
    # queries = ('Python is', 'Java is', 'Feminism is', 'Radboud University', 'artificial intelligence', 'computer science is')
    queries = [word for word in open('input.txt').read().split('\n')]  # REPLACE INPUT FILE NAME
    priorities = {j: len(open('input.txt').read().split('\n')) - i for i,j in enumerate(queries)}
    region = 'ie'

    default_num = '10' #crawl range of google search results
    num = '' #crawl range of google search results -a num=
    search_amount = [] #crawl range of google search results

    replace = True # Skip the word replacement
    wait = False # Sleep time delays to avoid ban

    percent = '20'

    avoid = '' # Avoid input urls

    start_urls = ['https://www.google.us/search?hl=en&as_q=&as_epq={query}&num={amount}&cr=countryUS&lr=lang_en&rls=org.mozilla:en-US:official&client=firefox-a&channel=fflb']

    download_html = False
    limit_country = False

    final_dict = {}

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
        'COOKIES_ENABLED': False,
        'EXTENSIONS': {
            'scrapy.extensions.telnet.TelnetConsole': None,
        },
        'LOG_LEVEL': 'INFO',
        'LOG_ENABLED': True,
        'DOWNLOAD_TIMEOUT': 180,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,
        'CONCURRENT_REQUESTS_PER_IP': 16,
        'DUPEFILTER_CLASS':'scrapy.dupefilters.BaseDupeFilter',

        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,
        'AUTOTHROTTLE_MAX_DELAY': 180,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,

        'RETRY_TIMES': 10,

        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
            # Enable custom user-agent middleware
            'googlesearch.middleware.RotateUserAgentMiddleware': 300
        },

    }

    def start_requests(self):

        #Crawl the range of google search results ex: -a num=10(default), -a num=10-15
        if self.num == '':
            self.search_amount = [int(self.default_num)]
        else:
            try:
                self.search_amount = [int(i) for i in self.num.split('-')]
                if self.search_amount[0] < 0 or (len(self.search_amount)==2 and self.search_amount[1] < self.search_amount[0]) or (len(self.search_amount)==2 and (self.search_amount[0] < 0 or self.search_amount[1] < 0)):
                    self.search_amount = [int(self.default_num)]
            except:
                self.search_amount = [int(self.default_num)]

        for start_url in self.start_urls:
            for query in self.queries:
                url = start_url.replace('{query}', '+'.join(query.split()).strip('+')).replace('{amount}', str(self.search_amount[-1]))
                priority = self.priorities[query]
                print('URL: ', url)
                yield Request(url=url, meta={'query': query, 'priority': priority},
                                            priority = priority)

    def parse(self, response):
        # Wait all reponses ex: -a wait=False(default)/True
        if self.wait:
            time.sleep(7)

        sel = Selector(response)
        first_title = '0'
        count = 0
        links = [link for link in sel.xpath('//div[@class="r"]')]
        # Make the list from the range of google search results ex: 10, 10-15
        links = links[self.search_amount[0] - 1 if self.search_amount[0] - 1 >= 0 else 0 : self.search_amount[1]] if len(self.search_amount) == 2 else links[:self.search_amount[0]]
        # Ignore urls according to pattern ex: -a avoid=wikipedia.org,dummies.com or -a avoid=' wikipedia.org, dummies.com'

        if self.avoid:
            links = ignore_pattern(self.avoid.split(','), links)

        link_priorities = {link: response.meta['priority']*100 + len(links) - i for i, link in enumerate(links)}

        for link in links:
            name = u''.join(link.xpath(".//text()").extract())
            url = link.xpath('.//a/@href').extract()[0]

            if count == 0:
                first_title = name
                self.final_dict[name] = ''
            count += 1
            print(response.meta['query'], count)
            yield Request(url=url, callback=self.parse_item, meta={'name': name,
                                                                   'query': response.meta['query'],
                                                                   'first_title': first_title,
                                                                   'priority': link_priorities[link]},
                                                                   priority = link_priorities[link])

    def parse_item(self, response):

        name = response.meta['name']
        query = response.meta['query']
        first_title = response.meta['first_title']
        priority = response.meta['priority']
        url = response.url

        # Parse webpage
        article = Article(url)
        try:
            article.download() # sometimes failed on time out
            article.parse()

            paragraphs = article.text.split('\n')
            merged = ' '.join([p for p in paragraphs if query.lower() in p.lower()])

            tokens = nltk.word_tokenize(merged) # split into tokens
            query_tokens = [qt.lower() for qt in nltk.word_tokenize(query)] # avoid query replacement

            # Skip the word replacement -a replace=True(default)/False
            if self.replace:
                # Replace verbs, nouns, adverbs, adjectives if word is not capitalised
                replaceble_words = [word.lower() for word, pos in nltk.pos_tag(tokens)
                                    if (pos == 'RB' or pos == 'JJ') and
                                    not word[0].istitle() and word.lower() not in query_tokens]

                # Calculate the ration of words to replace
                length = len(replaceble_words)

                try:
                    self.percent = int(self.percent)
                    if self.percent < 0:
                        self.percent = 0
                    elif self.percent > 100:
                        self.percent = 100
                except:
                    self.percent = 20

                percentage = round(self.percent * length / 100)
                random_words = random.sample(replaceble_words, percentage)

                # Replace words
                replaced_text = []
                if len(random_words) > 0: # if there are words to be replaced
                    for w in tokens:
                        if w.lower() in random_words and wordnet.synsets(w.lower()):  # word in replaceble and has synonyms
                            synonyms = find_synonyms(w)
                            if len(synonyms) > 0:
                                new_w = w.lower().replace(w, synonyms[0])
                                if w.istitle():  # capitalize if original word starts with capital letter
                                    new_w = new_w.capitalize()
                                replaced_text.append(new_w)
                            else:  # if no synonyms found - return the original word
                                replaced_text.append(w)
                        else:  # if word is not in WordNet
                            replaced_text.append(w)
                else:  # return same text as original
                    replaced_text = tokens

            else:  # return same text as original
                replaced_text = tokens

            if len(replaced_text) != 0:
                self.final_dict[first_title] += join_punctuation(replaced_text) + ' '

            with open('output.csv', 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter='\t')
                for key, value in self.final_dict.items():
                    writer.writerow([key, value])

            yield GoogleSearchItem({'name': name,
                                    'url': url,
                                    'merged': join_punctuation(replaced_text),
                                    'query': query,
                                    'priority' : priority})
        except:
            yield GoogleSearchItem({'name': name,
                                    'url': url,
                                    'merged': "",
                                    'query': query,
                                    'priority' : priority})


def join_punctuation(seq, characters=".,;:?!'"):

    text = ''
    count = 0
    for nxt in seq:
        if nxt in characters or count == 0:
            text += nxt
        else:
            text += ' ' + nxt
        count += 1
    return text


def find_synonyms(word):
    """ For an input word returns synonyms from wordnet, that has the same POS as the input word. """
    synonyms = [' '.join(syn_name.split('_')) for syn in wordnet.synsets(word.lower()) for syn_name in syn.lemma_names()
                if syn_name.lower() != word.lower() and
                len(syn_name.split('_')) == 1 and
                lemmatizer.lemmatize(syn_name) != lemmatizer.lemmatize(word.lower()) and
                nltk.pos_tag([syn_name])[0][1] == nltk.pos_tag([word.lower()])[0][1]
                ]
    return synonyms

def ignore_pattern(ignored_urls, urls):
    temp_set = set()
    ignored_urls = [i.strip() for i in ignored_urls if i.strip()]
    if ignored_urls:
        for u in urls:
            for i in ignored_urls:
                if i in u.xpath('.//a/@href').extract()[0] and u not in temp_set:
                    temp_set.add(u)
        urls = [u for u in urls if u not in temp_set]
    return urls
