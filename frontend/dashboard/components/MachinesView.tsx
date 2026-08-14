"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import { EmptyState, ErrorState, LoadingBlock, Panel, StatCard, StatusBadge, ToolbarButton } from "@/components/Ui";
import { formatDateTime, formatRelativeMinutes, formatUptime, requestBackend } from "@/lib/api";
import { animateProgressValue, useStaggerEntrance } from "@/lib/motion";
import type { MachineDetail, MachineMetric, MachineProgram, MachineSummary } from "@/lib/types";

type MachineSelection = {
  detail: MachineDetail;
  metrics: MachineMetric[];
  programs: MachineProgram[];
};

export function MachinesView() {
  const [machines, setMachines] = useState<MachineSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selection, setSelection] = useState<MachineSelection | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingSelection, setLoadingSelection] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMachines = useCallback(async () => {
    setLoadingList(true);
    setError(null);

    try {
      const machineList = await requestBackend<MachineSummary[]>("/api/v1/machines");
      setMachines(machineList);
      setSelectedId((current) => current ?? machineList[0]?.id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado");
    } finally {
      setLoadingList(false);
    }
  }, []);

  const loadSelection = useCallback(async (machineId: number) => {
    setLoadingSelection(true);
    setError(null);

    try {
      const [detail, metrics, programs] = await Promise.all([
        requestBackend<MachineDetail>(`/api/v1/machines/${machineId}`),
        requestBackend<MachineMetric[]>(`/api/v1/machines/${machineId}/metrics`),
        requestBackend<MachineProgram[]>(`/api/v1/machines/${machineId}/programs`),
      ]);

      setSelection({ detail, metrics, programs });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado");
      setSelection(null);
    } finally {
      setLoadingSelection(false);
    }
  }, []);

  useEffect(() => {
    void loadMachines();
  }, [loadMachines]);

  useEffect(() => {
    if (selectedId !== null) {
      void loadSelection(selectedId);
    } else {
      setSelection(null);
    }
  }, [loadSelection, selectedId]);

  const latestMetric = selection?.metrics[0];
  const onlineCount = useMemo(() => machines.filter((machine) => machine.status === "online").length, [machines]);
  const scopeRef = useStaggerEntrance([loadingList, selectedId, loadingSelection]);

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Maquinas</h1>
          <p>Inventario, metricas recentes e programas instalados.</p>
        </div>
        <div className="header-actions">
          <ToolbarButton onClick={loadMachines}>Atualizar</ToolbarButton>
        </div>
      </header>

      {loadingList ? <LoadingBlock /> : null}
      {error ? <ErrorState message={error} onRetry={loadMachines} /> : null}

      {!loadingList && !error && machines.length === 0 ? (
        <EmptyState title="Nenhuma maquina cadastrada" message="Execute o agente Windows para popular o inventario." />
      ) : null}

      {!loadingList && machines.length > 0 ? (
        <section className="content-grid machines-layout" ref={scopeRef}>
          <Panel title="Inventario" meta={<span>{machines.length} maquinas</span>}>
            <div className="machine-list" role="list">
              {machines.map((machine) => (
                <button
                  className={machine.id === selectedId ? "machine-row active" : "machine-row"}
                  key={machine.id}
                  type="button"
                  onClick={() => setSelectedId(machine.id)}
                >
                  <span>
                    <strong>{machine.hostname}</strong>
                    <small>{machine.username ?? "usuario nao informado"}</small>
                  </span>
                  <span>
                    <span className="item-meta">
                      <StatusBadge value={machine.status} />
                      {machine.rustdesk_id ? <span className="badge">RustDesk</span> : null}
                    </span>
                    <small>{formatRelativeMinutes(machine.last_seen)}</small>
                  </span>
                </button>
              ))}
            </div>
          </Panel>

          <div className="detail-column">
            <section className="stats-grid compact-stats" aria-label="Resumo de maquinas">
              <StatCard tone="accent" label="Total" value={machines.length} detail="maquinas registradas" />
              <StatCard label="Online" value={onlineCount} detail="com check-in recente" />
              <StatCard label="Offline" value={machines.length - onlineCount} detail="fora da janela atual" />
            </section>

            {loadingSelection ? <LoadingBlock label="Carregando maquina" /> : null}

            {selection && !loadingSelection ? (
              <>
                <Panel
                  title={selection.detail.hostname}
                  actions={
                    <>
                      <StatusBadge value={selection.detail.status} />
                      <Link className="secondary-button compact-button" href={`/machines/${selection.detail.id}`}>
                        Detalhes
                      </Link>
                    </>
                  }
                >
                  <dl className="detail-grid">
                    <div>
                      <dt>Usuario</dt>
                      <dd>{selection.detail.username ?? "-"}</dd>
                    </div>
                    <div>
                      <dt>IP</dt>
                      <dd>{selection.detail.ip_address ?? "-"}</dd>
                    </div>
                    <div>
                      <dt>Sistema</dt>
                      <dd>{selection.detail.operating_system ?? "-"}</dd>
                    </div>
                    <div>
                      <dt>Versao</dt>
                      <dd>{selection.detail.os_version ?? "-"}</dd>
                    </div>
                    <div>
                      <dt>Ultimo check-in</dt>
                      <dd>{formatDateTime(selection.detail.last_seen)}</dd>
                    </div>
                  </dl>
                </Panel>

                <Panel title="Metricas recentes" meta={<span>{selection.metrics.length} coletas</span>}>
                  {latestMetric ? (
                    <div className="metric-grid">
                      <MetricBar label="CPU" value={latestMetric.cpu_usage} />
                      <MetricBar label="RAM" value={latestMetric.ram_usage} />
                      <MetricBar label="Disco" value={latestMetric.disk_usage} />
                      <div className="uptime-box">
                        <span>Uptime</span>
                        <strong>{typeof latestMetric.uptime_seconds === "number" ? formatUptime(latestMetric.uptime_seconds) : "-"}</strong>
                      </div>
                    </div>
                  ) : (
                    <EmptyState title="Sem metricas" message="A maquina ainda nao enviou metricas." />
                  )}
                </Panel>

                <Panel title="Programas instalados" meta={<span>{selection.programs.length} itens</span>}>
                  {selection.programs.length === 0 ? (
                    <EmptyState title="Sem programas" message="O snapshot de programas ainda nao foi enviado." />
                  ) : (
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
                          {selection.programs.map((program, index) => (
                            <tr key={`${program.name}-${program.version ?? "none"}-${index}`}>
                              <td>{program.name}</td>
                              <td>{program.version ?? "-"}</td>
                              <td>{program.publisher ?? "-"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </Panel>
              </>
            ) : null}
          </div>
        </section>
      ) : null}
    </>
  );
}

function MetricBar({ label, value }: { label: string; value: number | null }) {
  const normalized = typeof value === "number" && !Number.isNaN(value) ? Math.max(0, Math.min(100, value)) : 0;
  const displayValue = typeof value === "number" && !Number.isNaN(value) ? `${normalized.toFixed(1)}%` : "-";
  const progressRef = useRef<HTMLProgressElement>(null);

  useGSAP(
    () => {
      animateProgressValue(progressRef.current, normalized);
    },
    { dependencies: [normalized], scope: progressRef },
  );

  return (
    <div className="metric-bar">
      <div>
        <span>{label}</span>
        <strong>{displayValue}</strong>
      </div>
      <progress ref={progressRef} value={normalized} max={100} aria-label={`${label}: ${displayValue}`} />
    </div>
  );
}
