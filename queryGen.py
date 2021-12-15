def single_query(search_terms):
    return "MATCH (:Products {id: "+search_terms[0]+"})-[:Similar]-(o)"\
                     "RETURN DISTINCT o"

def multiple_query():
    return "CALL apoc.periodic.iterate(\"MATCH (n1:XXX) "\
            "RETURN n1\", \""\
            "WITH n1"\
            "MATCH (n2:XXX)"\
            "WHERE id(n1) <> id(n2)"\
            "WITH n1, n2, distance(n1.location,n2.location) as dist ORDER BY dist LIMIT 1"\
            "CREATE (n1)-[r:DISTANCE{dist:dist}]->(n2)\", {batchSize:1, parallel:true, concurrency:10})"

def dfs_query(id):
    return  "MATCH (a:Products{id : '"+str(id)+"'}) "\
            "WITH id(a) AS startNode "\
            "CALL gds.alpha.dfs.stream('myGraph', {startNode: startNode, maxDepth: 4}) "\
            "YIELD path "\
            "UNWIND [ n in nodes(path) | n.id ] AS ids "\
            "RETURN ids"

def dist_query(node1, node2):
    return "MATCH (p1:Products { id:'"+str(node1)+"'}),(p2:Products { id:'"+str(node2)+"'}), " \
            "p = shortestPath((p1)-[*..]-(p2)) "\
            "where p1<>p2 "\
            "RETURN length(p) as len"

def info_query(id, type):
    if type == 'item':
        return "MATCH (n:Products {id: '"+str(id)+"'})"\
               "RETURN properties(n) as prop"
    if type == 'user':
        return "MATCH (n:Customers {id: '"+str(id)+"'})"\
               "RETURN properties(n) as prop"

def find_connected(id):
    return "Match (p:Products {id: '"+str(id)+"'})-[:Reviewed]-(connected) Return connected.customer_id"

def testable_query(id,depth):
    return  "MATCH (a:Products{id : '"+str(id)+"'}) "\
            "WITH id(a) AS startNode "\
            "CALL gds.alpha.dfs.stream('myGraph', {startNode: startNode, maxDepth: "+str(depth)+"}) "\
            "YIELD path "\
            "UNWIND [ n in nodes(path) | n.id ] AS ids "\
            "RETURN ids"
