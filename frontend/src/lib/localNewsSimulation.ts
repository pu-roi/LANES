/** Local presentation session routing; all flood processing stays in FastAPI. */
export type LocalNewsSimulationMode = "september24" | "persisted";
let mode: Promise<LocalNewsSimulationMode | null> | undefined;

export function getLocalNewsSimulation(): Promise<LocalNewsSimulationMode | null> {
  if (typeof window === "undefined" || process.env.NODE_ENV !== "development"
      || !["localhost", "127.0.0.1"].includes(window.location.hostname)) return Promise.resolve(null);
  mode ??= fetch("/news-simulation.local.json", { cache: "no-store" }).then(async response => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error("The local simulation configuration could not be loaded.");
    const configuration = await response.json();
    if (configuration.mode === "persisted") {
      // The usual development port can host reconstruction. Storage is scoped
      // separately below so the normal login and flood cache remain intact.
      if (!["3000", "3001"].includes(configuration.port)) throw new Error("Persisted news simulation requires local port 3000 or 3001.");
      return window.location.port === configuration.port ? "persisted" as const : null;
    }
    return configuration.mode === "september24" ? "september24" as const : null;
  });
  return mode;
}

export async function getSessionStorageKey(key: string): Promise<string> {
  return await getLocalNewsSimulation() === "persisted" ? `${key}:news-reconstruction` : key;
}
