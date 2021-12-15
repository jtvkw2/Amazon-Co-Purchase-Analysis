import sys
import time
from xml.etree.ElementTree import TreeBuilder
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
from PyQt5 import uic, QtGui


qtCreatorFile = "app.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class AmazonApp(QMainWindow):
    def __init__(self):
        super(AmazonApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.reccDF = None
        self.userDF = None

        self.driver = GraphDatabase.driver('neo4j://40.77.108.181:7687', auth=('neo4j', 'amazondb'))
        self.wordList = prd.get_wordlist()
        self.current_search = ['1', '48724']
        self.itemsSortBy = None

        completer = QCompleter(self.wordList, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.inputLine.setCompleter(completer)
        self.ui.errorLabel.setVisible(False)
        self.ui.addButton.clicked.connect(self.addButtonPressed)
        self.ui.recButton.clicked.connect(partial(self.RecButtonPressed,'item'))
        self.ui.userRecButton.clicked.connect(partial(self.RecButtonPressed,'user'))
        self.ui.algList.itemSelectionChanged.connect(self.algoSelected)
        self.ui.itemClearButton.clicked.connect(self.itemClearPressed)
        self.ui.clearAllButton.clicked.connect(self.clearAllPressed)
        self.ui.recAscend.clicked.connect(partial(self.sort_df, 'itemA'))
        self.ui.userAscend.clicked.connect(partial(self.sort_df, 'userA'))
        self.ui.recDecend.clicked.connect(partial(self.sort_df, 'itemD'))
        self.ui.userDecend.clicked.connect(partial(self.sort_df, 'userD'))
        self.ui.recSort1.itemSelectionChanged.connect(partial(self.sort_df, 'item'))
        self.ui.recSort2.itemSelectionChanged.connect(partial(self.sort_df, 'item'))
        self.ui.recSort3.itemSelectionChanged.connect(partial(self.sort_df, 'item'))
        self.ui.recSort4.itemSelectionChanged.connect(partial(self.sort_df, 'item'))
        self.ui.userSort1.itemSelectionChanged.connect(partial(self.sort_df, 'user'))
        self.ui.userSort2.itemSelectionChanged.connect(partial(self.sort_df, 'user'))
        self.ui.userSort3.itemSelectionChanged.connect(partial(self.sort_df, 'user'))
        self.ui.userSort4.itemSelectionChanged.connect(partial(self.sort_df, 'user'))


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
        # if type == 'item':
        #     self.groupFilt = self.ui.groupList.currentText()
        #     self.itemRatingFilt = self.ui.minItemAvgRating.currentText()
        #     self.itemReviewsFilt = self.ui.itemMinReviews.text()
        #     self.itemsSortBy = self.ui.itemsSortBy #idk if you want this as a class property
        # elif type == 'user':
        #     #check: ' if filter == "select filter": then filter = None '
        #     # (because of how the filter list properties are set up on the UI
        #     self.userRatingFilt = self.ui.minUserAvgRating.currentText()
        #     self.userReviewsFilt = self.ui.userMinReviews.text()
        #     self.userSortBy = self.ui.userSortBy #idk if you want this as a class property
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
                        inter = curr_nodes.intersection(temp_list)
                        all_nodes_id = list(inter)

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
                    final_df.sort_values('similarity')
                    self.reccDF = final_df
                    self.outputToUI(final_df, type)
                if type == 'user':
                    final_df = pd.DataFrame(final_data, columns = ['id', 'rating', 'reviews', 'similarity'])
                    final_df.sort_values('similarity')
                    self.userDF = final_df 
                    self.outputToUI(final_df, type)
                ttlTime = time.time() - start_time
                print("--- %s seconds ---" % (ttlTime))
                if type == 'item':
                    self.ui.recTime.setPlainText(str(round(ttlTime, 4)))
                if type == 'user':
                    self.ui.userTime.setPlainText(str(round(ttlTime, 4)))


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

        if algorithm == 'cosine': #Cosine Sim
            return 1 - distance.cosine(list1, list2)
        elif algorithm == 'Pearson': # Pearson
            return pearsonr(list1, list2)
        elif algorithm == 'Jaccard': # Jaccard
            return distance.jaccard(list1, list2)
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
        for i in reversed(range(self.ui.recTable.rowCount())):
            self.ui.recTable.removeRow(i)
        current_search = []

    def outputToUI(self, df, type):
        output_df = df[df.similarity != 1.0]
        style = "::section {""background-color: #f3f3f3; }"
        if type == 'item':
            results = output_df.to_numpy()
            self.ui.recTable.horizontalHeader().setStyleSheet(style)
            self.ui.recTable.setColumnCount(len(results[0]))
            self.ui.recTable.setRowCount(len(results))
            self.ui.recTable.setHorizontalHeaderLabels(['id', 'title', 'type', 'rating', 'salesrank', 'similarity'])
            self.ui.recTable.resizeColumnsToContents()
            self.ui.recTable.setColumnWidth(0, 80)
            self.ui.recTable.setColumnWidth(1, 220)
            self.ui.recTable.setColumnWidth(2, 80)
            self.ui.recTable.setColumnWidth(3, 80)
            self.ui.recTable.setColumnWidth(4, 80)
            self.ui.recTable.setColumnWidth(5, 160)
            rowCount = 0
            colCount = 0
            for row in results:
                for colCount in range(len(results[0])):
                    temp = str(row[colCount])
                    self.ui.recTable.setItem(rowCount, colCount % 6, QTableWidgetItem(temp))
                    colCount += 1
                rowCount += 1
            # if self.groupFilt is not None and self.groupFilt !='Select group':
            #     output_df = output_df[self.groupFilt]
            # if self.itemRatingFilt is not None and self.itemRatingFilt != 'Select minimum rating':
            #     output_df = output_df[output_df['rating'] >= self.itemRatingFilt]
            # output_df = self.sort_df(output_df, type)
            # for index, row in output_df.iterrows():
            #     out_str = str(row['title']) + " \n    Similarity: " + str(row['similarity'])
            #     self.ui.outputList.append(out_str)
        elif type == 'user':
            results = output_df.to_numpy()
            self.ui.userTable.horizontalHeader().setStyleSheet(style)
            self.ui.userTable.setColumnCount(len(results[0]))
            self.ui.userTable.setRowCount(len(results))
            self.ui.userTable.setHorizontalHeaderLabels(['id', 'rating', 'reviews', 'similarity'])
            self.ui.userTable.resizeColumnsToContents()
            self.ui.userTable.setColumnWidth(0, 40)
            self.ui.userTable.setColumnWidth(1, 110)
            self.ui.userTable.setColumnWidth(2, 50)
            self.ui.userTable.setColumnWidth(3, 40)
            rowCount = 0
            colCount = 0
            for row in results:
                for colCount in range(len(results[0])):
                    temp = str(row[colCount])
                    self.ui.userTable.setItem(rowCount, colCount, QTableWidgetItem(temp))
                rowCount += 1
            # output_df = self.sort_df(output_df, type)
            # if self.userRatingFilt is not None and self.userRatingFilt != 'Select minimum rating':
            #     output_df = output_df[output_df['rating'] >= self.userRatingFilt]
            # if self.userReviewsFilt is not None:
            #     output_df = output_df[output_df['reviews'] >= self.userReviewsFilt]
            # for index, row in output_df.iterrows():
            #     out_str = str(row['id']) + " \n    Similarity: " + str(row['similarity'])
            #     self.ui.outputList.append(out_str)

    def fillResults(self, df):
        output_df = df[df.similarity != 1.0]
        style = "::section {""background-color: #f3f3f3; }"        
        self.ui.recTable.openPersistentEditor()
        self.ui.recTable.horizontalHeader().setStyleSheet(style)
        self.ui.recTable.setColumnCount(len(results[0]))
        self.ui.recTable.setRowCount(len(results))
        self.ui.recTable.setHorizontalHeaderLabels(['id', 'title', 'type', 'rating', 'salesrank', 'similarity'])
        self.ui.recTable.resizeColumnsToContents()
        self.ui.recTable.setColumnWidth(0, 80)
        self.ui.recTable.setColumnWidth(1, 220)
        self.ui.recTable.setColumnWidth(2, 80)
        self.ui.recTable.setColumnWidth(3, 80)
        self.ui.recTable.setColumnWidth(4, 80)
        self.ui.recTable.setColumnWidth(5, 160)
        rowCount = 0
        colCount = 0
        for row in results:
            for colCount in range(len(results[0])):
                temp = str(row[colCount])
                self.ui.recTable.setItem(rowCount, colCount, QTableWidgetItem(temp))
            rowCount += 1

    def fillUserResults(self, df):
        output_df = df[df.similarity != 1.0]
        style = "::section {""background-color: #f3f3f3; }"        
        results = output_df.to_numpy()
        self.ui.recTable.horizontalHeader().setStyleSheet(style)
        self.ui.recTable.setColumnCount(len(results[0]))
        self.ui.recTable.setRowCount(len(results))
        self.ui.recTable.setHorizontalHeaderLabels(['id', 'rating', 'reviews', 'similarity'])
        self.ui.recTable.resizeColumnsToContents()
        self.ui.recTable.setColumnWidth(0, 120)
        self.ui.recTable.setColumnWidth(1, 260)
        self.ui.recTable.setColumnWidth(2, 120)
        self.ui.recTable.setColumnWidth(5, 180)
        rowCount = 0
        colCount = 0
        for row in results:
            for colCount in range(len(results[0])):
                temp = str(row[colCount])
                self.ui.userTable.setItem(rowCount, colCount, QTableWidgetItem(temp))
            rowCount += 1


    def sort_df(self, typeSend):
        type = None
        updwn = None
        if typeSend == 'itemA':
            type = 'item'
            updwn = True
        if typeSend == 'userA':
            type = 'user'
            updwn = True
        if typeSend == 'itemD':
            type = 'item'
            updwn = False
        if typeSend == 'userD':
            type = 'user'
            updwn = False
        if type == 'item':
            sort1, sort2, sort3, sort4 = None, None, None, None
            rs1 = self.ui.recSort1.selectedItems()
            if rs1:
                sort1 = rs1[0].text()
            rs2 = self.ui.recSort2.selectedItems()
            if rs2:
                sort2 = rs2[0].text()
            rs3 = self.ui.recSort3.selectedItems()
            if rs3:
                sort3 = rs3[0].text()
            rs4 = self.ui.recSort4.selectedItems()
            if rs4:
                sort4 = rs4[0].text()
            sortList = []
            if sort1:
                sortList.append(sort1)
            if sort2:
                sortList.append(sort2)
            if sort3:
                sortList.append(sort3)
            if sort4:
                sortList.append(sort4)
            if len(sortList) == 1:
                if sortList[0] == 'similarity':
                    return
            if len(sortList) > 0:
                setList = set(sortList)
                sortString = "' , '".join(map(str, setList))
                sstr = "'similarity' , '" + sortString + "'"
                new_df = self.reccDF
                new_df.sort_values(by= [sstr], ascending = updwn, inplace = True)
            self.fillResults(self, new_df)
        if type == 'user':
            sort1, sort2, sort3, sort4 = None, None, None, None
            us1 = self.ui.userSort1.selectedItems()
            if us1:
                sort1 = us1[0].text()
            us2 = self.ui.userSort2.selectedItems()
            if us2:
                sort2 = us2[0].text()
            us3 = self.ui.userSort3.selectedItems()
            if us3:
                sort3 = us3[0].text()
            us4 = self.ui.userSort4.selectedItems()
            if us4:
                sort4 = us4[0].text()
            sortList = []
            if sort1:
                sortList.append(sort1)
            if sort2:
                sortList.append(sort2)
            if sort3:
                sortList.append(sort3)
            if sort4:
                sortList.append(sort4)
            if len(sortList) == 1:
                if sortList[0] == 'similarity':
                    return
            table_row = []
            for i in reversed(range(self.ui.recTable.rowCount())):
                row = self.ui.recTable.row(i)
                for item in row:
                    table_row.append(str(item))
                self.ui.recTable.removeRow(i)
            old_df = pd.DataFrame(old_table)
            old_df.columns('id', 'rating', 'reviews', 'similarity')
            if len(sortList) > 0:
                sortString = "' , '".join(map(str, sortList))
                sstr = "'" + sortString + "'"
                old_df.sort_values(by= [sstr], ascending = False, inplace = True)
            self.outputToUI(self, old_df, type)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AmazonApp()
    window.show()
    sys.exit(app.exec_())
    window.close()
