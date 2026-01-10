-- Expand Phase: Add new columns while keeping old ones
BEGIN;

-- Add new structured address columns
ALTER TABLE customers
ADD COLUMN IF NOT EXISTS street_address VARCHAR(255),
ADD COLUMN IF NOT EXISTS city VARCHAR(100),
ADD COLUMN IF NOT EXISTS state VARCHAR(2),
ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10);

-- Populate new columns from existing address field
-- This is a simple parser; real-world addresses may require more complex handling
UPDATE customers
SET
    street_address = SPLIT_PART (address, ',', 1),
    city = TRIM(SPLIT_PART (address, ',', 2)),
    state = TRIM(SPLIT_PART (address, ',', 3)),
    zip_code = TRIM(SPLIT_PART (address, ',', 4))
WHERE
    address IS NOT NULL
    AND street_address IS NULL;

COMMIT;
