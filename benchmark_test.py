from timeit import default_timer as timer
import pandas as pd
import pytest
import random
from DbHelper import lst2pgarr, lst2pgarrexplicit

# Load the test rows CSV file into a pandas DataFrame
df = pd.read_csv("test_data/10k_rows.csv", header=None)
# number of vectors to search for
sample_size = 1000

# create multiple sets params for vector search, this will spawn multiple tests
number_of_tests = 1
test_cases = []
for i in range(number_of_tests):
    # Generate a random sample from the 10k rows
    random_indices = random.sample(range(len(df)), sample_size)
    df_random = df.iloc[random_indices]
    test_cases.append(df_random)

@pytest.mark.parametrize("search_vectors", test_cases)
def test_query_performance(postgresql, search_vectors):
    # Open a cursor to perform database operations
    cur = postgresql.cursor()
    getCountVectors(cur)

    rows = []
    for r in search_vectors.itertuples(index=False):
        rows.append(lst2pgarr(r))
    
    # Execute a sample query and measure its execution time
    start_time = timer()
    query = getQuery(rows)
    #print(query)
    cur.execute(query)

    print('Search vector:')
    print('\n')
    print(rows[0])
    print('\n')

    end_time = timer()
    query_time = end_time - start_time

    results = cur.fetchall()

    # Assert that the query returns the expected results
    # assert len(results) == 10  
    print(f'Search query for %s vectors completed in %s seconds' % (len(rows), query_time))
    print('\n')
    print('Query result:')
    print('(id, distance)')
    for row in results:
        print(row)
    # Assert that the query executes in a reasonable amount of time
    # assert query_time < 3.0  # for example, in seconds

    # Close the cursor and the connection
    cur.close()

def getQuery(rows):
    # You can prepend with EXPLAIN ANALYZE for internal postgres execution time
    if (len(rows) == 1):
        return """SELECT id, cube_distance(benchmark_vectors.vector, cube(ARRAY[%s])) 
                    FROM benchmark_vectors 
                    WHERE cube_distance(benchmark_vectors.vector, cube(ARRAY[%s])) < .3 
                    LIMIT 5;""" % (rows[0], rows[0])

            #ORDER BY benchmark_vectors.vector <-> cube(ARRAY[%s])

    # test a vector with no neighbors, this will be last in the results list 
    rows.append([999,9999,100000])
    searchRows = [(i,x) for i,x in enumerate(rows)]
    valuesString = ''
    for index, row in searchRows:
        valuesString = valuesString + '( %s::integer, ARRAY[%s] ),' % (index, row) 
    valuesString = valuesString[:-1] #trim the last comma
    return """CREATE TEMP TABLE search_queries AS 
                WITH t (id, v) AS ( VALUES %s)
                SELECT * FROM t;
                SELECT search_queries.id, bv.dist
                FROM search_queries
                LEFT JOIN LATERAL (
                    SELECT id, cube_distance(benchmark_vectors.vector, cube(v)) as dist
                    FROM benchmark_vectors 
                    WHERE cube_distance(benchmark_vectors.vector, cube(search_queries.v)) < .3 
                    LIMIT 1
                ) as bv ON TRUE
                """ % valuesString

def getCountVectors(cur):
    cur.execute('SELECT COUNT(*) FROM benchmark_vectors')
    results = cur.fetchall()
    print('Count of vector rows')
    for row in results:
        print(row)