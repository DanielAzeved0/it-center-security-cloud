export type MachineSummary = {
  id: number;
  hostname: string;
  username: string | null;
  ip_address: string | null;
  mac_address: string | null;
  serial_number: string | null;
  status: "online" | "offline" | string;
  last_seen: string | null;
  rustdesk_id: string | null;
};

export type MachineDetail = MachineSummary & {
  operating_system: string | null;
  os_version: string | null;
};

export type MachineMetric = {
  cpu_usage: number | null;
  ram_usage: number | null;
  disk_usage: number | null;
  uptime_seconds: number | null;
  created_at: string | null;
};

export type MachineProgram = {
  name: string;
  version: string | null;
  publisher: string | null;
};

export type MachineLocalAdmin = {
  admin_name: string;
  first_seen_at: string;
  last_seen_at: string;
};

export type AlertSummary = {
  id: number;
  machine_id: number | null;
  alert_type: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  status: "open" | "investigating" | "resolved" | "ignored" | string;
  title: string;
  description: string;
  created_at: string;
};

export type AuthUser = {
  id: number;
  email: string;
  name: string;
  role: "admin" | "analyst" | "viewer";
};

export type LoginResponse = {
  user: AuthUser;
};

export type SecurityEvent = {
  id: number;
  machine_id: number | null;
  event_type: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  source: string;
  description: string;
  created_at: string;
};

export type AlertSeverityCounts = {
  low: number;
  medium: number;
  high: number;
  critical: number;
};

export type DashboardSummary = {
  machines_total: number;
  machines_online: number;
  machines_offline: number;
  alerts_open_total: number;
  alerts_open_by_severity: AlertSeverityCounts;
  recent_events: SecurityEvent[];
};
