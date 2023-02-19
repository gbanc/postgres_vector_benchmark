import pytest
import psycopg2
from timeit import default_timer as timer
import pandas as pd

@pytest.fixture(scope="session")
def db_conn():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="password",
        host="localhost",
        port="5432"
    )
    yield conn
    conn.close()

def lst2pgarr(alist):
    return ','.join(map(str, alist))

@pytest.fixture(scope="session")
def remaining_data(db_conn):
    # Load the remaining rows CSV file into a pandas DataFrame
    df = pd.read_csv("test_data/remaining_rows.csv", header=None)

    # Open a cursor to perform database operations
    cur = db_conn.cursor()

    # Create a new table to store the remaining data
    cur.execute("CREATE TABLE vector_test (id SERIAL, vector cube)")

    # Insert the remaining data into the table
    # We have create the sql inline, parameters dont pass the array correctly
    for row in df.itertuples(index=False):
        cur.execute("INSERT INTO vector_test (vector) VALUES (cube(ARRAY[%s]))" % lst2pgarr(row))

    # Commit the changes to the database
    db_conn.commit()

    # Close the cursor
    cur.close()

    return df

def test_query_performance(remaining_data):
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="password",
        host="localhost",
        port="5432"
    )

    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Execute a sample query and measure its execution time
    start_time = timer()
    cur.execute("SELECT * FROM vector_test WHERE mycolumn = 'myvalue'")
    end_time = timer()
    query_time = end_time - start_time

    # Assert that the query returns the expected results
    results = cur.fetchall()
    assert len(results) == 10  # for example

    # Assert that the query executes in a reasonable amount of time
    assert query_time < 1.0  # for example, in seconds

    # Close the cursor and the connection
    cur.close()
    conn.close()