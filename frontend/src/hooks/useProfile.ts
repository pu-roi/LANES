import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";

export function useProfile() {
  const queryClient = useQueryClient();

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
    queryKey: ['my-reports'],
    queryFn: async () => {
      const response = await apiClient.get('/reports/me');
      return response;
    },
  });

  const { data: myPosts, isLoading: isLoadingPosts } = useQuery({
    queryKey: ['my-posts'],
    queryFn: async () => {
      const response = await apiClient.get('/posts/me');
      return response;
    },
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
