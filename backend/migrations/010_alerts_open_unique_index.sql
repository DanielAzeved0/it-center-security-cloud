BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_machine_alert_type_open_unique
ON alerts (machine_id, alert_type)
WHERE status IN ('open', 'investigating');

COMMIT;
