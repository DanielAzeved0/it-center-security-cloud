"use client";

import type { ReactNode } from "react";
import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { animateCountUp } from "@/lib/motion";

type StatCardProps = {
  label: string;
  value: string | number;
  detail: string;
};

export function StatCard({ label, value, detail }: StatCardProps) {
  const valueRef = useRef<HTMLElement>(null);

  useGSAP(
    () => {
      if (typeof value === "number") {
        animateCountUp(valueRef.current, value);
      }
    },
    { dependencies: [value], scope: valueRef },
  );

  return (
    <section className="stat-card">
      <span>{label}</span>
      <strong ref={valueRef}>{value}</strong>
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
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();

      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const tween = gsap.to(ref.current, {
          autoAlpha: 0.5,
          duration: 0.8,
          ease: "sine.inOut",
          repeat: -1,
          yoyo: true,
        });

        return () => {
          tween.kill();
        };
      });

      return () => mm.revert();
    },
    { scope: ref },
  );

  return (
    <div className="loading-block" ref={ref}>
      {label}...
    </div>
  );
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
