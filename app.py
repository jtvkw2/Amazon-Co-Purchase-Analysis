import sys
import time
import pandas as pd
import numpy as np
import ProccesedData as prd
import queryGen as qg
from neo4j import GraphDatabase
from functools import partial
from scipy.spatial import distance
from scipy.stats import pearsonr
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5 import uic


qtCreatorFile = "app.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class AmazonApp(QMainWindow):
    def __init__(self):
        super(AmazonApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.driver = GraphDatabase.driver('neo4j://40.77.108.181:7687', auth=('neo4j', 'amazondb'))
        self.wordList = prd.get_wordlist()
        self.current_search = ['1', '48724']
        self.groupFilt = None
        self.itemRatingFilt = None
        self.itemReviewsFilt = None
        self.userRatingFilt = None
        self.userReviewsFilt = None
        self.itemsSortBy = None

        completer = QCompleter(self.wordList, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.inputLine.setCompleter(completer)
        self.ui.errorLabel.setVisible(False)
        self.ui.addButton.clicked.connect(self.addButtonPressed)
        self.ui.itemRecButton.clicked.connect(partial(self.RecButtonPressed,'item'))
        self.ui.userRecButton.clicked.connect(partial(self.RecButtonPressed,'user'))
        self.ui.algList.itemSelectionChanged.connect(self.algoSelected)
        self.ui.itemClearButton.clicked.connect(self.itemClearPressed)
        self.ui.clearAllButton.clicked.connect(self.clearAllPressed)

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    def addButtonPressed(self):
        entryItem = self.ui.inputLine.text()
        self.ui.errorLabel.setVisible(False)
        if entryItem in self.wordList:
            id = prd.get_id(entryItem)
            self.current_search.append(id)
            self.ui.inputLine.clear()
            self.ui.inputList.append(entryItem)

    def RecButtonPressed(self, type):
        #check: ' if filter == "select filter": then filter = None '
        # (because of how the filter list properties are set up on the UI
        if type == 'item':
            self.groupFilt = self.ui.groupList.currentText()
            self.itemRatingFilt = self.ui.minItemAvgRating.currentText()
            self.itemsSortBy = self.ui.itemsSortBy #idk if you want this as a class property
        elif type == 'user':
            #check: ' if filter == "select filter": then filter = None '
            # (because of how the filter list properties are set up on the UI
            self.userRatingFilt = self.ui.minUserAvgRating.currentText()
            self.userReviewsFilt = self.ui.userMinReviews.text()
            self.userSortBy = self.ui.userSortBy #idk if you want this as a class property
        if len(self.current_search) == 0:
            self.ui.errorLabel.setText('Please Select Items')
            self.ui.errorLabel.setVisible(True)
            return
        if len(self.current_search) == 1:
            self.ui.errorLabel.setText('Please Select More Than 1 Item')
            self.ui.errorLabel.setVisible(True)
            return
        if len(self.ui.algList.selectedItems()) <= 0:
            self.ui.errorLabel.setText('Select Algorithm')
            self.ui.errorLabel.setVisible(True)
            return

        algorithm = self.ui.algList.selectedItems()[0].text()
        with self.driver.session() as recDB:
            if len(self.current_search) > 1:
                #print(self.current_search)
                start_time = time.time()
                all_nodes = recDB.write_transaction(self._search, qg.dfs_query(int(self.current_search[0])))
                all_nodes_id = self.recordToList(all_nodes, 'ids', type)
                for i in range(1, len(self.current_search)):
                    curr_nodes = set(all_nodes_id)
                    temp_nodes = recDB.write_transaction(self._search, qg.dfs_query(int(self.current_search[i])))
                    if temp_nodes:
                        temp_list = self.recordToList(temp_nodes, 'ids', type)
                        for n in temp_list:
                            curr_nodes.add(n)
                        all_nodes_id = list(curr_nodes)

                final_data = []
                for id in all_nodes_id:
                    curr_nodes = recDB.write_transaction(self._search, qg.dfs_query(int(id)))
                    if curr_nodes:
                        curr_list = self.recordToList(curr_nodes, 'ids', type)
                        curr_sim = self.find_sim(all_nodes_id, curr_list, algorithm)
                        if type == 'item':
                            item_info = recDB.write_transaction(self._search, qg.info_query(int(id), type))
                            if item_info:
                                title = item_info[0]['prop']['title']
                                group = item_info[0]['prop']['group_name']
                                avg_review_rating = item_info[0]['prop']['avg_review_rating']
                                salesrank = item_info[0]['prop']['salesrank']
                                curr_data = [id, title, group, avg_review_rating, salesrank, curr_sim]
                                final_data.append(curr_data)
                        elif type == 'user':
                            cust_nodes = recDB.write_transaction(self._search, qg.find_connected(int(id)))
                            cust_list = self.recordToList(cust_nodes, 'connected.customer_id', type)
                            for cust in cust_list:
                                user_info = recDB.write_transaction(self._search, qg.info_query(id, 'user'))
                                if user_info:
                                    print(user_info)
                                    rating = user_info[0]['prop']['rating']
                                    reviews = user_info[0]['prop']['votes']
                                    curr_data = [cust, rating, reviews, curr_sim]
                                    final_data.append(curr_data)
                if type == 'item':
                    final_df = pd.DataFrame(final_data, columns = ['id', 'title', 'type', 'rating', 'salesrank', 'similarity'])
                    self.outputToUI(final_df, type)
                if type == 'user':
                    final_df = pd.DataFrame(final_data, columns = ['id', 'rating', 'reviews', 'similarity'])
                    self.outputToUI(final_df, type)
                print("--- %s seconds ---" % (time.time() - start_time))


    def recordToList(self, data, input, type):
        output = []
        for i in range(len(data)-1):
            if type == 'item':
                output.append(int(data[i][input]))
            else:
                output.append(data[i][input])
        return output

    def find_sim(self, list1, list2, algorithm):
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

        if algorithm == 'algorithm1': #Cosin Sim
            return 1 - distance.cosine(list1, list2)
        elif algorithm == 'algorithm2': # Pearson
            return pearsonr(list1, list2)[0]
        elif algorithm == 'algorithm3': # Jaccard
            return sdistance.jaccard(list1, list2)
        else:
            return 0

    def _search(self, tx, query):
        return [record for record in tx.run(query)]

    def algoSelected(self):
        self.ui.errorLabel.setVisible(False)

    def itemClearPressed(self):
        self.ui.inputLine.clear()
        self.ui.inputList.clear()
        current_search = []

    def clearAllPressed(self):
        self.ui.inputLine.clear()
        self.ui.inputList.clear()
        self.ui.itemRecList.clear()
        current_search = []

    def outputToUI(self, df, type):
        output_df = df[df.similarity != 1.0]
        if type == 'item':
            if self.groupFilt is not None and self.groupFilt !='Select group':
                output_df = output_df[self.groupFilt]
            if self.itemRatingFilt is not None and self.itemRatingFilt != 'Select minimum rating':
                output_df = output_df[output_df['rating'] >= self.itemRatingFilt]
            output_df = self.sort_df(output_df, type)
            for index, row in output_df.iterrows():
                out_str = str(row['title']) + " \n    Similarity: " + str(row['similarity'])
                self.ui.outputList.append(out_str)
        elif type == 'user':
            output_df = self.sort_df(output_df, type)
            if self.userRatingFilt is not None and self.userRatingFilt != 'Select minimum rating':
                output_df = output_df[output_df['rating'] >= self.userRatingFilt]
            if self.userReviewsFilt is not None:
                output_df = output_df[output_df['reviews'] >= self.userReviewsFilt]
            for index, row in output_df.iterrows():
                out_str = str(row['id']) + " \n    Similarity: " + str(row['similarity'] + "\n")
                self.ui.outputList.append(out_str)

    def sort_df(self, df, type):
        if type == 'item':
            if self.itemsSortBy == 'Alphabetically A-Z':
                return df.sort_values(by = ['title'])
            elif self.itemsSortBy == 'Alphabetically Z-A':
                return df.sort_values(by=['title'], ascending = False)
            elif self.itemsSortBy == 'Average Rating':
                return df.sort_values(by = ['rating'])
            elif self.itemsSortBy == 'Salesrank':
                return df.sort_values(by = ['salesrank'])
            else:
                return df.sort_values(by = ['similarity'])
        elif type == 'user':
            if self.userSortBy == 'Alphabetically A-Z':
                return df.sort_values(by = ['id'])
            elif self.userSortBy == 'Alphabetically Z-A':
                return df.sort_values(by=['id'], ascending = False)
            elif self.userSortBy == 'Average Rating':
                return df.sort_values(by = ['rating'])
            elif self.userSortBy == 'Number of Reviews':
                return df.sort_values(by = ['rating'])
            else:
                return df.sort_values(by = ['similarity'], ascending = False)
        else:
            return df


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AmazonApp()
    window.show()
    sys.exit(app.exec_())
    window.close()
