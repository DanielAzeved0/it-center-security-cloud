"use client";

import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";

gsap.registerPlugin(useGSAP);

const ENTRANCE_SELECTOR = ".stat-card, .panel, .list-item, .machine-row, .table-wrap tbody tr";

export function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function useStaggerEntrance(dependencies: unknown[] = []) {
  const scopeRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();

      mm.add({ reduceMotion: "(prefers-reduced-motion: reduce)" }, (context) => {
        const { reduceMotion } = context.conditions as { reduceMotion: boolean };

        if (reduceMotion) {
          gsap.set(ENTRANCE_SELECTOR, { autoAlpha: 1, y: 0 });
          return;
        }

        gsap.from(ENTRANCE_SELECTOR, {
          autoAlpha: 0,
          y: 16,
          duration: 0.5,
          ease: "power2.out",
          stagger: 0.05,
        });
      });

      return () => mm.revert();
    },
    { scope: scopeRef, dependencies },
  );

  return scopeRef;
}

export function animateCountUp(element: HTMLElement | null, value: number, decimals = 0) {
  if (!element) {
    return;
  }

  if (prefersReducedMotion()) {
    element.textContent = value.toFixed(decimals);
    return;
  }

  const proxy = { value: 0 };
  gsap.to(proxy, {
    value,
    duration: 0.8,
    ease: "power2.out",
    onUpdate: () => {
      element.textContent = proxy.value.toFixed(decimals);
    },
  });
}

export function animateProgressValue(element: HTMLProgressElement | null, value: number) {
  if (!element) {
    return;
  }

  if (prefersReducedMotion()) {
    element.value = value;
    return;
  }

  gsap.fromTo(element, { value: 0 }, { value, duration: 0.8, ease: "power2.out" });
}
