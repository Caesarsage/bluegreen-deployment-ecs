-- Contract Phase: Remove old address column
-- IMPORTANT: Only run this after green is stable and blue is decommissioned!
BEGIN;

ALTER TABLE customers DROP COLUMN IF EXISTS address;

COMMIT;
