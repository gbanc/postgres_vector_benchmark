from timeit import default_timer as timer
import pandas as pd
import pytest
import random
from DbHelper import lst2pgarr

# Load the test rows CSV file into a pandas DataFrame
df = pd.read_csv("test_data/10k_rows.csv", header=None)
sample_size = 1

number_of_tests = 4
test_cases = []
for i in range(number_of_tests):
    random_indices = random.sample(range(len(df)), sample_size)
    df_random = df.iloc[random_indices]
    test_cases.append(df_random)

@pytest.mark.parametrize("search_vectors", test_cases)
def test_query_performance(postgresql, search_vectors):
    # Open a cursor to perform database operations
    cur = postgresql.cursor()

    # Generate a random sample from the 10k rows
    rows = []
    for r in search_vectors.itertuples(index=False):
        rows.append(lst2pgarr(r))
    
    # Execute a sample query and measure its execution time
    start_time = timer()
    # You can prepend with EXPLAIN ANALYZE for internal postgres execution time
    cur.execute("EXPLAIN ANALYZE SELECT id, cube_distance(benchmark_vector.vector, cube(ARRAY[%s])) \
        FROM benchmark_vector \
        WHERE cube_distance(benchmark_vector.vector, cube(ARRAY[%s])) < .3 \
        ORDER BY benchmark_vector.vector <-> cube(ARRAY[%s]) \
        LIMIT 5;" % (rows[0], rows[0], rows[0]))
    
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
    assert query_time < 3.0  # for example, in seconds

    # Close the cursor and the connection
    cur.close()