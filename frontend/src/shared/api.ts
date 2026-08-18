// Base fetch or axios interceptor for API calls to FastAPI
// Using standard Fetch API as a placeholder

const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
const BASE_URL = (envApiUrl && !envApiUrl.startsWith("encrypted:")) 
  ? envApiUrl 
  : "http://localhost:8000/api/v1";

export const apiClient = {
  get: async (endpoint: string) => {
    const response = await fetch(`${BASE_URL}${endpoint}`);
    if (!response.ok) throw new Error("API Route Failure");
    return response.json();
  },
  post: async <T>(endpoint: string, body: unknown): Promise<T> => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error("API Route Failure");
    return response.json() as Promise<T>;
  },
};
