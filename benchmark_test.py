import pytest
import psycopg2
import psycopg2.extras
from timeit import default_timer as timer
import pandas as pd
import random
from conftest import lst2pgarr

def test_query_performance(postgresql):
    # Open a cursor to perform database operations
    cur = postgresql.cursor()

    # Load the test rows CSV file into a pandas DataFrame
    df = pd.read_csv("test_data/10k_rows.csv", header=None)
    # Execute a sample query and measure its execution time
    start_time = timer()


    # Generate a random sample from the 10k rows
    sample_size = 1
    random_indices = random.sample(range(len(df)), sample_size)
    df_random = df.iloc[random_indices]
    rows = []
    for r in df_random.itertuples(index=False):
        rows.append(lst2pgarr(r))
    #cur.execute("SELECT * FROM benchmark_vector WHERE vector = ARRAY%s" % rows)
    
    cur.execute("SELECT id, cube_distance(benchmark_vector.vector, cube(ARRAY[%s])) \
        FROM benchmark_vector \
        WHERE cube_distance(benchmark_vector.vector, cube(ARRAY[%s])) < .3 \
        ORDER BY benchmark_vector.vector <-> cube(ARRAY[%s]) \
        LIMIT 5;" % (rows[0], rows[0], rows[0]))
    
    end_time = timer()
    query_time = end_time - start_time

    # Assert that the query returns the expected results
    results = cur.fetchall()
    assert len(results) == 10  # for example

    # Assert that the query executes in a reasonable amount of time
    assert query_time < 1.0  # for example, in seconds

    # Close the cursor and the connection
    cur.close()