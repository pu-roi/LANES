/**
 * Custom API Error class for structured error handling
 */
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Centralized API client using native fetch for LANES platform.
 * To be used in combination with TanStack React Query.
 */
export const apiClient = {
  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  },
  
  async post<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    const isFormData = body instanceof FormData;
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      headers: {
        ...(!isFormData && body ? { 'Content-Type': 'application/json' } : {}),
        ...options?.headers,
      },
      body: body ? (isFormData || typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
    });
  },

  async put<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    const isFormData = body instanceof FormData;
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      headers: {
        ...(!isFormData && body ? { 'Content-Type': 'application/json' } : {}),
        ...options?.headers,
      },
      body: body ? (isFormData || typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
    });
  },

  async patch<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    const isFormData = body instanceof FormData;
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      headers: {
        ...(!isFormData && body ? { 'Content-Type': 'application/json' } : {}),
        ...options?.headers,
      },
      body: body ? (isFormData || typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
    });
  },

  async delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  },

  async request<T>(endpoint: string, options: RequestInit): Promise<T> {
    // We assume backend API is exposed via a local proxy or directly at /api/v1
    // Adjust base URL if needed depending on environment variables
    let baseUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!baseUrl) {
      if (typeof window !== "undefined") {
        baseUrl = "/api/v1"; // Uses Next.js rewrites to proxy to backend
      } else {
        baseUrl = "http://127.0.0.1:8000/api/v1"; // Server-side fetching
      }
    }
    const url = `${baseUrl}${endpoint}`; 
    
    // Inject JWT token if available
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("lanes_token");
      if (token) {
        options.headers = {
          ...options.headers,
          "Authorization": `Bearer ${token}`
        };
      }
    }
    
    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        if (response.status === 401 && typeof window !== "undefined") {
          localStorage.removeItem("lanes_token");
        }
        // Attempt to parse JSON error message from FastAPI if it exists
        let errorMsg = `API request failed with status ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMsg = Array.isArray(errorData.detail) 
              ? errorData.detail.map((e: any) => e.msg).join(", ") 
              : (typeof errorData.detail === 'object' ? JSON.stringify(errorData.detail) : String(errorData.detail));
          }
        } catch (e) {
          // Response wasn't JSON, ignore
        }
        throw new ApiError(response.status, errorMsg);
      }
      
      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      
      // Catch network failures (e.g., user lost 4G connection)
      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        throw new Error("You are offline. Please check your connection.");
      }
      throw new Error("A network error occurred. Please try again later.");
    }
  },

  async download(endpoint: string, filename: string): Promise<void> {
    let baseUrl = process.env.NEXT_PUBLIC_API_URL || '/api/v1';
    const url = `${baseUrl}${endpoint}`;
    const headers: Record<string, string> = {};
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('lanes_token');
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, { method: 'GET', headers });
    if (!response.ok) throw new Error('Download failed');
    const blob = await response.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(objectUrl);
  }
};
