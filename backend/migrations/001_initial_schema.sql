BEGIN;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS machines (
    id BIGSERIAL PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255),
    ip_address INET,
    operating_system VARCHAR(255),
    os_version VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'offline',
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT machines_status_check CHECK (status IN ('online', 'offline')),
    CONSTRAINT machines_hostname_not_blank CHECK (btrim(hostname) <> '')
);

CREATE INDEX IF NOT EXISTS idx_machines_status ON machines (status);
CREATE INDEX IF NOT EXISTS idx_machines_last_seen ON machines (last_seen);

DROP TRIGGER IF EXISTS trg_machines_updated_at ON machines;

CREATE TRIGGER trg_machines_updated_at
BEFORE UPDATE ON machines
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS metrics (
    id BIGSERIAL PRIMARY KEY,
    machine_id BIGINT NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    cpu_usage NUMERIC(5,2) NOT NULL,
    ram_usage NUMERIC(5,2) NOT NULL,
    disk_usage NUMERIC(5,2) NOT NULL,
    uptime_seconds BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT metrics_cpu_usage_check CHECK (cpu_usage BETWEEN 0 AND 100),
    CONSTRAINT metrics_ram_usage_check CHECK (ram_usage BETWEEN 0 AND 100),
    CONSTRAINT metrics_disk_usage_check CHECK (disk_usage BETWEEN 0 AND 100),
    CONSTRAINT metrics_uptime_seconds_check CHECK (uptime_seconds >= 0)
);

CREATE INDEX IF NOT EXISTS idx_metrics_machine_id ON metrics (machine_id);
CREATE INDEX IF NOT EXISTS idx_metrics_created_at ON metrics (created_at);
CREATE INDEX IF NOT EXISTS idx_metrics_machine_created_at ON metrics (machine_id, created_at);

CREATE TABLE IF NOT EXISTS installed_programs (
    id BIGSERIAL PRIMARY KEY,
    machine_id BIGINT NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(100),
    publisher VARCHAR(255),
    installed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT installed_programs_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT installed_programs_machine_name_version_unique UNIQUE (machine_id, name, version)
);

CREATE INDEX IF NOT EXISTS idx_installed_programs_machine_id ON installed_programs (machine_id);

DROP TRIGGER IF EXISTS trg_installed_programs_updated_at ON installed_programs;

CREATE TRIGGER trg_installed_programs_updated_at
BEFORE UPDATE ON installed_programs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS machine_local_admins (
    id BIGSERIAL PRIMARY KEY,
    machine_id BIGINT NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    admin_name VARCHAR(255) NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT machine_local_admins_name_not_blank CHECK (btrim(admin_name) <> ''),
    CONSTRAINT machine_local_admins_machine_admin_unique UNIQUE (machine_id, admin_name)
);

CREATE INDEX IF NOT EXISTS idx_machine_local_admins_machine_id ON machine_local_admins (machine_id);

CREATE TABLE IF NOT EXISTS security_events (
    id BIGSERIAL PRIMARY KEY,
    machine_id BIGINT REFERENCES machines(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    source VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT security_events_event_type_not_blank CHECK (btrim(event_type) <> ''),
    CONSTRAINT security_events_description_not_blank CHECK (btrim(description) <> ''),
    CONSTRAINT security_events_severity_check CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT security_events_source_check CHECK (source IN ('agent', 'api', 'system'))
);

CREATE INDEX IF NOT EXISTS idx_security_events_machine_id ON security_events (machine_id);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events (event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events (severity);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events (created_at);
CREATE INDEX IF NOT EXISTS idx_security_events_machine_created_at ON security_events (machine_id, created_at);

CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    machine_id BIGINT REFERENCES machines(id) ON DELETE SET NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    CONSTRAINT alerts_alert_type_not_blank CHECK (btrim(alert_type) <> ''),
    CONSTRAINT alerts_title_not_blank CHECK (btrim(title) <> ''),
    CONSTRAINT alerts_description_not_blank CHECK (btrim(description) <> ''),
    CONSTRAINT alerts_severity_check CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT alerts_status_check CHECK (status IN ('open', 'investigating', 'resolved', 'ignored')),
    CONSTRAINT alerts_resolved_at_check CHECK (
        (status IN ('resolved', 'ignored') AND resolved_at IS NOT NULL)
        OR (status IN ('open', 'investigating') AND resolved_at IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_alerts_machine_id ON alerts (machine_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts (created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_status_severity ON alerts (status, severity);

CREATE TABLE IF NOT EXISTS agent_configs (
    id BIGSERIAL PRIMARY KEY,
    machine_id BIGINT NOT NULL UNIQUE REFERENCES machines(id) ON DELETE CASCADE,
    agent_version VARCHAR(50),
    checkin_interval_minutes INTEGER NOT NULL DEFAULT 5,
    collect_inventory BOOLEAN NOT NULL DEFAULT true,
    collect_security BOOLEAN NOT NULL DEFAULT true,
    collect_metrics BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT agent_configs_checkin_interval_check CHECK (checkin_interval_minutes > 0)
);

DROP TRIGGER IF EXISTS trg_agent_configs_updated_at ON agent_configs;

CREATE TRIGGER trg_agent_configs_updated_at
BEFORE UPDATE ON agent_configs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;
