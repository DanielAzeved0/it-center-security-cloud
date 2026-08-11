"use client";

import { useCallback, useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { EmptyState, ErrorState, LoadingBlock, SeverityBadge, StatCard, StatusBadge, ToolbarButton } from "@/components/Ui";
import { formatDateTime, formatRelativeMinutes, requestBackend } from "@/lib/api";
import { useStaggerEntrance } from "@/lib/motion";
import type { AlertSummary, MachineSummary, SecurityEvent } from "@/lib/types";

type DashboardData = {
  machines: MachineSummary[];
  alerts: AlertSummary[];
  events: SecurityEvent[];
};

export function DashboardView() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [machines, alerts, events] = await Promise.all([
        requestBackend<MachineSummary[]>("/api/v1/machines"),
        requestBackend<AlertSummary[]>("/api/v1/alerts"),
        requestBackend<SecurityEvent[]>("/api/v1/security-events"),
      ]);

      setData({ machines, alerts, events });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const machines = data?.machines ?? [];
  const alerts = data?.alerts ?? [];
  const events = data?.events ?? [];
  const onlineCount = machines.filter((machine) => machine.status === "online").length;
  const offlineCount = machines.filter((machine) => machine.status === "offline").length;
  const openAlerts = alerts.filter((alert) => alert.status === "open").length;
  const lastSeen = machines
    .map((machine) => machine.last_seen)
    .filter((value): value is string => Boolean(value))
    .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0];
  const scopeRef = useStaggerEntrance([loading]);

  return (
    <Shell
      title="Dashboard"
      subtitle="Visao operacional das maquinas, alertas e eventos recentes."
      actions={<ToolbarButton onClick={loadData}>Atualizar</ToolbarButton>}
    >
      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorState message={error} onRetry={loadData} /> : null}

      {!loading && !error && data ? (
        <div ref={scopeRef}>
          <section className="stats-grid" aria-label="Indicadores principais">
            <StatCard label="Maquinas" value={machines.length} detail={`${onlineCount} online, ${offlineCount} offline`} />
            <StatCard label="Online" value={onlineCount} detail="Ativas pelo ultimo check-in" />
            <StatCard label="Alertas abertos" value={openAlerts} detail={`${alerts.length} alertas no total`} />
            <StatCard label="Ultimo check-in" value={formatRelativeMinutes(lastSeen)} detail={formatDateTime(lastSeen)} />
          </section>

          <section className="content-grid two-columns">
            <div className="panel">
              <div className="panel-header">
                <h2>Maquinas recentes</h2>
              </div>
              {machines.length === 0 ? (
                <EmptyState title="Nenhuma maquina registrada" message="Execute o agente para enviar o primeiro check-in." />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Hostname</th>
                        <th>Status</th>
                        <th>Ultimo check-in</th>
                      </tr>
                    </thead>
                    <tbody>
                      {machines.slice(0, 6).map((machine) => (
                        <tr key={machine.id}>
                          <td>
                            <strong>{machine.hostname}</strong>
                            <span>{machine.ip_address ?? "-"}</span>
                          </td>
                          <td>
                            <StatusBadge value={machine.status} />
                          </td>
                          <td>{formatRelativeMinutes(machine.last_seen)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="panel">
              <div className="panel-header">
                <h2>Alertas recentes</h2>
              </div>
              {alerts.length === 0 ? (
                <EmptyState title="Sem alertas" message="Nenhum alerta foi registrado ate o momento." />
              ) : (
                <div className="stack-list">
                  {alerts.slice(0, 5).map((alert) => (
                    <article className="list-item" key={alert.id}>
                      <div>
                        <strong>{alert.title}</strong>
                        <p>{alert.description}</p>
                      </div>
                      <div className="item-meta">
                        <SeverityBadge value={alert.severity} />
                        <StatusBadge value={alert.status} />
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Eventos de seguranca</h2>
              <span>{events.length} eventos</span>
            </div>
            {events.length === 0 ? (
              <EmptyState title="Sem eventos" message="As regras SOC ainda nao registraram eventos." />
            ) : (
              <div className="stack-list compact">
                {events.slice(0, 8).map((event) => (
                  <article className="list-item" key={event.id}>
                    <div>
                      <strong>{event.event_type}</strong>
                      <p>{event.description}</p>
                    </div>
                    <div className="item-meta">
                      <SeverityBadge value={event.severity} />
                      <span>{formatDateTime(event.created_at)}</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      ) : null}
    </Shell>
  );
}
