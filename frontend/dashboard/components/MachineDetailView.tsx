"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Shell } from "@/components/Shell";
import { EmptyState, ErrorState, LoadingBlock, SeverityBadge, StatusBadge, ToolbarButton } from "@/components/Ui";
import { formatDateTime, formatRelativeMinutes, formatUptime, requestBackend } from "@/lib/api";
import type { AlertSummary, MachineDetail, MachineLocalAdmin, MachineMetric, MachineProgram, SecurityEvent } from "@/lib/types";

type SectionState<T> = {
  data: T;
  loading: boolean;
  error: string | null;
};

const emptyMetricsState: SectionState<MachineMetric[]> = {
  data: [],
  loading: true,
  error: null,
};

const emptyProgramsState: SectionState<MachineProgram[]> = {
  data: [],
  loading: true,
  error: null,
};

const emptyAdminsState: SectionState<MachineLocalAdmin[]> = {
  data: [],
  loading: true,
  error: null,
};

const emptyEventsState: SectionState<SecurityEvent[]> = {
  data: [],
  loading: true,
  error: null,
};

const emptyAlertsState: SectionState<AlertSummary[]> = {
  data: [],
  loading: true,
  error: null,
};

export function MachineDetailView({ machineId }: { machineId: string }) {
  const parsedMachineId = Number(machineId);
  const validMachineId = Number.isInteger(parsedMachineId) && parsedMachineId > 0;

  const [detail, setDetail] = useState<MachineDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(true);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<SectionState<MachineMetric[]>>(emptyMetricsState);
  const [programs, setPrograms] = useState<SectionState<MachineProgram[]>>(emptyProgramsState);
  const [admins, setAdmins] = useState<SectionState<MachineLocalAdmin[]>>(emptyAdminsState);
  const [events, setEvents] = useState<SectionState<SecurityEvent[]>>(emptyEventsState);
  const [alerts, setAlerts] = useState<SectionState<AlertSummary[]>>(emptyAlertsState);

  const loadDetail = useCallback(async () => {
    if (!validMachineId) {
      setDetail(null);
      setDetailLoading(false);
      setDetailError("Identificador de maquina invalido.");
      return;
    }

    setDetailLoading(true);
    setDetailError(null);

    try {
      const machineDetail = await requestBackend<MachineDetail>(`/api/v1/machines/${parsedMachineId}`);
      setDetail(machineDetail);
    } catch (err) {
      setDetail(null);
      setDetailError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setDetailLoading(false);
    }
  }, [parsedMachineId, validMachineId]);

  const loadMetrics = useCallback(async () => {
    if (!validMachineId) {
      setMetrics({ data: [], loading: false, error: null });
      return;
    }

    setMetrics((current) => ({ ...current, loading: true, error: null }));

    try {
      const metricList = await requestBackend<MachineMetric[]>(`/api/v1/machines/${parsedMachineId}/metrics`);
      setMetrics({ data: metricList, loading: false, error: null });
    } catch (err) {
      setMetrics({ data: [], loading: false, error: err instanceof Error ? err.message : "Erro inesperado" });
    }
  }, [parsedMachineId, validMachineId]);

  const loadPrograms = useCallback(async () => {
    if (!validMachineId) {
      setPrograms({ data: [], loading: false, error: null });
      return;
    }

    setPrograms((current) => ({ ...current, loading: true, error: null }));

    try {
      const programList = await requestBackend<MachineProgram[]>(`/api/v1/machines/${parsedMachineId}/programs`);
      setPrograms({ data: programList, loading: false, error: null });
    } catch (err) {
      setPrograms({ data: [], loading: false, error: err instanceof Error ? err.message : "Erro inesperado" });
    }
  }, [parsedMachineId, validMachineId]);

  const loadAdmins = useCallback(async () => {
    if (!validMachineId) {
      setAdmins({ data: [], loading: false, error: null });
      return;
    }

    setAdmins((current) => ({ ...current, loading: true, error: null }));

    try {
      const adminList = await requestBackend<MachineLocalAdmin[]>(`/api/v1/machines/${parsedMachineId}/admins`);
      setAdmins({ data: adminList, loading: false, error: null });
    } catch (err) {
      setAdmins({ data: [], loading: false, error: err instanceof Error ? err.message : "Erro inesperado" });
    }
  }, [parsedMachineId, validMachineId]);

  const loadEvents = useCallback(async () => {
    if (!validMachineId) {
      setEvents({ data: [], loading: false, error: null });
      return;
    }

    setEvents((current) => ({ ...current, loading: true, error: null }));

    try {
      const eventList = await requestBackend<SecurityEvent[]>("/api/v1/security-events");
      setEvents({
        data: eventList.filter((event) => event.machine_id === parsedMachineId),
        loading: false,
        error: null,
      });
    } catch (err) {
      setEvents({ data: [], loading: false, error: err instanceof Error ? err.message : "Erro inesperado" });
    }
  }, [parsedMachineId, validMachineId]);

  const loadAlerts = useCallback(async () => {
    if (!validMachineId) {
      setAlerts({ data: [], loading: false, error: null });
      return;
    }

    setAlerts((current) => ({ ...current, loading: true, error: null }));

    try {
      const alertList = await requestBackend<AlertSummary[]>("/api/v1/alerts");
      setAlerts({
        data: alertList.filter((alert) => alert.machine_id === parsedMachineId),
        loading: false,
        error: null,
      });
    } catch (err) {
      setAlerts({ data: [], loading: false, error: err instanceof Error ? err.message : "Erro inesperado" });
    }
  }, [parsedMachineId, validMachineId]);

  const loadAll = useCallback(() => {
    void loadDetail();
    void loadMetrics();
    void loadPrograms();
    void loadAdmins();
    void loadEvents();
    void loadAlerts();
  }, [loadAdmins, loadAlerts, loadDetail, loadEvents, loadMetrics, loadPrograms]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const latestMetric = metrics.data[0];
  const lastSeenLabel = detail ? formatRelativeMinutes(detail.last_seen) : "sem check-in";
  const programsPreview = useMemo(() => programs.data.slice(0, 80), [programs.data]);
  const metricHistory = useMemo(() => metrics.data.slice(0, 12), [metrics.data]);
  const metricSummary = useMemo(() => buildMetricSummary(metricHistory), [metricHistory]);
  const latestEvents = useMemo(() => events.data.slice(0, 10), [events.data]);
  const openAlerts = useMemo(() => alerts.data.filter((alert) => alert.status === "open"), [alerts.data]);

  return (
    <Shell
      title={detail?.hostname ?? "Detalhe da maquina"}
      subtitle="Resumo operacional, metricas, administradores locais, eventos e alertas da maquina."
      actions={
        <>
          <Link className="secondary-button" href="/machines">
            Voltar
          </Link>
          <ToolbarButton onClick={loadAll}>Atualizar</ToolbarButton>
        </>
      }
    >
      {detailLoading ? <LoadingBlock label="Carregando maquina" /> : null}
      {detailError ? <ErrorState message={detailError} onRetry={loadDetail} /> : null}

      {detail && !detailLoading ? (
        <section className="machine-detail-layout">
          <section className="panel machine-hero" aria-label="Resumo da maquina">
            <div className="machine-hero-main">
              <div>
                <span className="eyebrow">Maquina monitorada</span>
                <h2>{detail.hostname}</h2>
                <p>{formatMachineIdentity(detail.username, detail.ip_address)}</p>
              </div>
              <StatusBadge value={detail.status} />
            </div>
            <div className={`status-context ${detail.status.toLowerCase() === "online" ? "online" : "offline"}`}>
              <strong>{detail.status.toLowerCase() === "online" ? "Ativa na janela operacional" : "Fora da janela operacional"}</strong>
              <span>Ultima comunicacao: {lastSeenLabel}</span>
            </div>
            <dl className="detail-grid detail-grid-wide">
              <DetailItem label="Usuario" value={detail.username} />
              <DetailItem label="IP" value={detail.ip_address} />
              <DetailItem label="Sistema operacional" value={detail.operating_system} />
              <DetailItem label="Versao" value={detail.os_version} />
              <DetailItem label="Ultimo check-in" value={formatDateTime(detail.last_seen)} helper={lastSeenLabel} />
              <DetailItem label="ID interno" value={String(detail.id)} />
            </dl>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Alertas da maquina</h2>
              <span>{alerts.data.length} itens</span>
            </div>
            {alerts.loading ? <LoadingBlock label="Carregando alertas" /> : null}
            {alerts.error ? <SectionError message={alerts.error} onRetry={loadAlerts} /> : null}
            {!alerts.loading && !alerts.error && alerts.data.length === 0 ? (
              <EmptyState title="Sem alertas para esta maquina" message="Nenhum alerta foi associado a este ativo ate o momento." />
            ) : null}
            {!alerts.loading && !alerts.error && alerts.data.length > 0 ? (
              <div className="stack-list compact">
                {alerts.data.slice(0, 6).map((alert) => (
                  <article className="list-item" key={alert.id}>
                    <div>
                      <strong>{alert.title}</strong>
                      <p>{alert.description}</p>
                      <small>
                        {alert.alert_type} | {formatDateTime(alert.created_at)}
                      </small>
                    </div>
                    <div className="item-meta">
                      <SeverityBadge value={alert.severity} />
                      <StatusBadge value={alert.status} />
                    </div>
                  </article>
                ))}
              </div>
            ) : null}
            {!alerts.loading && !alerts.error && openAlerts.length > 0 ? (
              <p className="panel-note">{openAlerts.length} alerta(s) aberto(s) exigem acompanhamento na tela de Alertas.</p>
            ) : null}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Metricas recentes</h2>
              <span>{metrics.data.length} coletas</span>
            </div>
            {metrics.loading ? <LoadingBlock label="Carregando metricas" /> : null}
            {metrics.error ? <SectionError message={metrics.error} onRetry={loadMetrics} /> : null}
            {!metrics.loading && !metrics.error && latestMetric ? (
              <div className="metric-grid detail-metrics">
                <MetricTile label="CPU" value={latestMetric.cpu_usage} />
                <MetricTile label="RAM" value={latestMetric.ram_usage} />
                <MetricTile label="Disco" value={latestMetric.disk_usage} />
                <div className="uptime-box">
                  <span>Uptime</span>
                  <strong>{formatOptionalUptime(latestMetric.uptime_seconds)}</strong>
                  <small>{formatDateTime(latestMetric.created_at)}</small>
                </div>
              </div>
            ) : null}
            {!metrics.loading && !metrics.error && !latestMetric ? (
              <EmptyState title="Nenhuma metrica registrada" message="A maquina ainda nao enviou coletas de metricas." />
            ) : null}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Historico de metricas</h2>
              <span>ultimas {metricHistory.length} coletas</span>
            </div>
            {metrics.loading ? <LoadingBlock label="Carregando historico" /> : null}
            {metrics.error ? <SectionError message={metrics.error} onRetry={loadMetrics} /> : null}
            {!metrics.loading && !metrics.error && metricHistory.length === 0 ? (
              <EmptyState title="Sem historico" message="As coletas historicas aparecem depois dos proximos check-ins." />
            ) : null}
            {!metrics.loading && !metrics.error && metricHistory.length > 0 ? (
              <div className="metric-history">
                <div className="metric-summary-grid" aria-label="Resumo do historico de metricas">
                  <MetricSummaryItem label="CPU media" value={metricSummary.cpuAverage} />
                  <MetricSummaryItem label="RAM media" value={metricSummary.ramAverage} />
                  <MetricSummaryItem label="Disco medio" value={metricSummary.diskAverage} />
                  <MetricSummaryItem label="Pico de CPU" value={metricSummary.cpuPeak} />
                </div>
                <div className="table-wrap">
                  <table className="compact-table">
                    <thead>
                      <tr>
                        <th>Coleta</th>
                        <th>CPU</th>
                        <th>RAM</th>
                        <th>Disco</th>
                        <th>Uptime</th>
                      </tr>
                    </thead>
                    <tbody>
                      {metricHistory.map((metric, index) => (
                        <tr key={`${metric.created_at ?? "metric"}-${index}`}>
                          <td>{formatDateTime(metric.created_at)}</td>
                          <td>{formatOptionalPercent(metric.cpu_usage)}</td>
                          <td>{formatOptionalPercent(metric.ram_usage)}</td>
                          <td>{formatOptionalPercent(metric.disk_usage)}</td>
                          <td>{formatOptionalUptime(metric.uptime_seconds)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Programas instalados</h2>
              <span>{programs.data.length} itens</span>
            </div>
            {programs.loading ? <LoadingBlock label="Carregando programas" /> : null}
            {programs.error ? <SectionError message={programs.error} onRetry={loadPrograms} /> : null}
            {!programs.loading && !programs.error && programs.data.length === 0 ? (
              <EmptyState title="Nenhum programa registrado" message="O snapshot de programas ainda nao foi enviado." />
            ) : null}
            {!programs.loading && !programs.error && programs.data.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Nome</th>
                      <th>Versao</th>
                      <th>Publicador</th>
                    </tr>
                  </thead>
                  <tbody>
                    {programsPreview.map((program, index) => (
                      <tr key={`${program.name}-${program.version ?? "none"}-${index}`}>
                        <td>{program.name}</td>
                        <td>{formatOptionalText(program.version)}</td>
                        <td>{formatOptionalText(program.publisher)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Administradores locais</h2>
              <span>{admins.data.length} contas</span>
            </div>
            {admins.loading ? <LoadingBlock label="Carregando administradores" /> : null}
            {admins.error ? <SectionError message={admins.error} onRetry={loadAdmins} /> : null}
            {!admins.loading && !admins.error && admins.data.length === 0 ? (
              <EmptyState title="Sem administradores registrados" message="O baseline de administradores aparece apos o check-in com coleta de seguranca." />
            ) : null}
            {!admins.loading && !admins.error && admins.data.length > 0 ? (
              <div className="table-wrap">
                <table className="compact-table">
                  <thead>
                    <tr>
                      <th>Conta</th>
                      <th>Primeira deteccao</th>
                      <th>Ultima deteccao</th>
                    </tr>
                  </thead>
                  <tbody>
                    {admins.data.map((admin) => (
                      <tr key={admin.admin_name}>
                        <td>{admin.admin_name}</td>
                        <td>{formatDateTime(admin.first_seen_at)}</td>
                        <td>{formatDateTime(admin.last_seen_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Eventos de seguranca</h2>
              <span>{events.data.length} eventos</span>
            </div>
            {events.loading ? <LoadingBlock label="Carregando eventos" /> : null}
            {events.error ? <SectionError message={events.error} onRetry={loadEvents} /> : null}
            {!events.loading && !events.error && events.data.length === 0 ? (
              <EmptyState title="Sem eventos para esta maquina" message="Eventos SOC Light associados a este ativo aparecerao aqui." />
            ) : null}
            {!events.loading && !events.error && events.data.length > 0 ? (
              <div className="stack-list compact">
                {latestEvents.map((event) => (
                  <article className="list-item" key={event.id}>
                    <div>
                      <strong>{event.event_type}</strong>
                      <p>{event.description}</p>
                      <small>
                        Origem: {event.source} | {formatDateTime(event.created_at)}
                      </small>
                    </div>
                    <div className="item-meta">
                      <SeverityBadge value={event.severity} />
                    </div>
                  </article>
                ))}
              </div>
            ) : null}
          </section>
        </section>
      ) : null}
    </Shell>
  );
}

function DetailItem({ label, value, helper }: { label: string; value: string | null | undefined; helper?: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{formatOptionalText(value)}</dd>
      {helper ? <small>{helper}</small> : null}
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: number | null | undefined }) {
  const normalized = normalizePercent(value);

  return (
    <div className="metric-bar">
      <div>
        <span>{label}</span>
        <strong>{normalized.label}</strong>
      </div>
      <progress value={normalized.value} max={100} aria-label={`${label}: ${normalized.label}`} />
    </div>
  );
}

function MetricSummaryItem({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="metric-summary-item">
      <span>{label}</span>
      <strong>{formatOptionalPercent(value)}</strong>
    </div>
  );
}

function SectionError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="section-error" role="alert">
      <span>{message}</span>
      <button className="secondary-button" type="button" onClick={onRetry}>
        Tentar novamente
      </button>
    </div>
  );
}

function normalizePercent(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return { value: 0, label: "-" };
  }

  const normalized = Math.max(0, Math.min(100, value));
  return { value: normalized, label: `${normalized.toFixed(1)}%` };
}

function formatOptionalText(value: string | null | undefined) {
  return value && value.trim().length > 0 ? value : "-";
}

function formatOptionalUptime(value: number | null | undefined) {
  return typeof value === "number" && !Number.isNaN(value) ? formatUptime(value) : "-";
}

function formatOptionalPercent(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "-";
  }

  return `${Math.max(0, Math.min(100, value)).toFixed(1)}%`;
}

function formatMachineIdentity(username: string | null, ipAddress: string | null) {
  const user = formatOptionalText(username);
  const ip = formatOptionalText(ipAddress);
  return `${user} | ${ip}`;
}

function buildMetricSummary(history: MachineMetric[]) {
  return {
    cpuAverage: averageMetric(history, "cpu_usage"),
    ramAverage: averageMetric(history, "ram_usage"),
    diskAverage: averageMetric(history, "disk_usage"),
    cpuPeak: peakMetric(history, "cpu_usage"),
  };
}

function averageMetric(history: MachineMetric[], key: "cpu_usage" | "ram_usage" | "disk_usage") {
  const values = history
    .map((metric) => metric[key])
    .filter((value): value is number => typeof value === "number" && !Number.isNaN(value));

  if (values.length === 0) {
    return null;
  }

  return values.reduce((total, value) => total + value, 0) / values.length;
}

function peakMetric(history: MachineMetric[], key: "cpu_usage" | "ram_usage" | "disk_usage") {
  const values = history
    .map((metric) => metric[key])
    .filter((value): value is number => typeof value === "number" && !Number.isNaN(value));

  return values.length > 0 ? Math.max(...values) : null;
}
