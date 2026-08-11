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
      return apiClient.post('/auth/test-token').catch(() => null);
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
          throw new Error("Too many requests. Please wait a minute before trying again.");
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
    // Clear user from cache
    queryClient.setQueryData(['auth-user'], null);
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
