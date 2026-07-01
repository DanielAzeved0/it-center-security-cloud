"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Shell } from "@/components/Shell";
import { EmptyState, ErrorState, LoadingBlock, StatusBadge, ToolbarButton } from "@/components/Ui";
import { formatDateTime, formatRelativeMinutes, formatUptime, requestBackend } from "@/lib/api";
import type { MachineDetail, MachineMetric, MachineProgram } from "@/lib/types";

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

export function MachineDetailView({ machineId }: { machineId: string }) {
  const parsedMachineId = Number(machineId);
  const validMachineId = Number.isInteger(parsedMachineId) && parsedMachineId > 0;

  const [detail, setDetail] = useState<MachineDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(true);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<SectionState<MachineMetric[]>>(emptyMetricsState);
  const [programs, setPrograms] = useState<SectionState<MachineProgram[]>>(emptyProgramsState);

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

  const loadAll = useCallback(() => {
    void loadDetail();
    void loadMetrics();
    void loadPrograms();
  }, [loadDetail, loadMetrics, loadPrograms]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const latestMetric = metrics.data[0];
  const lastSeenLabel = detail ? formatRelativeMinutes(detail.last_seen) : "sem check-in";
  const programsPreview = useMemo(() => programs.data.slice(0, 80), [programs.data]);

  return (
    <Shell
      title={detail?.hostname ?? "Detalhe da maquina"}
      subtitle="Resumo operacional, ultimo check-in, metricas recentes e programas instalados."
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

function formatMachineIdentity(username: string | null, ipAddress: string | null) {
  const user = formatOptionalText(username);
  const ip = formatOptionalText(ipAddress);
  return `${user} | ${ip}`;
}
