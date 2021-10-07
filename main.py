#import networkx as nx
from apyori import apriori as ap
#import numpy as np
#import matplotlib.pyplot as plt
import DataProcessing as dp


def main():
    print("Processing Data...")
    file = "amazon-meta.txt"
    dp.process_data(file)

    print("Name of 0738700797 -> " + str(dp.get_name('0738700797')))
    print("Rating for: 0738700797 -> " + str(dp.get_rating('0312199406')))
    print("Group of B000056PNB -> " + str(dp.get_group('1859677800')))
    print("Ranking of 0273651870 -> " + str(dp.get_rank('0273651870')))
    print("Similar of 0874850037 -> " + str(dp.get_similar('0874850037')))

    #yori = [[key] + val for key, val in dp.get_full_sim().items()]
    #print(list(ap(yori, min_support = 0.012, min_confidence=0.8)))

if __name__ == '__main__':
    main()
