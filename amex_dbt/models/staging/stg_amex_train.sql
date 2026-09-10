{{ config(materialized='view') }}

select
    *
from {{ source('amex', 'TRAIN_ANALYTICS_SAMPLE') }}
