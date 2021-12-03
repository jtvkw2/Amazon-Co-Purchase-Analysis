import csv

titles_dict = {}
with open('title.csv', newline='') as pscfile:
    reader = csv.DictReader(pscfile)
    for row in reader:
        titles_dict[row['ID']] = row['Title']

asin_dict = {}
with open('asin.csv', newline='') as pscfile:
    reader = csv.DictReader(pscfile)
    for row in reader:
        asin_dict[row['ID']] = row['Asin']

wordList = list(titles_dict.values())

def get_asin(id):
    return asin_dict.get(int(id))

def get_name(id):
    return title_dict.get(int(id))

def get_id(val):
    for key, value in titles_dict.items():
         if val == value:
             return key

    return "There is no such Key"

def get_wordlist():
    return wordList
