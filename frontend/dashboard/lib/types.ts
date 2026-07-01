export type MachineSummary = {
  id: number;
  hostname: string;
  username: string | null;
  ip_address: string | null;
  status: "online" | "offline" | string;
  last_seen: string | null;
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

export type SecurityEvent = {
  id: number;
  machine_id: number | null;
  event_type: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  source: string;
  description: string;
  created_at: string;
};
