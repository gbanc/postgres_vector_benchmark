import pandas as pd
import psycopg2
from settings import DATABASE_PARAMS

# format the list of floats into a string for sql query
def lst2pgarr(alist):
    return ','.join(map(str, alist))

class DbHelper:
    def __init__(self):
        return

    def populate_database(self):
        conn = psycopg2.connect(**DATABASE_PARAMS)
        self.create_and_load_test_table(conn)

    def create_and_load_test_table(self, db_connection):
        with db_connection.cursor() as cur:
            # Load the remaining rows CSV file into a pandas DataFrame
            df = pd.read_csv("test_data/remaining_rows.csv", header=None)

            cur.execute("CREATE EXTENSION IF NOT EXISTS cube;")
            # Create a new table to store the remaining data
            cur.execute("CREATE TABLE benchmark_vector (id serial PRIMARY KEY, vector cube)")

            # Insert the remaining data into the table
            # We have create the sql inline, parameters dont pass the array correctly
            df = df.fillna(0)
            for row in df.itertuples(index=False):
                cur.execute("INSERT INTO benchmark_vector (vector) VALUES (cube(ARRAY[%s]))" % lst2pgarr(row))
                db_connection.commit()

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

            

if __name__ == "__main__":
    helper = DbHelper()
    helper.populate_database()