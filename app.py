import sys
import ProccesedData as prd
from neo4j import GraphDatabase
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
        self.current_search = []
        self.groupFilt = None
        self.itemRatingFilt = None
        self.itemReviewsFilt = None
        self.userRatingFilt = None
        self.userReviewsFilt = None

        completer = QCompleter(self.wordList, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.inputLine.setCompleter(completer)
        self.ui.errorLabel.setVisible(False)
        self.ui.addButton.clicked.connect(self.addButtonPressed)
        self.ui.itemRecButton.clicked.connect(self.itemRecButtonPressed)
        self.ui.userRecButton.clicked.connect(self.userRecButtonPressed)
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

   def itemRecButtonPressed(self):
        #check: ' if filter == "select filter": then filter = None '
        # (because of how the filter list properties are set up on the UI
        self.groupFilt = self.ui.groupList.currentText()
        self.itemRatingFilt = self.ui.minItemAvgRating.currentText()
        self.itemReviewsFilt = self.ui.itemMinReviews.text()
        itemsSortBy = self.ui.itemsSortBy #idk if you want this as a class property
        
        if len(self.current_search) == 0:
            self.ui.errorLabel.setText('Please Select Items')
            self.ui.errorLabel.setVisible(True)
            return
        if len(self.ui.algList.selectedItems()) <= 0:
            self.ui.errorLabel.setText('Select Algorithm')
            self.ui.errorLabel.setVisible(True)
            return
        query = self.getQuery()
        with self.driver.session() as recDB:
            nodes = recDB.write_transaction(self._search, query)
        for node in nodes:
            self.ui.itemRecList.append(node["o.title"])
            
            
    def userRecButtonPressed(self):
        #check: ' if filter == "select filter": then filter = None '
        # (because of how the filter list properties are set up on the UI
        self.userRatingFilt = self.ui.minUserAvgRating.currentText()
        self.userReviewsFilt = self.ui.userMinReviews.text()
        userSortBy = self.ui.userSortBy #idk if you want this as a class property

        if len(self.current_search) == 0:
            self.ui.errorLabel.setText('Please Select Items')
            self.ui.errorLabel.setVisible(True)
            return
        if len(self.ui.algList.selectedItems()) <= 0:
            self.ui.errorLabel.setText('Select Algorithm')
            self.ui.errorLabel.setVisible(True)
            return
        #FIXME: This is where output (users) should be appended to 'outputList' (in the UI) (See Above)
              
            
    '''
    THIS IS WHERE QUERIES FOR DIFFERENT ALGORITHMS GO!!!! 
    '''

    def getQuery(self):
        algorithm = self.ui.algList.selectedItems()[0].text()
        if algorithm == 'algorithm1':
            query = "MATCH (:Products {id: "+self.current_search[0]+"})-[:Similar]-(o) RETURN DISTINCT o.title LIMIT 25"
            return query
        elif algorithm == 'algorithm2':
            query = ""
            return query
        elif algorithm == 'algorithm3':
            query = ""
            return query

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


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = AmazonApp()
    window.show()
    sys.exit(app.exec_())
    window.close()



'''
class AppDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle('Recomendation Engine')
        # This is Azure Neo4j Database - Not fully complete but working
        self.driver = GraphDatabase.driver('neo4j://40.77.108.181:7687', auth=('neo4j', 'amazondb'))

        #Init Values
        self.wordList = prd.get_wordlist()
        self.current_search = []

        # Query properties
        self.search_type = None
        self.type = None
        self.low_score = 0
        self.high_score = 5
        self.category = None
        self.num_of_reviews_min = 0

        #UI
        self.initUI()

        # input field
    def initUI(self):
        fnt = QFont('Open Sans', 12)
        mainLayout = QVBoxLayout()

        # Main input Bar
        self.input = QLineEdit()
        self.input.setFixedHeight(50)
        self.input.setFont(fnt)
        self.input.editingFinished.connect(self.addEntry)
        mainLayout.addWidget(self.input)

        # AutoCompletion based on titles in database
        completer = QCompleter(self.wordList, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.input.setCompleter(completer)

        #Console Input
        self.input_console = QTextEdit()
        self.input_console.setFont(fnt)
        mainLayout.addWidget(self.input_console)

        # Search Output
        self.output_console = QTextEdit()
        self.output_console.setFont(fnt)
        mainLayout.addWidget(self.output_console)

        #Submit Button to execute query
        sub_button = QPushButton('Submit', self)
        sub_button.setToolTip('Click to Find Similar')
        sub_button.clicked.connect(self.search)
        mainLayout.addWidget(sub_button)

        #Clears all stored values and console
        clear_button = QPushButton('Clear', self)
        clear_button.setToolTip('Click to Clear All')
        clear_button.clicked.connect(self.clear)
        mainLayout.addWidget(clear_button)

        self.setLayout(mainLayout)

    #Adds entries for later query
    def addEntry(self):
        entryItem = self.input.text() #Checks incoming text

        #Verifys that title is in Database otherwise it does not submit
        if entryItem in self.wordList:
            id = prd.get_id(entryItem)
            self.current_search.append(id)
            self.input.clear()
            self.input_console.append(entryItem + "\n    ID: " + str(id) + "\n")

    #Clears all Feilds onclick
    def clear(self):
        self.input.clear()
        self.input_console.clear()
        self.output_console.clear()
        self.current_search = []
        self.properties = []

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()


    def _search(self, tx, query):
        return [record for record in tx.run(query)]

    #Search to execute query - done onclick
    def search(self):
        if len(self.current_search) == 0:
            return
        print(self.current_search[0])
        self.output_console.clear()
        # Maybe: query should include 'apoc.cypher.mapParallel' for parallel processing
        # Use https://guides.neo4j.com/sandbox/recommendations/index.html for list of queries
        query = "MATCH (:Products {id: "+self.current_search[0]+"})-[:Similar]-(o)"\
                "RETURN DISTINCT o.title LIMIT 25"

        query2 = f"""
            WITH {self.current_search} as titles
            MATCH (p1:Products)-[:Similar]->(p2:Products)
            WHERE p1.title in titles
            WITH p1, collect(p2) as p2p
            WITH collect(p2p) as allTitles
            WITH reduce(commonTitles = head(allTitles), prod in tail(allTitles) |
                apoc.coll.intersection(commonTitles, prod)) as commonTitles
            RETURN commonTitles
        """

        # Query outline to match users based on Cosign similarity
        # Users have not been input into database yet
            #MATCH (p1:User {name: 'Cynthia Freeman'})-[x:RATED]->(movie)<-[x2:RATED]-(p2:User)
            #WHERE p2 <> p1
            #WITH p1, p2, collect(x.rating) AS p1Ratings, collect(x2.rating) AS p2Ratings
            #WHERE size(p1Ratings) > 10
            #RETURN p1.name AS from,
            #       p2.name AS to,
            #       gds.alpha.similarity.cosine(p1Ratings, p2Ratings) AS similarity
            #ORDER BY similarity DESC

        # Query outline to match users based on Pearson similarity
            # MATCH (p1:User {name: 'Cynthia Freeman'})-[x:RATED]->(movie:Movie)
            # WITH p1, gds.alpha.similarity.asVector(movie, x.rating) AS p1Vector
            # MATCH (p2:User)-[x2:RATED]->(movie:Movie) WHERE p2 <> p1
            # WITH p1, p2, p1Vector, gds.alpha.similarity.asVector(movie, x2.rating) AS p2Vector
            # WHERE size(apoc.coll.intersection([v in p1Vector | v.category], [v in p2Vector | v.category])) > 10
            # RETURN p1.name AS from,
                # p2.name AS to,
                # gds.alpha.similarity.pearson(p1Vector, p2Vector, {vectorType: "maps"}) AS similarity
            # ORDER BY similarity DESC
            # LIMIT 100


        with self.driver.session() as recDB:
            nodes = recDB.write_transaction(self._search, query)
        for node in nodes:
            #print(node)
            self.output_console.append(node["o.title"])


#Runs App on Startup
app = QApplication(sys.argv)
demo = AppDemo()
demo.show()
sys.exit(app.exec_())
demo.close()
'''
