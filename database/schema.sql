CREATE TABLE IF NOT EXISTS hcpcs_codes (
    id BIGSERIAL PRIMARY KEY,

    hcpcs_code VARCHAR(50) NOT NULL,

    group_code VARCHAR(10),

    category_name VARCHAR(255),

    long_description TEXT NOT NULL,

    desc_hash CHAR(32) NOT NULL,

    effective_date DATE NOT NULL,

    end_date DATE,

    is_current BOOLEAN NOT NULL DEFAULT TRUE,

    version INT NOT NULL DEFAULT 1,

    inserted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_hcpcs_code_current
ON hcpcs_codes(hcpcs_code)
WHERE is_current = TRUE;


CREATE INDEX IF NOT EXISTS idx_hcpcs_code
ON hcpcs_codes(hcpcs_code);

CREATE TABLE IF NOT EXISTS pipeline_metrics (
    id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    rows_loaded INT NOT NULL DEFAULT 0,
    last_success_ts TIMESTAMP,
    dq_failures INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);