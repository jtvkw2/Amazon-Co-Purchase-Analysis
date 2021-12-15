import sys
import time
import pandas as pd
import numpy as np
import ProccesedData as prd
import queryGen as qg
import random
from neo4j import GraphDatabase
from scipy.spatial import distance
from scipy.stats import pearsonr
import matplotlib.pyplot as plt
import dataframe_image as dfi

def alt_main():
        random.seed(1)
        driver = GraphDatabase.driver('neo4j://40.77.108.181:7687', auth=('neo4j', 'amazondb'))
        algorithm_list = ['Cosine', 'Pearson', 'Jaccard']
        knownlist = ['1', '48724', '501052', '143633', '285655', '494433', '58070' , '376009']
        depth = 4
        data = []
        with driver.session() as recDB:
            for algorithm in algorithm_list:
                for input_len in range(1, 8):
                    for t in ['Random', 'Known']:
                        randomlist = []
                        for i in range(0,input_len):
                            if t == 'Random':
                                n = str(random.randint(1,30000))
                            elif t == 'Known':
                                n = knownlist[i]
                            randomlist.append(n)

                        start_time = time.time()
                        avg_sim = run_query(recDB, randomlist, depth, algorithm)
                        print(avg_sim)
                        count = round((time.time() - start_time), 2)
                        data.append([algorithm, input_len, count, t, avg_sim])
        df = pd.DataFrame(data, columns = ['Algorithm','Input Len', 'Time', 'Type', 'Average Similarity'])
        random_df = df[df['Type'] == 'Random']
        known_df = df[df['Type'] == 'Known']

        cosine_df = known_df[known_df['Algorithm'] == 'Cosine']
        pearson_df = known_df[known_df['Algorithm'] == 'Pearson']
        jaccard_df = known_df[known_df['Algorithm'] == 'Jaccard']

        print(df)
        dfi.export(random_df, 'random_dataframe.png', max_rows=-1)
        dfi.export(known_df, 'known_dataframe.png', max_rows=-1)

        #Depth Plot
        plt.plot(cosine_df['Input Len'], cosine_df['Time'], label = 'Cosine')
        plt.plot(pearson_df['Input Len'], pearson_df['Time'], label = 'Pearson')
        plt.plot(jaccard_df['Input Len'], jaccard_df['Time'], label = 'Jaccard')
        plt.xlabel('Input Len')
        plt.ylabel('Time')
        plt.legend(loc='lower right')
        plt.title('Input Len per Time per algorithm for Known List')
        plt.savefig("Input Len.jpg")
        plt.clf()


        # Average Sim
        plt.plot(cosine_df['Input Len'], cosine_df['Average Similarity'], label = 'Cosine')
        plt.plot(pearson_df['Input Len'], pearson_df['Average Similarity'], label = 'Pearson')
        plt.plot(jaccard_df['Input Len'], jaccard_df['Average Similarity'], label = 'Jaccard')
        plt.xlabel('Input Len')
        plt.ylabel('Averag')
        plt.legend(loc='lower right')
        plt.title('Average Similarity per Input Len per algorithm for Known List')
        plt.savefig("AvgSim_Len.jpg")
        plt.clf()

def main():
    random.seed(1)
    driver = GraphDatabase.driver('neo4j://40.77.108.181:7687', auth=('neo4j', 'amazondb'))
    algorithm_list = ['Cosine', 'Pearson', 'Jaccard']
    knownlist = ['1', '48724']
    data = []
    with driver.session() as recDB:
        for algorithm in algorithm_list:
            for depth in range(1, 8):
                for t in ['Random', 'Known']:
                    randomlist = []
                    for i in range(0,2):
                        if t == 'Random':
                            n = str(random.randint(1,30000))
                        elif t == 'Known':
                            n = knownlist[i]
                        randomlist.append(n)

                    start_time = time.time()
                    avg_sim = run_query(recDB, randomlist, depth, algorithm)
                    print(avg_sim)
                    count = round((time.time() - start_time), 2)
                    data.append([algorithm, depth, count, t, avg_sim])
    df = pd.DataFrame(data, columns = ['Algorithm','Depth', 'Time', 'Type', 'Average Similarity'])
    random_df = df[df['Type'] == 'Random']
    known_df = df[df['Type'] == 'Known']

    cosine_df = known_df[known_df['Algorithm'] == 'Cosine']
    pearson_df = known_df[known_df['Algorithm'] == 'Pearson']
    jaccard_df = known_df[known_df['Algorithm'] == 'Jaccard']

    print(df)
    dfi.export(random_df, 'random_dataframe.png', max_rows=-1)
    dfi.export(known_df, 'known_dataframe.png', max_rows=-1)

    #Depth Plot
    plt.plot(cosine_df['Depth'], cosine_df['Time'], label = 'Cosine')
    plt.plot(pearson_df['Depth'], pearson_df['Time'], label = 'Pearson')
    plt.plot(jaccard_df['Depth'], jaccard_df['Time'], label = 'Jaccard')
    plt.xlabel('Depth')
    plt.ylabel('Time')
    plt.legend(loc='lower right')
    plt.title('Depth per Time per algorithm for Known List')
    plt.savefig("Depth.jpg")
    plt.clf()


    # Average Sim
    plt.plot(cosine_df['Depth'], cosine_df['Average Similarity'], label = 'Cosine')
    plt.plot(pearson_df['Depth'], pearson_df['Average Similarity'], label = 'Pearson')
    plt.plot(jaccard_df['Depth'], jaccard_df['Average Similarity'], label = 'Jaccard')
    plt.xlabel('Depth')
    plt.ylabel('Averag')
    plt.legend(loc='lower right')
    plt.title('Average Similarity per Depth per algorithm for Known List')
    plt.savefig("AvgSim.jpg")
    plt.clf()




def run_query(recDB, randomlist, depth, algorithm):
    avg_sim = 0
    count = 0
    type = 'item'

    all_nodes = recDB.write_transaction(search, qg.testable_query(int(randomlist[0]), depth))
    all_nodes_id = recordToList(all_nodes, 'ids', type)
    if all_nodes_id:
        for i in range(1, len(randomlist)):
            curr_nodes = set(all_nodes_id)
            temp_nodes = recDB.write_transaction(search, qg.testable_query(int(randomlist[i]), depth))
            if temp_nodes:
                temp_list = recordToList(temp_nodes, 'ids', type)
                for n in temp_list:
                    curr_nodes.add(n)
                all_nodes_id = list(curr_nodes)
        for id in all_nodes_id:
            curr_nodes = recDB.write_transaction(search, qg.testable_query(int(id), depth))
            if curr_nodes:
                count += 1
                curr_list = recordToList(curr_nodes, 'ids', type)
                avg_sim += find_sim(all_nodes_id, curr_list, algorithm)
        if count > 0:
            avg_sim = avg_sim/count
        else:
            avg_sim = 0
    return avg_sim


def search(tx, query):
    return [record for record in tx.run(query)]

def find_sim(list1, list2, algorithm):
    if len(list1) >=100:
        list1 = list1[:100]
    if len(list2) >= 100:
        list2 = list2[:100]
    if len(list1) > len(list2):
        list2.extend(['0'] * (len(list1)-len(list2)))
    if len(list2) > len(list1):
        list1.extend(['0'] * (len(list2)-len(list1)))

    list1 = np.asarray(list1, dtype='float64')
    list2 = np.asarray(list2, dtype='float64')

    if algorithm == 'Cosine': #Cosin Sim
        return 1 - distance.cosine(list1, list2)
    elif algorithm == 'Pearson': # Pearson
        return pearsonr(list1, list2)[0]
    elif algorithm == 'Jaccard': # Jaccard
        return distance.jaccard(list1, list2)
    else:
        return 0


def recordToList(data, input, type):
    output = []
    for i in range(len(data)-1):
        if type == 'item':
            output.append(int(data[i][input]))
        else:
            output.append(data[i][input])
    return output

if __name__ == '__main__':
    alt_main()
