'''
This will insert the data into the PostgreSQL Database hosted on Amazon AWS.
Will use the dictionaries created in "DataProcessing.py".
Called by "main.py"

Authors:    Abnormal Distribution Team
            Chris Mims
            Sydney Yeargers
            Jacob Voyles
            Liyuan Wang
Project:    CPTS 415 Big Data Group Project
Created:    October 22, 2021
'''
import DataProcessing as dp
import re

id_list = []

def cleanStr4SQL(s):
    return s.replace("'", "`").replace("\n", " ")

def int2BoolStr(value):
    if value == 0:
        return 'False'
    else:
        return 'True'

def insert2Product(conn):
    # When inserting into database, these work quite well, I think that we need to see if 
    # there are some special characters that need to be escaped to improve flow into the
    # database without droping items. I have it outputting a text file with rejected tuples.
    # There are print statements to follow along. If you use test.txt (only 2000ish lines)
    # It isn't too bad. Only 74 items are added to the database. With only 1 dropped tuple.
    print('Inserting into product table!')
    cur = conn.cursor()
    file = open('FailedProduct.txt', 'w')
    
    for key, value in dp.asin_dict.items():
        id = key
        asin = value

        if dp.get_name(id) is None:
            continue
        id_list.append(id)
        title = dp.get_name(id)
        group = dp.get_group(id)
        rank = dp.get_rank(id)
        rate = dp.get_rating(id)

        sql_str = "INSERT INTO product (ID, ASIN, title, group_name, salesrank, avg_review_rating) " \
                  "VALUES (" + str(id) + ",'" + \
                           cleanStr4SQL(asin) + "','" + \
                           cleanStr4SQL(title) + "','" + \
                           cleanStr4SQL(group) + "'," + \
                           str(rank) + "," + \
                           str(rate) + ");"
        print(sql_str)
        try:
            cur.execute(sql_str)
        except:
            print('Failed to insert ', str(id), ' in product table')
            file.write(sql_str)
        conn.commit()
    file.close()

def insert2Similar(conn):
    print('Inserting into similar table!')
    cur = conn.cursor()
    for id in id_list:
        sim_list = dp.get_similar(id)
        if not sim_list:
            continue
        for sim in sim_list:
            sql_str = "INSERT INTO similar_products (product_id, similar_ASIN) " \
                      "VALUES (" + str(id) + ",'" + cleanStr4SQL(sim) + "');"
            print(sql_str)
            try:
                cur.execute(sql_str)
            except:
                print('Failed to insert ', str(id), ' in similar table')
            conn.commit()

def insert2Category(conn):
    print('Inserting into category table!')
    cur =conn.cursor()
    for item in dp.cat_dict.items():
        cat_item = item[1]
        cat = cat_item[0]
        head_cat = cat_item[1]
        cat_name_match = re.findall(r'.*(?=\[)', cat)
        if cat_name_match:
            cat_name = cat_name_match[0]
        else:
            cat_name = ''
        cat_num_match = re.findall(r'\[(.*)\]', cat)
        if cat_num_match:
            cat_num = cat_num_match[0]
        else:
            cat_num = -1
        hcat_num_match = re.findall(r'\[(.*)\]', head_cat)
        if hcat_num_match:
            hcat_num = hcat_num_match[0]
        else:
            hcat_num = -1    
        sql_str = "INSERT INTO category (category_id, name, head_category_id) " \
                  "VALUES (" + str(cat_num) + ",'" + cleanStr4SQL(cat_name) + "'," \
                             + str(hcat_num) + ");"
        try:
            cur.execute(sql_str)
        except:
            print('Failed to insert ', str(cat_num)), ' into category table!'
        conn.commit()

def insert2ProdCat(conn):
    print('Inserting into product category table!')
    cur = conn.cursor()
    for id in id_list:
        sub_cat_obj = dp.get_subcat(id)
        if not sub_cat_obj:
            continue
        sub_cat_list = sub_cat_obj.values()
        for item in sub_cat_list:
            sub_cat_num_match = re.findall(r'\[(.*)\]', item)
            if sub_cat_num_match:
                sub_cat_num = sub_cat_num_match[0]
            else:
                continue
            sql_str = "INSERT INTO product_categories (product_id, category_id) " \
                      "VALUES (" + str(id) + "," + str(sub_cat_num) + ");"
            try:
                cur.execute(sql_str)
            except:
                print('Failed to insert ', str(id), "'s category ", str(sub_cat_num), \
                      'to the product_categories table!')
            conn.commit()
            

def insert2Review(conn):
    print('Inserting into review table!')
    cur = conn.cursor()
    for id in id_list:
        review_obj = dp.get_reviews(id)
        if not review_obj:
            continue
        review_list = review_obj.values()
        for review in review_list:
            date = review.get('date')
            customer_id = review.get('customer')
            rating = review.get('rating')
            votes = review.get('votes')
            helpful = review.get('helpful')
            sql_str = "INSERT INTO review (date, customer_id, rating, votes, helpful) " \
                      "VALUES (%s,%s,%s,%s,%s) RETURNING review_id;"
            r_id = None
            try:
                cur.execute(sql_str, (cleanStr4SQL(date),
                                      cleanStr4SQL(customer_id),
                                      str(rating),
                                      str(votes),
                                      str(helpful)))
                r_id = str(cur.fetchone()[0])
            except:
                print('Failed to insert review for ', str(id), ' in review table!')
            conn.commit()

            new_sql = "INSERT INTO product_reviews (product_id, review_id) " \
                      "VALUES (%s,%s);"
            try:
                cur.execute(new_sql, (str(id), r_id))
            except:
                print('Failed to insert review ', r_id, ' for product ', str(id), ' in product_reviews table!')
            conn.commit()