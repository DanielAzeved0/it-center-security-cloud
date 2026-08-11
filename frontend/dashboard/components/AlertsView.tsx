"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Shell } from "@/components/Shell";
import { EmptyState, ErrorState, LoadingBlock, SeverityBadge, StatCard, StatusBadge, ToolbarButton } from "@/components/Ui";
import { formatDateTime, requestBackend } from "@/lib/api";
import { useStaggerEntrance } from "@/lib/motion";
import type { AlertSummary, AuthUser } from "@/lib/types";

export function AlertsView() {
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [machineFilter, setMachineFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolvingId, setResolvingId] = useState<number | null>(null);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [alertsPayload, userPayload] = await Promise.all([
        requestBackend<AlertSummary[]>("/api/v1/alerts"),
        requestBackend<{ user: AuthUser }>("/api/v1/auth/me"),
      ]);
      setAlerts(alertsPayload);
      setCurrentUser(userPayload.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAlerts();
  }, [loadAlerts]);

  const resolveAlert = async (alertId: number) => {
    setResolvingId(alertId);
    setError(null);

    try {
      await requestBackend<{ status: string; message: string }>(`/api/v1/alerts/${alertId}/resolve`, {
        method: "PATCH",
      });
      await loadAlerts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setResolvingId(null);
    }
  };

  const openAlerts = useMemo(() => alerts.filter((alert) => alert.status === "open"), [alerts]);
  const highAlerts = useMemo(
    () => alerts.filter((alert) => alert.severity === "high" || alert.severity === "critical"),
    [alerts],
  );
  const resolvedAlerts = alerts.filter((alert) => alert.status === "resolved").length;
  const severityOptions = useMemo(() => uniqueValues(alerts.map((alert) => alert.severity)), [alerts]);
  const typeOptions = useMemo(() => uniqueValues(alerts.map((alert) => alert.alert_type)), [alerts]);
  const machineOptions = useMemo(
    () => uniqueValues(alerts.map((alert) => (alert.machine_id === null ? "sem-maquina" : String(alert.machine_id)))),
    [alerts],
  );
  const filteredAlerts = useMemo(
    () =>
      alerts.filter((alert) => {
        const matchesSeverity = severityFilter === "all" || alert.severity === severityFilter;
        const matchesType = typeFilter === "all" || alert.alert_type === typeFilter;
        const machineValue = alert.machine_id === null ? "sem-maquina" : String(alert.machine_id);
        const matchesMachine = machineFilter === "all" || machineValue === machineFilter;

        return matchesSeverity && matchesType && matchesMachine;
      }),
    [alerts, machineFilter, severityFilter, typeFilter],
  );
  const hasActiveFilters = severityFilter !== "all" || typeFilter !== "all" || machineFilter !== "all";
  const canResolveAlerts = currentUser?.role === "admin" || currentUser?.role === "analyst";

  const clearFilters = () => {
    setSeverityFilter("all");
    setTypeFilter("all");
    setMachineFilter("all");
  };

  const scopeRef = useStaggerEntrance([loading]);

  return (
    <Shell
      title="Alertas"
      subtitle="Fila de alertas gerados pelas regras de seguranca."
      actions={<ToolbarButton onClick={loadAlerts}>Atualizar</ToolbarButton>}
    >
      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorState message={error} onRetry={loadAlerts} /> : null}

      {!loading && !error ? (
        <div ref={scopeRef}>
          <section className="stats-grid" aria-label="Resumo de alertas">
            <StatCard label="Total" value={alerts.length} detail="alertas registrados" />
            <StatCard label="Abertos" value={openAlerts.length} detail="pendentes de acao" />
            <StatCard label="Alta severidade" value={highAlerts.length} detail="high ou critical" />
            <StatCard label="Resolvidos" value={resolvedAlerts} detail="finalizados" />
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Fila de alertas</h2>
              <span>{filteredAlerts.length} de {alerts.length} itens</span>
            </div>

            <div className="filter-bar" aria-label="Filtros de alertas">
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
                  {typeOptions.map((alertType) => (
                    <option key={alertType} value={alertType}>
                      {alertType}
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

            {alerts.length === 0 ? (
              <EmptyState title="Sem alertas" message="Nenhum alerta foi gerado ate o momento." />
            ) : filteredAlerts.length === 0 ? (
              <EmptyState title="Nenhum alerta encontrado" message="Ajuste os filtros para ampliar a busca." />
            ) : (
              <div className="stack-list">
                {filteredAlerts.map((alert) => (
                  <article className="list-item alert-item" key={alert.id}>
                    <div>
                      <strong>{alert.title}</strong>
                      <p>{alert.description}</p>
                      <small>
                        Tipo: {alert.alert_type} | Maquina: {alert.machine_id ?? "-"} | {formatDateTime(alert.created_at)}
                      </small>
                    </div>
                    <div className="item-meta">
                      <SeverityBadge value={alert.severity} />
                      <StatusBadge value={alert.status} />
                      <button
                        className="primary-button"
                        type="button"
                        disabled={!canResolveAlerts || alert.status === "resolved" || resolvingId === alert.id}
                        onClick={() => void resolveAlert(alert.id)}
                        title={!canResolveAlerts ? "Seu perfil nao pode resolver alertas" : undefined}
                      >
                        {resolvingId === alert.id ? "Resolvendo" : "Resolver"}
                      </button>
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

function uniqueValues(values: string[]): string[] {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b, "pt-BR"));
}
