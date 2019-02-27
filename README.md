## Googlesearch
Crawler is written using Python 3

## Description

The crawler googles 10 keywords, for each keyword it crawls 10 top links on google search.
On each link it takes all the paragraphs that contain the keyword.
Then it replaces 70 percent of all adjectives and adverbs with a synonym from WordNet.

## Adjustments

1. To add new POS tags (NN, VB, VBG, NNP, NNS, NNPS, VBP, VB, VBD, VBG), change this:
`replaceble_words = [word.lower() for word, pos in nltk.pos_tag(tokens)
                            if (pos == 'RB'  or pos == 'JJ') and
                            not word[0].istitle()]`
In this case you will need to check that the synonym is in the correct grammatical form (you can do conjugation using pattern package in Python)

2. To adjust the ration of words to be replaced, change this:

`percentage = round(70 * length / 100)`


## Usage

1. First you need to install all the necessary requirements:
`pip install -r requirements.txt`

It will install the following libraries:
Scrapy==1.5.0
newspaper3k==0.2.8
nltk==3.3
newspaper==0.1.0.7

2. Then add the queries in ./googlesearch/input.txt, separated by a new line

3. Then you need to run from the main directory ('./google search/'):

`scrapy crawl googlesearch`

4. In addition, you can use advanced features for the crawler:
(NO SPACES NEXT TO THE EQUAL SIGN & `-a` before each parameter)  

4.1. Change the range of Google search results - add `-a num=` parameter (default 10)

`scrapy crawl googlesearch -a num=10` - the number of responses
or
`scrapy crawl googlesearch -a num=10-15` - the range of responses

4.2. Skip word replacement - add `-a replace=` parameter True/False (default True)

`scrapy crawl googlesearch -a replace=True` - replace words
or
`scrapy crawl googlesearch -a replace=False` - don't replace words

4.3. Avoid urls - add `-a avoid=` parameter (default crawl all)

`scrapy crawl googlesearch -a avoid=wikipedia.org` - one URL
or
`scrapy crawl googlesearch -a avoid=wikipedia.org,dummies.com` - the set of URLs (no spaces)
or (if you want to put space)
`scrapy crawl googlesearch -a avoid=' wikipedia.org, dummies.com'` - the set of URLs in commas

4.4. The ration of words to be replaced - add `-a percent=` parameter (default 20)

`scrapy crawl googlesearch -a percent=70` - replace 70 percent of words

4.5. Sleep time delays to avoid ban (may help for google) - add `-a wait=` parameter True/False (default False)

`scrapy crawl googlesearch -a wait=True` - turn on sleep time
or
`scrapy crawl googlesearch -a wait=False` - turn off sleep time

4.6. Combine in any order

`scrapy crawl googlesearch -a num=2-8 -a replace=True -a avoid=' wikipedia.org, dummies.com' -a percent=70 -a wait=True`

5. The output file 'output.csv' will be saved in the main directory. To open it in excel, you need to open an empty sheet with excel (just create a blank page).
The you click File-Import-Csv file, choose the file, Delimited-"Tab"-Finish.
