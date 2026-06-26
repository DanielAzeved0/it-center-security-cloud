"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Shell } from "@/components/Shell";
import { EmptyState, ErrorState, LoadingBlock, SeverityBadge, StatCard, StatusBadge, ToolbarButton } from "@/components/Ui";
import { formatDateTime, requestBackend } from "@/lib/api";
import type { AlertSummary } from "@/lib/types";

export function AlertsView() {
  const [alerts, setAlerts] = useState<AlertSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const payload = await requestBackend<AlertSummary[]>("/api/v1/alerts");
      setAlerts(payload);
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

  return (
    <Shell
      title="Alertas"
      subtitle="Fila de alertas gerados pelas regras de seguranca."
      actions={<ToolbarButton onClick={loadAlerts}>Atualizar</ToolbarButton>}
    >
      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorState message={error} onRetry={loadAlerts} /> : null}

      {!loading && !error ? (
        <>
          <section className="stats-grid" aria-label="Resumo de alertas">
            <StatCard label="Total" value={alerts.length} detail="alertas registrados" />
            <StatCard label="Abertos" value={openAlerts.length} detail="pendentes de acao" />
            <StatCard label="Alta severidade" value={highAlerts.length} detail="high ou critical" />
            <StatCard label="Resolvidos" value={resolvedAlerts} detail="finalizados" />
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Fila de alertas</h2>
              <span>{alerts.length} itens</span>
            </div>

            {alerts.length === 0 ? (
              <EmptyState title="Sem alertas" message="Nenhum alerta foi gerado ate o momento." />
            ) : (
              <div className="stack-list">
                {alerts.map((alert) => (
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
                        disabled={alert.status === "resolved" || resolvingId === alert.id}
                        onClick={() => void resolveAlert(alert.id)}
                      >
                        {resolvingId === alert.id ? "Resolvendo" : "Resolver"}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      ) : null}
    </Shell>
  );
}
