#!/bin/bash
psql -c "CREATE DATABASE documental_cehap;" || true
psql -c "CREATE USER documental_user WITH PASSWORD 'documental2026';" || true
psql -c "GRANT ALL PRIVILEGES ON DATABASE documental_cehap TO documental_user;"
psql -c "ALTER DATABASE documental_cehap OWNER TO documental_user;"
