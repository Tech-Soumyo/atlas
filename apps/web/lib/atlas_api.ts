export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export function getAtlasApiBaseUrl(): string {
  // Server side in Compose prefers the internal service DNS name.
  if (typeof window === "undefined") {
    return (
      process.env.ATLAS_API_INTERNAL_URL ??
      process.env.NEXT_PUBLIC_ATLAS_API_URL ??
      "http://localhost:8000"
    );
  }
  return process.env.NEXT_PUBLIC_ATLAS_API_URL ?? "http://localhost:8000";
}

export async function fetchApiHealth(): Promise<HealthResponse | null> {
  const baseUrl = getAtlasApiBaseUrl();
  try {
    const response = await fetch(`${baseUrl}/health`, {
      cache: "no-store",
      next: { revalidate: 0 },
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}
