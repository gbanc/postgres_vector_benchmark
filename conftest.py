import pytest
import psycopg2
import psycopg2.extras
import pandas as pd
import pytest
from pytest_postgresql.janitor import DatabaseJanitor
from pytest_postgresql import factories
from DbHelper import DbHelper
from settings import DATABASE_PARAMS

def load_database(**kwargs):
    db_connection: connection = psycopg2.connect(**kwargs)
    helper = DbHelper()
    helper.create_and_load_test_table(db_connection)

@pytest.fixture
def database(postgresql_proc):
    # variable definition
    janitor = DatabaseJanitor(**DATABASE_PARAMS)
    janitor.init()
    yield psycopg2.connect(**DATABASE_PARAMS)
    janitor.drop()
    
postgresql_proc = factories.postgresql_proc(
    # load=[load_database],
)

# postgresql = factories.postgresql(
#     "postgresql_proc",
# )

# comment this out if you use the above
@pytest.fixture(scope="session")
def postgresql():
    conn = psycopg2.connect(**DATABASE_PARAMS)
    yield conn
    conn.close()