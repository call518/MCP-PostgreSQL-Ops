#!/bin/bash

# postgres
docker exec -it postgresql-17 psql -U postgres -d postgres -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
docker exec -it postgresql-17 psql -U postgres -d postgres -c "CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;"

# testdb
docker exec -it postgresql-17 psql -U postgres -d testdb -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
docker exec -it postgresql-17 psql -U postgres -d testdb -c "CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;"
