import DataProcessing as dp
import InsertData as id
import psycopg2
import os


def main():
    print("Processing Data...")
    file = "amazon-meta.txt"  # just make sure .txt is in same folder as .py
    dp.process_data(file)

    engine = None
    try:
        # THIS WILL BE DIFFERENT FOR ALL OF US UNTIL THE AWS IS SET
        engine = psycopg2.connect(
            database=, user="postgres", host="localhost", password=,
            port="5432")
    except:
        print('Unable to connect to the database!')

    with open("BigDataProjectDB.sql", 'r') as file:
        sqlFile = file.read()
        file.close()
        sqlCommands = sqlFile.split(';')
        for command in sqlCommands:  
            if command != '\n':
                command += ';'
                print(command)  
                try:  
                    cur = engine.cursor()
                    cur.execute(command)
                    cur.close()
                except Exception as e:
                    print('Could not create tables!', e)
                engine.commit()

    id.insert2Product(engine)
    id.insert2Similar(engine)
    id.insert2Category(engine)
    id.insert2ProdCat(engine)
    id.insert2Review(engine)
    cur.close()
    engine.close()

    # print(set(dp.group_dict.values()))
    # yori = [[key] + val for key, val in dp.get_full_sim().items()]
    # print(list(ap(yori, min_support = 0.012, min_confidence=0.8)))


if __name__ == '__main__':
    main()
