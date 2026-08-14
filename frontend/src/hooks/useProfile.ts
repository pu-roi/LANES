import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { useAuth } from "@/hooks/useAuth";

export function useProfile() {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const updateProfileMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.patch('/users/me/profile', data);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth-user'] });
    },
  });

  const { data: myReports, isLoading: isLoadingReports } = useQuery({
    queryKey: ['my-reports', user?.id],
    queryFn: async () => {
      const response = await apiClient.get('/reports/me');
      return response;
    },
    enabled: !!user?.id,
  });

  const { data: myPosts, isLoading: isLoadingPosts } = useQuery({
    queryKey: ['my-posts', user?.id],
    queryFn: async () => {
      const response = await apiClient.get('/posts/me');
      return response;
    },
    enabled: !!user?.id,
  });

  return {
    updateProfile: updateProfileMutation.mutateAsync,
    isUpdatingProfile: updateProfileMutation.isPending,
    myReports,
    isLoadingReports,
    myPosts,
    isLoadingPosts,
  };
}
