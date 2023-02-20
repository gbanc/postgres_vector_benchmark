import pytest
import psycopg2
import psycopg2.extras
import pandas as pd
import pytest
from pytest_postgresql.janitor import DatabaseJanitor
from pytest_postgresql import factories

# format the list of floats into a string for sql query
def lst2pgarr(alist):
    return ','.join(map(str, alist))

def load_database(**kwargs):
    db_connection: connection = psycopg2.connect(**kwargs)
    with db_connection.cursor() as cur:

        # Load the remaining rows CSV file into a pandas DataFrame
        df = pd.read_csv("test_data/remaining_rows.csv", header=None)

        cur.execute("CREATE EXTENSION cube;")
        # Create a new table to store the remaining data
        cur.execute("CREATE TABLE benchmark_vector (id serial PRIMARY KEY, vector cube)")

        # Insert the remaining data into the table
        # We have create the sql inline, parameters dont pass the array correctly
        df = df.fillna(0)
        for row in df.itertuples(index=False):
            cur.execute("INSERT INTO benchmark_vector (vector) VALUES (cube(ARRAY[%s]))" % lst2pgarr(row))
        # sql = """
        #     INSERT INTO benchmark_vector (vector)
        #     VALUES (cube(ARRAY%s)) 
        # """
        # first_3 = df.head(3)
        # print(first_3)
        # data_gen = []
        # for index, row in first_3.iterrows():
        #     data_gen.append(lst2pgarr(row))
        # print(data_gen)
        # psycopg2.extras.execute_batch(cur, sql, ((1,3,4), (1,234,3)), page_size=1000)

        db_connection.commit()

@pytest.fixture
def database(postgresql_proc):
    # variable definition

    janitor = DatabaseJanitor(
        postgresql_proc.user,
        postgresql_proc.host,
        postgresql_proc.port,
        "vector_benchmark_test",
        postgresql_proc.version,
        password="password",
    )
    janitor.init()
    yield psycopg2.connect(
        dbname="vector_benchmark_test",
        user=postgresql_proc.user,
        password="password",
        host=postgresql_proc.host,
        port=postgresql_proc.port,
    )
    janitor.drop()
    
postgresql_proc = factories.postgresql_proc(
    load=[load_database],
)

postgresql = factories.postgresql(
    "postgresql_proc",
)