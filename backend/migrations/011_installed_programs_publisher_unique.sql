BEGIN;

ALTER TABLE installed_programs
    DROP CONSTRAINT IF EXISTS installed_programs_machine_name_version_unique;

ALTER TABLE installed_programs
    DROP CONSTRAINT IF EXISTS installed_programs_machine_name_version_publisher_unique;

ALTER TABLE installed_programs
    ADD CONSTRAINT installed_programs_machine_name_version_publisher_unique
    UNIQUE (machine_id, name, version, publisher);

COMMIT;
