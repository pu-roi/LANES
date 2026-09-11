"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";

export function useAuth() {
  const queryClient = useQueryClient();

  // 1. Fetch user profile
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth-user'],
    queryFn: async () => {
      // Return null if no token is found in localStorage to avoid unnecessary API requests
      if (typeof window !== 'undefined' && !localStorage.getItem('lanes_token')) {
        return null;
      }
      return apiClient.post('/auth/test-token').catch(() => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('lanes_token');
        }
        return null;
      });
    },
    retry: false, // Don't retry auth checks if unauthorized
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // 2. Login Mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: URLSearchParams) => {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const response = await fetch(`${baseUrl}/auth/login/access-token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: credentials.toString(),
      });

      if (!response.ok) {
        if (response.status === 429) {
          const retryAfterSeconds = Math.max(1, Math.ceil(Number(response.headers.get("Retry-After")) || 60));
          const minutes = Math.floor(retryAfterSeconds / 60);
          const seconds = retryAfterSeconds % 60;
          const waitTime = minutes > 0
            ? `${minutes} minute${minutes === 1 ? "" : "s"}${seconds > 0 ? ` and ${seconds} second${seconds === 1 ? "" : "s"}` : ""}`
            : `${seconds} second${seconds === 1 ? "" : "s"}`;
          throw new Error(`Too many requests. Try again in ${waitTime}.`);
        }
        const errorData = await response.json().catch(() => null);
        if (errorData?.detail?.code === "UNVERIFIED_ACCOUNT") {
          throw new Error(JSON.stringify(errorData.detail));
        }
        throw new Error(errorData?.detail || "Incorrect username or password");
      }

      return response.json();
    },
    onSuccess: async (data) => {
      // Save token
      localStorage.setItem("lanes_token", data.access_token);
      // Invalidate the auth-user cache so it immediately re-fetches the user
      await queryClient.invalidateQueries({ queryKey: ['auth-user'] });
    },
  });

  // 3. Logout function
  const logout = () => {
    localStorage.removeItem("lanes_token");
    // Immediately push null into the auth-user cache so all subscribers (FloatingNav,
    // ProfileView, etc.) re-render RIGHT AWAY without waiting for a re-fetch.
    // queryClient.clear() removes the cache but does NOT notify React Query observers,
    // which is why the UI appeared "stuck" until a manual page refresh.
    queryClient.setQueryData(['auth-user'], null);
    // Wipe all other cached data (feed, notifications, saved places, etc.) so stale
    // data from the previous session doesn't bleed through on the next login.
    queryClient.removeQueries();
  };

  return {
    user: user as any,
    isAuthenticated: !!user,
    isLoading,
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    logout,
  };
}
