DROP TABLE IF EXISTS data_quality_log CASCADE;
CREATE TABLE data_quality_log (
    check_id SERIAL PRIMARY KEY,
    check_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    affected_rows BIGINT,
    details TEXT,
    checked_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO data_quality_log (check_name, severity, affected_rows, details)
SELECT 'raw_statements_row_count', 'INFO', COUNT(*), 'Total statement rows loaded'
FROM raw_statements;

INSERT INTO data_quality_log (check_name, severity, affected_rows, details)
SELECT 'raw_labels_row_count', 'INFO', COUNT(*), 'Total customers with labels'
FROM raw_labels;

INSERT INTO data_quality_log (check_name, severity, affected_rows, details)
SELECT 'missing_customer_id', 'ERROR', COUNT(*), 'Rows with null customer_ID'
FROM raw_statements WHERE "customer_ID" IS NULL;

INSERT INTO data_quality_log (check_name, severity, affected_rows, details)
SELECT 'missing_statement_date', 'ERROR', COUNT(*), 'Rows with null S_2'
FROM raw_statements WHERE "S_2" IS NULL;

INSERT INTO data_quality_log (check_name, severity, affected_rows, details)
SELECT 'labels_without_statements', 'WARNING', COUNT(*), 'Customers in labels with no matching statement rows'
FROM raw_labels l
LEFT JOIN raw_statements s ON l."customer_ID" = s."customer_ID"
WHERE s."customer_ID" IS NULL;

DROP TABLE IF EXISTS dim_customer CASCADE;
CREATE TABLE dim_customer AS
SELECT
    l."customer_ID",
    l.target,
    MIN(s."S_2"::DATE) AS first_statement_date,
    MAX(s."S_2"::DATE) AS last_statement_date,
    COUNT(s."S_2") AS n_statements
FROM raw_labels l
LEFT JOIN raw_statements s ON l."customer_ID" = s."customer_ID"
GROUP BY l."customer_ID", l.target;

ALTER TABLE dim_customer ADD PRIMARY KEY ("customer_ID");
CREATE INDEX idx_dim_customer_target ON dim_customer (target);

INSERT INTO data_quality_log (check_name, severity, affected_rows, details)
SELECT 'dim_customer_row_count', 'INFO', COUNT(*), 'Final customer dimension row count'
FROM dim_customer;


DROP TABLE IF EXISTS fact_statements CASCADE;
CREATE TABLE fact_statements AS
SELECT
    s."customer_ID",
    s."S_2"::DATE AS statement_date,
    NULLIF(s."P_2", '')::DOUBLE PRECISION AS "P_2",
    NULLIF(s."D_39", '')::DOUBLE PRECISION AS "D_39",
    NULLIF(s."B_1", '')::DOUBLE PRECISION AS "B_1",
    NULLIF(s."B_2", '')::DOUBLE PRECISION AS "B_2",
    NULLIF(s."R_1", '')::DOUBLE PRECISION AS "R_1",
    NULLIF(s."S_3", '')::DOUBLE PRECISION AS "S_3",
    NULLIF(s."D_41", '')::DOUBLE PRECISION AS "D_41",
    NULLIF(s."B_3", '')::DOUBLE PRECISION AS "B_3",
    NULLIF(s."D_42", '')::DOUBLE PRECISION AS "D_42",
    NULLIF(s."D_43", '')::DOUBLE PRECISION AS "D_43",
    NULLIF(s."D_44", '')::DOUBLE PRECISION AS "D_44",
    NULLIF(s."B_4", '')::DOUBLE PRECISION AS "B_4",
    NULLIF(s."D_45", '')::DOUBLE PRECISION AS "D_45",
    NULLIF(s."B_5", '')::DOUBLE PRECISION AS "B_5",
    NULLIF(s."R_2", '')::DOUBLE PRECISION AS "R_2",
    NULLIF(s."D_46", '')::DOUBLE PRECISION AS "D_46",
    NULLIF(s."D_47", '')::DOUBLE PRECISION AS "D_47",
    NULLIF(s."D_48", '')::DOUBLE PRECISION AS "D_48",
    NULLIF(s."D_49", '')::DOUBLE PRECISION AS "D_49",
    NULLIF(s."B_6", '')::DOUBLE PRECISION AS "B_6",
    NULLIF(s."B_7", '')::DOUBLE PRECISION AS "B_7",
    NULLIF(s."B_8", '')::DOUBLE PRECISION AS "B_8",
    NULLIF(s."D_50", '')::DOUBLE PRECISION AS "D_50",
    NULLIF(s."D_51", '')::DOUBLE PRECISION AS "D_51",
    NULLIF(s."B_9", '')::DOUBLE PRECISION AS "B_9",
    NULLIF(s."R_3", '')::DOUBLE PRECISION AS "R_3",
    NULLIF(s."D_52", '')::DOUBLE PRECISION AS "D_52",
    NULLIF(s."P_3", '')::DOUBLE PRECISION AS "P_3",
    NULLIF(s."B_10", '')::DOUBLE PRECISION AS "B_10",
    NULLIF(s."D_53", '')::DOUBLE PRECISION AS "D_53",
    NULLIF(s."S_5", '')::DOUBLE PRECISION AS "S_5",
    NULLIF(s."B_11", '')::DOUBLE PRECISION AS "B_11",
    NULLIF(s."S_6", '')::DOUBLE PRECISION AS "S_6",
    NULLIF(s."D_54", '')::DOUBLE PRECISION AS "D_54",
    NULLIF(s."R_4", '')::DOUBLE PRECISION AS "R_4",
    NULLIF(s."S_7", '')::DOUBLE PRECISION AS "S_7",
    NULLIF(s."B_12", '')::DOUBLE PRECISION AS "B_12",
    NULLIF(s."S_8", '')::DOUBLE PRECISION AS "S_8",
    NULLIF(s."D_55", '')::DOUBLE PRECISION AS "D_55",
    NULLIF(s."D_56", '')::DOUBLE PRECISION AS "D_56",
    NULLIF(s."B_13", '')::DOUBLE PRECISION AS "B_13",
    NULLIF(s."R_5", '')::DOUBLE PRECISION AS "R_5",
    NULLIF(s."D_58", '')::DOUBLE PRECISION AS "D_58",
    NULLIF(s."S_9", '')::DOUBLE PRECISION AS "S_9",
    NULLIF(s."B_14", '')::DOUBLE PRECISION AS "B_14",
    NULLIF(s."D_59", '')::DOUBLE PRECISION AS "D_59",
    NULLIF(s."D_60", '')::DOUBLE PRECISION AS "D_60",
    NULLIF(s."D_61", '')::DOUBLE PRECISION AS "D_61",
    NULLIF(s."B_15", '')::DOUBLE PRECISION AS "B_15",
    NULLIF(s."S_11", '')::DOUBLE PRECISION AS "S_11",
    NULLIF(s."D_62", '')::DOUBLE PRECISION AS "D_62",
    NULLIF(s."D_63", '') AS "D_63",
    NULLIF(s."D_64", '') AS "D_64",
    NULLIF(s."D_65", '')::DOUBLE PRECISION AS "D_65",
    NULLIF(s."B_16", '')::DOUBLE PRECISION AS "B_16",
    NULLIF(s."B_17", '')::DOUBLE PRECISION AS "B_17",
    NULLIF(s."B_18", '')::DOUBLE PRECISION AS "B_18",
    NULLIF(s."B_19", '')::DOUBLE PRECISION AS "B_19",
    NULLIF(s."D_66", '')::DOUBLE PRECISION AS "D_66",
    NULLIF(s."B_20", '')::DOUBLE PRECISION AS "B_20",
    NULLIF(s."D_68", '')::DOUBLE PRECISION AS "D_68",
    NULLIF(s."S_12", '')::DOUBLE PRECISION AS "S_12",
    NULLIF(s."R_6", '')::DOUBLE PRECISION AS "R_6",
    NULLIF(s."S_13", '')::DOUBLE PRECISION AS "S_13",
    NULLIF(s."B_21", '')::DOUBLE PRECISION AS "B_21",
    NULLIF(s."D_69", '')::DOUBLE PRECISION AS "D_69",
    NULLIF(s."B_22", '')::DOUBLE PRECISION AS "B_22",
    NULLIF(s."D_70", '')::DOUBLE PRECISION AS "D_70",
    NULLIF(s."D_71", '')::DOUBLE PRECISION AS "D_71",
    NULLIF(s."D_72", '')::DOUBLE PRECISION AS "D_72",
    NULLIF(s."S_15", '')::DOUBLE PRECISION AS "S_15",
    NULLIF(s."B_23", '')::DOUBLE PRECISION AS "B_23",
    NULLIF(s."D_73", '')::DOUBLE PRECISION AS "D_73",
    NULLIF(s."P_4", '')::DOUBLE PRECISION AS "P_4",
    NULLIF(s."D_74", '')::DOUBLE PRECISION AS "D_74",
    NULLIF(s."D_75", '')::DOUBLE PRECISION AS "D_75",
    NULLIF(s."D_76", '')::DOUBLE PRECISION AS "D_76",
    NULLIF(s."B_24", '')::DOUBLE PRECISION AS "B_24",
    NULLIF(s."R_7", '')::DOUBLE PRECISION AS "R_7",
    NULLIF(s."D_77", '')::DOUBLE PRECISION AS "D_77",
    NULLIF(s."B_25", '')::DOUBLE PRECISION AS "B_25",
    NULLIF(s."B_26", '')::DOUBLE PRECISION AS "B_26",
    NULLIF(s."D_78", '')::DOUBLE PRECISION AS "D_78",
    NULLIF(s."D_79", '')::DOUBLE PRECISION AS "D_79",
    NULLIF(s."R_8", '')::DOUBLE PRECISION AS "R_8",
    NULLIF(s."R_9", '')::DOUBLE PRECISION AS "R_9",
    NULLIF(s."S_16", '')::DOUBLE PRECISION AS "S_16",
    NULLIF(s."D_80", '')::DOUBLE PRECISION AS "D_80",
    NULLIF(s."R_10", '')::DOUBLE PRECISION AS "R_10",
    NULLIF(s."R_11", '')::DOUBLE PRECISION AS "R_11",
    NULLIF(s."B_27", '')::DOUBLE PRECISION AS "B_27",
    NULLIF(s."D_81", '')::DOUBLE PRECISION AS "D_81",
    NULLIF(s."D_82", '')::DOUBLE PRECISION AS "D_82",
    NULLIF(s."S_17", '')::DOUBLE PRECISION AS "S_17",
    NULLIF(s."R_12", '')::DOUBLE PRECISION AS "R_12",
    NULLIF(s."B_28", '')::DOUBLE PRECISION AS "B_28",
    NULLIF(s."R_13", '')::DOUBLE PRECISION AS "R_13",
    NULLIF(s."D_83", '')::DOUBLE PRECISION AS "D_83",
    NULLIF(s."R_14", '')::DOUBLE PRECISION AS "R_14",
    NULLIF(s."R_15", '')::DOUBLE PRECISION AS "R_15",
    NULLIF(s."D_84", '')::DOUBLE PRECISION AS "D_84",
    NULLIF(s."R_16", '')::DOUBLE PRECISION AS "R_16",
    NULLIF(s."B_29", '')::DOUBLE PRECISION AS "B_29",
    NULLIF(s."B_30", '')::DOUBLE PRECISION AS "B_30",
    NULLIF(s."S_18", '')::DOUBLE PRECISION AS "S_18",
    NULLIF(s."D_86", '')::DOUBLE PRECISION AS "D_86",
    NULLIF(s."D_87", '')::DOUBLE PRECISION AS "D_87",
    NULLIF(s."R_17", '')::DOUBLE PRECISION AS "R_17",
    NULLIF(s."R_18", '')::DOUBLE PRECISION AS "R_18",
    NULLIF(s."D_88", '')::DOUBLE PRECISION AS "D_88",
    NULLIF(s."B_31", '')::DOUBLE PRECISION AS "B_31",
    NULLIF(s."S_19", '')::DOUBLE PRECISION AS "S_19",
    NULLIF(s."R_19", '')::DOUBLE PRECISION AS "R_19",
    NULLIF(s."B_32", '')::DOUBLE PRECISION AS "B_32",
    NULLIF(s."S_20", '')::DOUBLE PRECISION AS "S_20",
    NULLIF(s."R_20", '')::DOUBLE PRECISION AS "R_20",
    NULLIF(s."R_21", '')::DOUBLE PRECISION AS "R_21",
    NULLIF(s."B_33", '')::DOUBLE PRECISION AS "B_33",
    NULLIF(s."D_89", '')::DOUBLE PRECISION AS "D_89",
    NULLIF(s."R_22", '')::DOUBLE PRECISION AS "R_22",
    NULLIF(s."R_23", '')::DOUBLE PRECISION AS "R_23",
    NULLIF(s."D_91", '')::DOUBLE PRECISION AS "D_91",
    NULLIF(s."D_92", '')::DOUBLE PRECISION AS "D_92",
    NULLIF(s."D_93", '')::DOUBLE PRECISION AS "D_93",
    NULLIF(s."D_94", '')::DOUBLE PRECISION AS "D_94",
    NULLIF(s."R_24", '')::DOUBLE PRECISION AS "R_24",
    NULLIF(s."R_25", '')::DOUBLE PRECISION AS "R_25",
    NULLIF(s."D_96", '')::DOUBLE PRECISION AS "D_96",
    NULLIF(s."S_22", '')::DOUBLE PRECISION AS "S_22",
    NULLIF(s."S_23", '')::DOUBLE PRECISION AS "S_23",
    NULLIF(s."S_24", '')::DOUBLE PRECISION AS "S_24",
    NULLIF(s."S_25", '')::DOUBLE PRECISION AS "S_25",
    NULLIF(s."S_26", '')::DOUBLE PRECISION AS "S_26",
    NULLIF(s."D_102", '')::DOUBLE PRECISION AS "D_102",
    NULLIF(s."D_103", '')::DOUBLE PRECISION AS "D_103",
    NULLIF(s."D_104", '')::DOUBLE PRECISION AS "D_104",
    NULLIF(s."D_105", '')::DOUBLE PRECISION AS "D_105",
    NULLIF(s."D_106", '')::DOUBLE PRECISION AS "D_106",
    NULLIF(s."D_107", '')::DOUBLE PRECISION AS "D_107",
    NULLIF(s."B_36", '')::DOUBLE PRECISION AS "B_36",
    NULLIF(s."B_37", '')::DOUBLE PRECISION AS "B_37",
    NULLIF(s."R_26", '')::DOUBLE PRECISION AS "R_26",
    NULLIF(s."R_27", '')::DOUBLE PRECISION AS "R_27",
    NULLIF(s."B_38", '')::DOUBLE PRECISION AS "B_38",
    NULLIF(s."D_108", '')::DOUBLE PRECISION AS "D_108",
    NULLIF(s."D_109", '')::DOUBLE PRECISION AS "D_109",
    NULLIF(s."D_110", '')::DOUBLE PRECISION AS "D_110",
    NULLIF(s."D_111", '')::DOUBLE PRECISION AS "D_111",
    NULLIF(s."B_39", '')::DOUBLE PRECISION AS "B_39",
    NULLIF(s."D_112", '')::DOUBLE PRECISION AS "D_112",
    NULLIF(s."B_40", '')::DOUBLE PRECISION AS "B_40",
    NULLIF(s."S_27", '')::DOUBLE PRECISION AS "S_27",
    NULLIF(s."D_113", '')::DOUBLE PRECISION AS "D_113",
    NULLIF(s."D_114", '')::DOUBLE PRECISION AS "D_114",
    NULLIF(s."D_115", '')::DOUBLE PRECISION AS "D_115",
    NULLIF(s."D_116", '')::DOUBLE PRECISION AS "D_116",
    NULLIF(s."D_117", '')::DOUBLE PRECISION AS "D_117",
    NULLIF(s."D_118", '')::DOUBLE PRECISION AS "D_118",
    NULLIF(s."D_119", '')::DOUBLE PRECISION AS "D_119",
    NULLIF(s."D_120", '')::DOUBLE PRECISION AS "D_120",
    NULLIF(s."D_121", '')::DOUBLE PRECISION AS "D_121",
    NULLIF(s."D_122", '')::DOUBLE PRECISION AS "D_122",
    NULLIF(s."D_123", '')::DOUBLE PRECISION AS "D_123",
    NULLIF(s."D_124", '')::DOUBLE PRECISION AS "D_124",
    NULLIF(s."D_125", '')::DOUBLE PRECISION AS "D_125",
    NULLIF(s."D_126", '')::DOUBLE PRECISION AS "D_126",
    NULLIF(s."D_127", '')::DOUBLE PRECISION AS "D_127",
    NULLIF(s."D_128", '')::DOUBLE PRECISION AS "D_128",
    NULLIF(s."D_129", '')::DOUBLE PRECISION AS "D_129",
    NULLIF(s."B_41", '')::DOUBLE PRECISION AS "B_41",
    NULLIF(s."B_42", '')::DOUBLE PRECISION AS "B_42",
    NULLIF(s."D_130", '')::DOUBLE PRECISION AS "D_130",
    NULLIF(s."D_131", '')::DOUBLE PRECISION AS "D_131",
    NULLIF(s."D_132", '')::DOUBLE PRECISION AS "D_132",
    NULLIF(s."D_133", '')::DOUBLE PRECISION AS "D_133",
    NULLIF(s."R_28", '')::DOUBLE PRECISION AS "R_28",
    NULLIF(s."D_134", '')::DOUBLE PRECISION AS "D_134",
    NULLIF(s."D_135", '')::DOUBLE PRECISION AS "D_135",
    NULLIF(s."D_136", '')::DOUBLE PRECISION AS "D_136",
    NULLIF(s."D_137", '')::DOUBLE PRECISION AS "D_137",
    NULLIF(s."D_138", '')::DOUBLE PRECISION AS "D_138",
    NULLIF(s."D_139", '')::DOUBLE PRECISION AS "D_139",
    NULLIF(s."D_140", '')::DOUBLE PRECISION AS "D_140",
    NULLIF(s."D_141", '')::DOUBLE PRECISION AS "D_141",
    NULLIF(s."D_142", '')::DOUBLE PRECISION AS "D_142",
    NULLIF(s."D_143", '')::DOUBLE PRECISION AS "D_143",
    NULLIF(s."D_144", '')::DOUBLE PRECISION AS "D_144",
    NULLIF(s."D_145", '')::DOUBLE PRECISION AS "D_145"
FROM raw_statements s
WHERE s."customer_ID" IS NOT NULL
  AND s."S_2" IS NOT NULL;

ALTER TABLE fact_statements
    ALTER COLUMN "customer_ID" SET NOT NULL,
    ALTER COLUMN statement_date SET NOT NULL;

ALTER TABLE fact_statements
    ADD PRIMARY KEY ("customer_ID", statement_date);

CREATE INDEX idx_fact_statements_customer ON fact_statements ("customer_ID");
CREATE INDEX idx_fact_statements_date ON fact_statements (statement_date);

INSERT INTO data_quality_log (check_name, severity, affected_rows, details)
SELECT 'fact_statements_row_count', 'INFO', COUNT(*), 'Final typed statement fact row count'
FROM fact_statements;
