import re

group_dict = {}
sim_dict = {}
ratings_dict = {}
name_dict = {}
rank_dict = {}

limit = 2000 #Used for testing

def process_data(file):
    with open(file) as f:
        curr_asin = 0
        count = 0
        for line in f:
            if count == limit:
                break
            else:
                count += 1
            line = line.strip()
            check_asin = re.search(r'ASIN:\s*(\d+)',line)
            check_group = re.search(r'group:\s*(\w+)', line)
            check_similar = re.search(r'similar:\s*(\w+)',line)
            check_rate = re.search(r'avg rating:\s*(\d+)', line)
            check_name = re.search(r'title:\s*(\w+)', line)
            check_rank = re.search(r'salesrank:\s*(\d+)',line)
            if check_asin is not None:
                curr_asin = line[6:]
            if check_group is not None:
                curr_group = line[7:]
                group_dict[curr_asin] = curr_group
            if check_similar is not None:
                curr_similar = line[8:]
                sim_split = curr_similar.split()
                sim_dict[curr_asin] = [item for item in sim_split[1:]]
            if check_rate is not None:
                curr_rate = line[-3:]
                ratings_dict[curr_asin] = curr_rate
            if check_name is not None:
                curr_name = line[7:]
                name_dict[curr_asin] = curr_name
            if check_rank is not None:
                curr_rank = line[12:]
                rank_dict[curr_asin] = curr_rank



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
