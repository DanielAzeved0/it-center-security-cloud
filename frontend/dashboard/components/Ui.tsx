import type { ReactNode } from "react";

type StatCardProps = {
  label: string;
  value: string | number;
  detail: string;
};

export function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <section className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </section>
  );
}

export function StatusBadge({ value }: { value: string }) {
  return <span className={`badge ${value.toLowerCase()}`}>{value}</span>;
}

export function SeverityBadge({ value }: { value: string }) {
  return <span className={`badge severity-${value.toLowerCase()}`}>{value}</span>;
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="error-state" role="alert">
      <div>
        <strong>Falha ao carregar dados</strong>
        <p>{message}</p>
      </div>
      <button className="secondary-button" type="button" onClick={onRetry}>
        Tentar novamente
      </button>
    </div>
  );
}

export function LoadingBlock({ label = "Carregando dados" }: { label?: string }) {
  return <div className="loading-block">{label}...</div>;
}

export function ToolbarButton({
  children,
  onClick,
  disabled,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button className="secondary-button" type="button" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}
