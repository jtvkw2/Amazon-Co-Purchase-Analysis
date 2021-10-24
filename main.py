#import networkx as nx
# from apyori import apriori as ap
#import numpy as np
#import matplotlib.pyplot as plt
import DataProcessing as dp
# import TestResults as tr
import InsertData as id
import psycopg2
import os


def main():
    print("Processing Data...")
    file = "/Users/chris24/Documents/WSU/Fall 2021/CPTS 415 /Project/Amazon-Co-Purchase-Analysis/test.txt"
    dp.process_data(file)

    # print("ASIN of 454888 ->", dp.get_asin('454888'))
    # print("Name of 454888 -> " + str(dp.get_name('454888')))
    # print("Rating for: 454888 -> " + str(dp.get_rating('454888')))
    # print("Group of 454888 -> " + str(dp.get_group('454888')))
    # print("Ranking of 454888 -> " + str(dp.get_rank('454888')))
    # print("Similar of 454888 -> " + str(dp.get_similar('454888')))
    # print("Subcategories of 454888 are ->", dp.get_subcat('454888'))
    # print("Reviews of 454888 -> ", dp.get_reviews('454888'))

    engine = None
    try:
        engine = psycopg2.connect(
            database="postgres",
            user = 'DBUsr',
            password = 'password',
            host = "abnormaldistributiondb.cejfw2khahqu.us-west-2.rds.amazonaws.com",
            port = '5432'
        )
    except:
        print('Unable to connect to the database!')
    cur = engine.cursor()

    with open("/Users/chris24/Documents/WSU/Fall 2021/CPTS 415 /Project/Amazon-Co-Purchase-Analysis/BigDataProjectDB.sql", 'r') as file:
        sqlFile = file.read()
        file.close()

        sqlCommands = sqlFile.split(';')

        for command in sqlCommands:    # Had to remove the alter table command for category table
            print(command)             # We will need to load in the data and then assert the
            try:                       # constraint and figure out what to do with deletion
                cur.execute(command)   # problems!
            except:
                print('Could not create tables!')
            engine.commit()

    id.insert2Product(engine)
    id.insert2Similar(engine)
    id.insert2Category(engine)
    id.insert2ProdCat(engine)
    id.insert2Review(engine)

    cur.close()
    engine.close()

    # print(set(dp.group_dict.values()))
    #yori = [[key] + val for key, val in dp.get_full_sim().items()]
    #print(list(ap(yori, min_support = 0.012, min_confidence=0.8)))

if __name__ == '__main__':
    main()
