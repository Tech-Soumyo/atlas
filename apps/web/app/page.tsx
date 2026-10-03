import { fetchApiHealth, getAtlasApiBaseUrl } from "../lib/atlas_api";

export default async function Home() {
  const health = await fetchApiHealth();
  const apiBase = getAtlasApiBaseUrl();

  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-zinc-50 px-6 py-16 font-sans text-zinc-900">
      <main className="w-full max-w-xl">
        <p className="text-sm font-medium tracking-wide text-zinc-500 uppercase">
          Atlas
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
          RAG foundations shell
        </h1>
        <p className="mt-3 text-base leading-7 text-zinc-600">
          M0 checks that the Next.js app can reach the FastAPI health endpoint.
        </p>

        <section
          className="mt-8 border border-zinc-200 bg-white p-5"
          aria-live="polite"
        >
          <h2 className="text-sm font-medium text-zinc-500">API health</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Base URL</dt>
              <dd className="font-mono text-zinc-800">{apiBase}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Status</dt>
              <dd className="font-medium">
                {health ? health.status : "unreachable"}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Service</dt>
              <dd>{health?.service ?? "—"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-500">Version</dt>
              <dd className="font-mono">{health?.version ?? "—"}</dd>
            </div>
          </dl>
        </section>
      </main>
    </div>
  );
}
