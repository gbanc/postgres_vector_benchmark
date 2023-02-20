import pandas as pd
import psycopg2
from settings import DATABASE_PARAMS
import io
import csv

# format the list of floats into a string for sql query
def lst2pgarr(alist):
    return ','.join(map(str, alist))

def lst2pgarrexplicit(alist):
    return '{' + ','.join(map(str,alist)) + '}'

class DbHelper:
    def __init__(self):
        return

    def populate_database(self):
        conn = psycopg2.connect(**DATABASE_PARAMS)
        self.create_and_load_test_table(conn)


    def create_and_load_test_table(self, db_connection):

        def insert_with_string_io(df: pd.DataFrame, table_name: str):
            buffer = io.StringIO()
            df.to_csv(buffer, index=False, header=False, sep='\t' )
            buffer.seek(0)
            with db_connection.cursor() as cursor:
                try:
                    cursor.copy_from(file=buffer, table=table_name,  null="", sep='\t', columns=['vector'])
                except (Exception, psycopg2.DatabaseError) as error:
                    print("Error: %s" % error)

        def processChunk(df):
            # do some data munging to turn float arrays into postgres array strings
            rows = []
            for row in df.itertuples(index=False):
                rows.append(row)
            newdf = pd.DataFrame({'vector': rows})
            newdf['vector'] = newdf.vector.apply(lambda x: lst2pgarrexplicit(x))
            insert_with_string_io(newdf, 'csv_vectors')


        with db_connection.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS cube;")
            # Create an intermediate table table to store raw arrays
            cur.execute("CREATE TABLE IF NOT EXISTS csv_vectors (vector float[])")
            with pd.read_csv("test_data/remaining_rows.csv", chunksize=100, header=None) as reader:
                for chunk in reader:
                    processChunk(chunk)
                    db_connection.commit()
            
            # select insert from csv_vectors to cube column 
            cur.execute("CREATE TABLE IF NOT EXISTS benchmark_vectors (id serial PRIMARY KEY, vector cube)")
            cur.execute("INSERT INTO benchmark_vectors (vector) SELECT cube(vector) FROM csv_vectors")
            cur.close()

if __name__ == "__main__":
    helper = DbHelper()
    helper.populate_database()