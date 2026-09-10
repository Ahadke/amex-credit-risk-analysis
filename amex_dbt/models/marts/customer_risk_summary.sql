{{ config(materialized='table') }}

select
    "customer_ID" as customer_id,
    max(TARGET) as target,
    count(*) as statement_count,
    min("S_2") as first_statement_date,
    max("S_2") as last_statement_date
from {{ ref('stg_amex_train') }}
group by "customer_ID"
