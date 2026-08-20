BEGIN;

ALTER TABLE machine_local_admins
    DROP CONSTRAINT IF EXISTS machine_local_admins_machine_admin_unique;

CREATE UNIQUE INDEX IF NOT EXISTS idx_machine_local_admins_machine_lower_admin_unique
ON machine_local_admins (machine_id, lower(admin_name));

COMMIT;
