export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function requestBackend<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/backend${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Falha na API (${response.status})`;

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Mantem a mensagem padrao quando a resposta nao for JSON.
    }

    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

export async function downloadBackendFile(path: string, fallbackFilename: string): Promise<void> {
  const response = await fetch(`/api/backend${path}`, { cache: "no-store" });

  if (!response.ok) {
    let message = `Falha ao gerar arquivo (${response.status})`;

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Mantem a mensagem padrao quando a resposta nao for JSON.
    }

    throw new ApiError(message, response.status);
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const filenameMatch = disposition.match(/filename="([^"]+)"/);
  const filename = filenameMatch ? filenameMatch[1] : fallbackFilename;

  const blob = await response.blob();
  const downloadUrl = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(downloadUrl);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

export function formatRelativeMinutes(value: string | null | undefined): string {
  if (!value) {
    return "sem check-in";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "sem check-in";
  }

  const minutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000));

  if (minutes < 1) {
    return "agora";
  }

  if (minutes === 1) {
    return "ha 1 min";
  }

  return `ha ${minutes} min`;
}

export function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) {
    return `${days}d ${hours}h`;
  }

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  return `${minutes}m`;
}
