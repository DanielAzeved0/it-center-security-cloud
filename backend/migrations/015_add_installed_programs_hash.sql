ALTER TABLE machines
ADD COLUMN IF NOT EXISTS installed_programs_hash VARCHAR(64);
