import re

asin_dict = {}
title_dict = {}
group_dict = {}
subcat_dict = {}
rank_dict = {}
rate_dict = {}
sim_dict = {}
review_dict = {}
cat_dict = {}

# limit = 2000 #Used for testing

def process_data(file):
    with open(file) as f:
        curr_id = 0
        count = 0
        num_ratings = 0
        num_cat = 0
        review_num = 0
        total_reviews = 0
        cat_num = 0
        total_cat = 0
        for line in f:
            # if count == limit: These lines were used for testing
            #     break
            # else:
            #     count += 1
            line = line.strip()
            if num_ratings > 0:
                review_split = line.split()
                if not review_split:
                    num_ratings = 0
                    review_num = 0
                    continue
                if total_reviews == review_num:
                    review_dict[curr_id] = {}
                temp = {}
                temp = {"date": review_split[0],
                        "customer": review_split[2],
                        "rating": review_split[4],
                        "votes": review_split[6],
                        "helpful": review_split[8]}
                review_dict[curr_id].update({str(review_num): temp})
                num_ratings -= 1
                review_num += 1
                if num_ratings == 0:
                    review_num = 0
                continue    
            if num_cat > 0:
                cat_split = line.split('|')
                prev_cat = ''
                if total_cat == num_cat:
                    subcat_dict[curr_id] = {}
                for item in cat_split[1:]:
                    temp = [item, prev_cat]
                    cat_dict[cat_num] = temp
                    cat_num +=1
                    prev_cat = item
                subcat_dict[curr_id].update({str(num_cat): cat_split[-1]})
                num_cat -= 1
                if num_cat == 0:
                    cat_num = 0
                    total_cat == 0
                continue
            check_id = re.search(r'(Id):\s*(\d)', line) 
            if check_id is not None:
                id_matches = re.findall(r'(?<=Id:   )\d+', line)
                curr_id = int(id_matches[0])
                count += 1
            p_range = list(range(0, 550000, 5000))
            if (count in p_range and count != 0):
                print('Processed ', count, ' products')
                continue
            check_asin = re.search(r'(ASIN):\s*(\S+)',line)
            if check_asin is not None:
                asin_match = re.findall(r'(?<=ASIN: ).*', line)
                asin_dict[curr_id] = asin_match[0]
                continue
            check_group = re.search(r'(group):\s*(\w+)', line)
            if check_group is not None:
                curr_group = re.findall(r'(?<=group: ).*', line)[0]
                group_dict[curr_id] = curr_group
                continue
            check_similar = re.search(r'(similar):\s*(\w+)',line)
            if check_similar is not None:
                sim_num = int(re.findall(r'(?<=similar: )\d', line)[0])
                if sim_num == 0:
                    continue
                curr_similar = re.findall(r'(?<=similar: \d  ).*', line)[0]
                sim_split = curr_similar.split()
                sim_dict[curr_id] = [item for item in sim_split[1:]]
                continue
            check_cat = re.search(r'(categories): *(\d+)', line)
            if check_cat is not None:
                c_matches = re.findall(r'(?<=categories: )\d+', line)
                num_cat = int(c_matches[0])
                total_cat = num_cat
                continue
            check_rate = re.search(r'(avg rating):\s*(\d+)', line)
            if check_rate is not None:
                ar_matches = re.findall(r'(?<=avg rating: )\d?\.?\d+', line)
                curr_rate = float(ar_matches[0])
                rate_dict[curr_id] = curr_rate
            check_reviews = re.search(r'(total): +(\S+)', line)
            if check_reviews is not None:
                r_matches = re.findall(r'(?<=total: )\d+', line)
                num_ratings = int(r_matches[0])
                continue
            check_name = re.search(r'(title):\s*(\w+)', line)
            if check_name is not None:
                curr_name = re.findall(r'(?<=title: ).*', line)[0]
                title_dict[curr_id] = curr_name
                continue
            check_rank = re.search(r'(salesrank):\s*(\d+)',line)
            if check_rank is not None:
                sr_matches = re.findall(r'(?<=salesrank: )\d+', line)
                curr_rank = int(sr_matches[0])
                rank_dict[curr_id] = curr_rank
                continue


def get_asin(id):
    return asin_dict.get(int(id))

def get_name(id):
    return title_dict.get(int(id))

def get_rating(id):
    return rate_dict.get(int(id))

def get_group(id):
    return group_dict.get(int(id))

def get_rank(id):
    return rank_dict.get(int(id))

def get_similar(id):
    return sim_dict.get(int(id))

def get_full_sim():
    return sim_dict

def get_subcat(id):
    return subcat_dict.get(int(id))

def get_reviews(id):
    return review_dict.get(int(id))
