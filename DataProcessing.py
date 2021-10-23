import re

group_dict = {}
sim_dict = {}
ratings_dict = {}
name_dict = {}
rank_dict = {}
review_dict = {}
cat_dict = {}

limit = 2000 #Used for testing

def process_data(file):
    with open(file) as f:
        curr_asin = 0
        count = 0
        num_ratings = 0
        num_cat = 0
        review_num = 0
        cat_num = 0
        for line in f:
            if count == limit:
                break
            else:
                count += 1
            line = line.strip()
            if num_ratings > 0:
                review_split = line.split()
                review = {}
                review[review_num] = {"date": review_split[0],
                                            "customer": review_split[2],
                                            "rating": review_split[4],
                                            "votes": review_split[6],
                                            "helpful": review_split[8]
                }
                review_dict[curr_asin] = review[review_num]
                review_num += 1
                num_ratings -= 1
                if num_ratings == 0:
                    review_num = 0
            if num_cat > 0:
                cat_split = line.split('|')
                cat = {}
                prev_cat = ""
                for item in cat_split[1:]:
                    cat[cat_num] = {"category": item, "head_cat": prev_cat}
                    cat_dict[curr_asin] = cat[cat_num]
                    cat_num +=1
                    prev_cat = item
                num_cat -= 1
                if num_cat == 0:
                    cat_num = 0
            check_asin = re.search(r'ASIN:\s*(\d+)',line)
            if check_asin is not None:
                curr_asin = line[6:]
                continue
            check_group = re.search(r'group:\s*(\w+)', line)
            if check_group is not None:
                curr_group = line[7:]
                group_dict[curr_asin] = curr_group
                continue
            check_similar = re.search(r'similar:\s*(\w+)',line)
            if check_similar is not None:
                curr_similar = line[8:]
                sim_split = curr_similar.split()
                sim_dict[curr_asin] = [item for item in sim_split[1:]]
                continue
            check_cat = re.search(r'categories: *(\d+)', line)
            if check_cat is not None:
                c_matches = re.findall(r'(?<=categories: )\d+', line)
                num_cat = int(c_matches[0])
                continue
            check_rate = re.search(r'avg rating:\s*(\d+)', line)
            if check_rate is not None:
                curr_rate = line[-3:]
                ratings_dict[curr_asin] = curr_rate
            check_reviews = re.search(r'total: +(\S+)', line)
            if check_reviews is not None:
                r_matches = re.findall(r'(?<=total: )\d+', line)
                num_ratings = int(r_matches[0])
                continue
            check_name = re.search(r'title:\s*(\w+)', line)
            if check_name is not None:
                curr_name = line[7:]
                name_dict[curr_asin] = curr_name
                continue
            check_rank = re.search(r'salesrank:\s*(\d+)',line)
            if check_rank is not None:
                curr_rank = line[12:]
                rank_dict[curr_asin] = curr_rank
                continue



def get_name(id):
    return name_dict.get(id)

def get_rating(id):
    return ratings_dict.get(id)

def get_group(id):
    return group_dict.get(id)

def get_rank(id):
    return rank_dict.get(id)

def get_similar(id):
    return sim_dict.get(id)

def get_full_sim():
    return sim_dict

