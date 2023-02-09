# Local Native Postgres Install
The default Postgresql package comes with cube, but limited to 100 dimensions.    
In order to increase the limit, we need to edit cubedata.h and recompile.    
Instruction on how to do that can be found here: https://stackoverflow.com/questions/53958843/there-is-no-cubedata-h-and-contrib-directory-in-postgresql    
To save us the trouble, we instead use docker-compose as detailed in the next section.
1. Install postgres and start postgres server    
    - Linux    
    `sudo systemctl start postgres`
2. Connect to your local postgres instance    
``` psql -U postgres -h 127.0.0.1 postgres --password ```
3. Create a database    
``` CREATE DATABASE test_vectors;```
4. Connect to db    
``` \c test_vectors; ```
5. Create cube extension    
``` CREATE EXTENSION cube; ```

# Locally using Docker Image and Docker-Compose
### In order to use cube with more than 100dim, We use a custom docker image with MAX_CUBE_DIM = 2048
1. Install docker and docker-compose
2. Run docker-compose file in same dir as docker-compose.yml    
``` sudo docker-compose up ```
3. Connect to container        
    ``` sudo docker exec -it vector_test bash ```    
4. Then connect to db so we can run queries    
    ``` psql -U user_0 db_0 ```
5. Create cube extension    
    ``` CREATE EXTENSION cube; ```

# DigitalOcean Managed Database
### Again, the cube extension will be limited to 100 dimensions.
https://docs.digitalocean.com/products/databases/postgresql/how-to/connect/
1. Follow the instructions to connect to your database using psql.
2. Create cube extension    
    ``` CREATE EXTENSION cube; ```

# Creating a temp table with data and running queries
### Note that by default cube is limited to 100 dimensions.
1. Create a temporary table, and generate 10k (1e4) vectors with 120 dimensions to insert:
Note that random() returns a number between 0 and 1
    ```
    CREATE TEMP TABLE space_nd AS
      SELECT i, cube(array_agg(random()::float)) AS c
      FROM generate_series(1,1e4) AS i
      CROSS JOIN LATERAL generate_series(1,120)
        AS x
      GROUP BY i; 
    ```
2. Generate a single point and use the <-> operator to find nearest 5 points using Euclidean distance 
    ``` 
    WITH points AS (
      SELECT cube(array_agg(random()::float)) AS c
      FROM generate_series(1,120)
        AS x
    )
    SELECT i,
      pg_typeof(space_nd.c),
      pg_typeof(points.c),
      cube_distance(space_nd.c, points.c)
    FROM space_nd
    CROSS JOIN points
    ORDER BY space_nd.c <-> points.c
    LIMIT 5;
    ```
3. To get query timings and plan, prepend the query with `EXPLAIN ANALYZE`
4. Create a GiST index on cube column (c) of space_nd
``` 
CREATE INDEX ON space_nd USING gist ( c );
```

# Creating a regular table, inserting, and querying data
1. Create table    
``` CREATE TABLE vector_table (id serial PRIMARY KEY, vector cube) ```
2. Insert one random 120d array    
``` INSERT INTO vector_table (vector) SELECT cube(array_agg(random()::float)) FROM generate_series(1,120) ```
3. Search for nearby points where distance is less than .3
    ``` 
    SELECT id, cube_distance(vector_table.vector, {search_vector}) 
    WHERE cube_distance(vector_table.vector, {search_vector}) < .3
    ORDER BY space_nd.c <-> {search_vector}
    LIMIT 5;
    ```

# Running and benchmarking parallel queries
We can orchestrate parallel requests using python multithreading to perform multiple concurrent queries
     
# Precision 
Since cube extension stores values internally as 64-bit floating point numbers, i think it is unlikely that reducing the input vector values will result in performance increases. 

# Benchmarks
For local testing, in our docker-compose file we limit our container to 1 cpu core    
A basic managed database instance on DigitalOcean is 1GB RAM / 1vCPU / 10 GB disk    
Using 1 core on my Thinkpad should be somewhat comparable to 1vCPU, albeit 1vCPU on their hardware will be more powerful    
    
Note that postgres does do some optimizing after running the same query multiple times, so query times may improve after the first query (sometimes significantly)    
    
The bottleneck for inserting data and creating indexes is usually RAM.    
When performing search queries, the bottlenecks are CPU and storage I/O    
    
As you can see below from comparing 50M to 1G memory, search query times are similar.    
The main difference I noticed is creating indeces takes much longer with 50M memory. 

Summary Table:
|   1 cpu core / 50M memory  | 10k    | 100k    | 1M       |
|----------------------------|--------|---------|----------|
| Creating Temp Table and Insert       | 1383 ms | 19735 ms | 264618 ms |
| Query 1 Point; No index    | 116 ms  | 533 ms   | 5925.5 ms |
| Query 1 point; With index  | 86 ms   |    483.3     | 3215 ms   |
| Insert 1 point; No index   | 0.4 ms |   4.3ms      | 2.3 ms    |
| Insert 1 point; With Index | 1.5 ms |   5.1ms      | 9.8 ms    |

    

|  1 cpu core /  1G memory   | 10k    | 100k    | 1M       |
|----------------------------|--------|---------|----------|
| Creating Temp Table and Insert        | 1149 ms | 14241 ms | 203225 ms |
| Query 1 Point; No index    | 102 ms  | 347 ms   | 4700 ms   |
| Query 1 point; With index  | 90 ms   | 319 ms   | 3299 ms   |
| Insert 1 point; No index   | 0.5 ms  | 0.4 ms   | 1.9 ms    |
| Insert 1 point; With Index | 1.1 ms  | 0.8 ms   | 6.4 ms    |

1. ThinkPad X260 - Intel(R) Core(TM) i5-6300U CPU @ 2.40GHz
    - 1 cpu core
    - 50M memory
    - 120 dimension vectors
        1. 10k rows
            - Creating temp table and inserting 10k rows: 1383ms
            - Querying 1 point
                - No index: 109ms to 124ms - Avg. 116.5ms
                - With Index: 40ms to 132ms - Avg. 86ms
            - Insert 1 point
                - No Index: 0.369ms to 0.511ms - Avg. 0.44ms
                - With Index: 0.198ms to 1.260ms -  Avg. 1.458ms
        2. 100k rows
            - Creating temp table and inserting 100k rows: 19735ms
            - Querying 1 point
                - No index: 533ms 
                - With index: 330ms to 636.550ms - Avg. 483.3ms
            - Insert 1 point
                - No Index: 0.235ms to 8.350ms - Avg. 4.293ms
                - With Index: 0.644ms to 9.485ms -  Avg. 5.065ms
        3. 1M rows
            - Creating temp table and inserting 1M rows: 264618ms
            - Querying 1 point
                - No index: 4000ms to 7851ms - Avg. 5925.5ms
                - With index: 3063ms to 3367ms - Avg. 3215ms
            - Insert 1 point
                - No Index: 0.509ms to 4.030ms - Avg. 2.27ms
                - With Index: 4.102ms to 15.635ms - Avg. 9.869 ms
    - 1 cpu core
    - 1G memory
    - 120 dimension vectors
        1. 10k rows
            - Creating temp table and inserting 10k rows: 1149ms
            - Querying 1 point
                - No index: 72ms to 132ms - Avg. 102ms
                - With index: 53ms to 127ms -  Avg. 90ms
            - Insert 1 point
                - No Index: 0.380ms to 0.560ms - Avg. 0.47ms
                - With Index: 0.665ms to 1.482ms -  Avg. 1.074ms

        2. 100k rows
            - Creating temp table and inserting 100k rows: 14241ms
            - Querying 1 point
                - No index: 294ms to 401ms - Avg. 347ms
                - With index: 289ms to 350ms - Avg. 319ms
            - Insert 1 point
                - No index: 0.350ms to 0.445ms - Avg. 0.397ms
                - With index: 0.331ms to 1.3ms - Avg. 0.815ms
        3. 1M rows
            - Creating temp table and inserting 1M rows: 203225ms
            - Querying 1 point
                - No index: 3366ms to 6035ms - Avg. 4700ms
                - With index: 3259ms to 3339ms - Avg. 3299ms
            - Insert 1 point
                - No index: 0.121 ms to 3.774ms - Avg. 1.948ms
                - With index: 1.852ms to 11ms - Avg. 6.426ms
                

    
    Conclusion: Search Queries are reasonably fast, but inserting large amounts of data and creating indexes takes much longer.