BEGIN;

ALTER TABLE machines DROP COLUMN IF EXISTS snipeit_asset_id;

COMMIT;
