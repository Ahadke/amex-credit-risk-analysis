-- Warehouse validation queries.
-- Quoted "customer_ID" matches AMEX source names and Python.
-- statement_date is the cleaned date field (source column S_2).

SELECT COUNT(*) FROM raw_labels;

SELECT COUNT(*) FROM raw_statements;

SELECT COUNT(*) FROM dim_customer;

SELECT COUNT(*) FROM fact_statements;

SELECT COUNT(DISTINCT "customer_ID")
FROM fact_statements;

SELECT AVG(target::numeric)
FROM dim_customer;

SELECT
    "customer_ID",
    statement_date,
    COUNT(*)
FROM fact_statements
GROUP BY
    "customer_ID",
    statement_date
HAVING COUNT(*) > 1
LIMIT 20;

SELECT
    "customer_ID",
    COUNT(*)
FROM dim_customer
GROUP BY "customer_ID"
HAVING COUNT(*) > 1
LIMIT 20;
