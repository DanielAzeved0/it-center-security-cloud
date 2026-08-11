"use client";

import { useCallback, useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { EmptyState, ErrorState, LoadingBlock, SeverityBadge, StatCard, ToolbarButton } from "@/components/Ui";
import { downloadBackendFile, formatDateTime, requestBackend } from "@/lib/api";
import { useStaggerEntrance } from "@/lib/motion";
import type { DashboardSummary } from "@/lib/types";

export function ExecutiveDashboardView() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const payload = await requestBackend<DashboardSummary>("/api/v1/dashboard/summary");
      setSummary(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  const exportPdf = async () => {
    setExporting(true);
    setExportError(null);

    try {
      await downloadBackendFile("/api/v1/reports/executive.pdf", "relatorio-executivo.pdf");
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Erro inesperado ao gerar o PDF");
    } finally {
      setExporting(false);
    }
  };

  const severity = summary?.alerts_open_by_severity;
  const scopeRef = useStaggerEntrance([loading]);

  return (
    <Shell
      title="Dashboard Executivo"
      subtitle="Visao resumida de maquinas, alertas por severidade e eventos recentes."
      actions={
        <>
          <ToolbarButton onClick={loadSummary}>Atualizar</ToolbarButton>
          <button className="primary-button" type="button" disabled={exporting || !summary} onClick={exportPdf}>
            {exporting ? "Gerando PDF" : "Exportar PDF"}
          </button>
        </>
      }
    >
      {loading ? <LoadingBlock /> : null}
      {error ? <ErrorState message={error} onRetry={loadSummary} /> : null}
      {exportError ? <div className="form-error" role="alert">{exportError}</div> : null}

      {!loading && !error && summary ? (
        <div ref={scopeRef}>
          <section className="stats-grid" aria-label="Indicadores executivos">
            <StatCard
              label="Maquinas"
              value={summary.machines_total}
              detail={`${summary.machines_online} online, ${summary.machines_offline} offline`}
            />
            <StatCard label="Alertas abertos" value={summary.alerts_open_total} detail="Aguardando acao" />
            <StatCard label="Eventos recentes" value={summary.recent_events.length} detail="Ultimas coletas" />
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Alertas abertos por severidade</h2>
            </div>
            {summary.alerts_open_total === 0 || !severity ? (
              <EmptyState title="Sem alertas abertos" message="Nenhum alerta esta pendente de acao." />
            ) : (
              <div className="stats-grid" aria-label="Alertas por severidade">
                <StatCard label="Baixa" value={severity.low} detail="severidade low" />
                <StatCard label="Media" value={severity.medium} detail="severidade medium" />
                <StatCard label="Alta" value={severity.high} detail="severidade high" />
                <StatCard label="Critica" value={severity.critical} detail="severidade critical" />
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Eventos de seguranca recentes</h2>
              <span>{summary.recent_events.length} eventos</span>
            </div>
            {summary.recent_events.length === 0 ? (
              <EmptyState title="Sem eventos" message="As regras SOC ainda nao registraram eventos." />
            ) : (
              <div className="stack-list compact">
                {summary.recent_events.map((event) => (
                  <article className="list-item" key={event.id}>
                    <div>
                      <strong>{event.event_type}</strong>
                      <p>{event.description}</p>
                      <small>Maquina: {event.machine_id ?? "-"}</small>
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
