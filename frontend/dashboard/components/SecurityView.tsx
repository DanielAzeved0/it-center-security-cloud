"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Shell } from "@/components/Shell";
import { EmptyState, ErrorState, LoadingBlock, SeverityBadge, StatCard, ToolbarButton } from "@/components/Ui";
import { formatDateTime, requestBackend } from "@/lib/api";
import type { SecurityEvent } from "@/lib/types";

export function SecurityView() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const payload = await requestBackend<SecurityEvent[]>("/api/v1/security-events");
      setEvents(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  const severityCounts = useMemo(
    () => ({
      low: events.filter((event) => event.severity === "low").length,
      medium: events.filter((event) => event.severity === "medium").length,
      high: events.filter((event) => event.severity === "high").length,
      critical: events.filter((event) => event.severity === "critical").length,
    }),
    [events],
  );

  return (
    <Shell
      title="Seguranca"
      subtitle="Eventos SOC Light recebidos ou gerados pelo sistema."
      actions={<ToolbarButton onClick={loadEvents}>Atualizar</ToolbarButton>}
    >
      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorState message={error} onRetry={loadEvents} /> : null}

      {!loading && !error ? (
        <>
          <section className="stats-grid" aria-label="Resumo de eventos">
            <StatCard label="Eventos" value={events.length} detail="registros de seguranca" />
            <StatCard label="Medium" value={severityCounts.medium} detail="eventos de atencao" />
            <StatCard label="High" value={severityCounts.high} detail="eventos importantes" />
            <StatCard label="Critical" value={severityCounts.critical} detail="acao imediata" />
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Eventos recentes</h2>
              <span>{severityCounts.low} low</span>
            </div>

            {events.length === 0 ? (
              <EmptyState title="Sem eventos de seguranca" message="As coletas SOC Light ainda nao registraram eventos." />
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Evento</th>
                      <th>Severidade</th>
                      <th>Origem</th>
                      <th>Maquina</th>
                      <th>Data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((event) => (
                      <tr key={event.id}>
                        <td>
                          <strong>{event.event_type}</strong>
                          <span>{event.description}</span>
                        </td>
                        <td>
                          <SeverityBadge value={event.severity} />
                        </td>
                        <td>{event.source}</td>
                        <td>{event.machine_id ?? "-"}</td>
                        <td>{formatDateTime(event.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      ) : null}
    </Shell>
  );
}
