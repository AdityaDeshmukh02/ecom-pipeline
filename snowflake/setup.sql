-- ── Setup ────────────────────────────────────────────
USE DATABASE ECOM_DB;
USE SCHEMA RAW;
USE WAREHOUSE ECOM_WH;

-- ── File Format & Stage ───────────────────────────────
CREATE OR REPLACE FILE FORMAT parquet_format
    TYPE = PARQUET;

CREATE OR REPLACE STAGE ecom_stage
    FILE_FORMAT = parquet_format;

-- ── Create Tables ─────────────────────────────────────
CREATE OR REPLACE TABLE RAW.ORDERS
USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
    FROM TABLE(
        INFER_SCHEMA(
            LOCATION => '@ECOM_STAGE/orders.parquet',
            FILE_FORMAT => 'parquet_format'
        )
    )
);

CREATE OR REPLACE TABLE RAW.USERS
USING TEMPLATE (
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
    FROM TABLE(
        INFER_SCHEMA(
            LOCATION => '@ECOM_STAGE/users.parquet',
            FILE_FORMAT => 'parquet_format'
        )
    )
);

create or replace table raw.events
USING TEMPLATE(                                  --Template() - Clause, Primarily used with "create" to automatically generate table's schema from semi-structured files such as Parquet.
    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))        --Array_AGG()- Stroes all the objects into a single object.
                                                 -- Object_Construct(*) - Converts each row of output into a JSON object.
    FROM TABLE(                                  --From Table() - It wraps infer_schema and treats it as a regular table.
    INFER_SCHEMA(                                --INFER_SCHEMA()- It reads parquet file and figures out the column names and data types.
        LOCATION => '@ECOM_STAGE/events.parquet',
        FILE_FORMAT => 'parquet_format'
        )
    )
);

-- ── Load Data ─────────────────────────────────────────
COPY INTO RAW.ORDERS
FROM @ECOM_STAGE/orders.parquet
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

COPY INTO RAW.USERS
FROM @ECOM_STAGE/users.parquet
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

COPY INTO RAW.EVENTS
FROM @ECOM_STAGE/events.parquet
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- ── Verify ────────────────────────────────────────────
SELECT COUNT(*) FROM RAW.ORDERS;   -- expected: 242
SELECT COUNT(*) FROM RAW.USERS;    -- expected: 500
SELECT COUNT(*) FROM RAW.EVENTS;   -- expected: 10000