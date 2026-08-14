"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingBlock, Panel, SeverityBadge, StatCard, ToolbarButton } from "@/components/Ui";
import { formatDateTime, requestBackend } from "@/lib/api";
import { useStaggerEntrance } from "@/lib/motion";
import type { SecurityEvent } from "@/lib/types";

export function SecurityView() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [machineFilter, setMachineFilter] = useState("all");
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
  const severityOptions = useMemo(() => uniqueValues(events.map((event) => event.severity)), [events]);
  const typeOptions = useMemo(() => uniqueValues(events.map((event) => event.event_type)), [events]);
  const machineOptions = useMemo(
    () => uniqueValues(events.map((event) => (event.machine_id === null ? "sem-maquina" : String(event.machine_id)))),
    [events],
  );
  const filteredEvents = useMemo(
    () =>
      events.filter((event) => {
        const matchesSeverity = severityFilter === "all" || event.severity === severityFilter;
        const matchesType = typeFilter === "all" || event.event_type === typeFilter;
        const machineValue = event.machine_id === null ? "sem-maquina" : String(event.machine_id);
        const matchesMachine = machineFilter === "all" || machineValue === machineFilter;

        return matchesSeverity && matchesType && matchesMachine;
      }),
    [events, machineFilter, severityFilter, typeFilter],
  );
  const hasActiveFilters = severityFilter !== "all" || typeFilter !== "all" || machineFilter !== "all";

  const clearFilters = () => {
    setSeverityFilter("all");
    setTypeFilter("all");
    setMachineFilter("all");
  };

  const scopeRef = useStaggerEntrance([loading]);

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Seguranca</h1>
          <p>Eventos SOC Light recebidos ou gerados pelo sistema.</p>
        </div>
        <div className="header-actions">
          <ToolbarButton onClick={loadEvents}>Atualizar</ToolbarButton>
        </div>
      </header>

      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorState message={error} onRetry={loadEvents} /> : null}

      {!loading && !error ? (
        <div ref={scopeRef}>
          <section className="stats-grid" aria-label="Resumo de eventos">
            <StatCard tone="accent" label="Eventos" value={events.length} detail="registros de seguranca" />
            <StatCard tone="warning" label="Medium" value={severityCounts.medium} detail="eventos de atencao" />
            <StatCard tone="danger" label="High" value={severityCounts.high} detail="eventos importantes" />
            <StatCard tone="critical" label="Critical" value={severityCounts.critical} detail="acao imediata" />
          </section>

          <Panel title="Eventos recentes" meta={<span>{filteredEvents.length} de {events.length} eventos</span>}>
            <div className="filter-bar" aria-label="Filtros de eventos de seguranca">
              <label>
                Severidade
                <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>
                  <option value="all">Todas</option>
                  {severityOptions.map((severity) => (
                    <option key={severity} value={severity}>
                      {severity}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Tipo
                <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
                  <option value="all">Todos</option>
                  {typeOptions.map((eventType) => (
                    <option key={eventType} value={eventType}>
                      {eventType}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Maquina
                <select value={machineFilter} onChange={(event) => setMachineFilter(event.target.value)}>
                  <option value="all">Todas</option>
                  {machineOptions.map((machineId) => (
                    <option key={machineId} value={machineId}>
                      {machineId === "sem-maquina" ? "Sem maquina" : `ID ${machineId}`}
                    </option>
                  ))}
                </select>
              </label>
              <button className="secondary-button" type="button" disabled={!hasActiveFilters} onClick={clearFilters}>
                Limpar filtros
              </button>
            </div>

            {events.length === 0 ? (
              <EmptyState title="Sem eventos de seguranca" message="As coletas SOC Light ainda nao registraram eventos." />
            ) : filteredEvents.length === 0 ? (
              <EmptyState title="Nenhum evento encontrado" message="Ajuste os filtros para ampliar a busca." />
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
                    {filteredEvents.map((event) => (
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
          </Panel>
        </div>
      ) : null}
    </>
  );
}

function uniqueValues(values: string[]): string[] {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b, "pt-BR"));
}
