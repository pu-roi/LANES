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
    onMutate: async (newData: any) => {
      await queryClient.cancelQueries({ queryKey: ['auth-user'] });
      const previousUser = queryClient.getQueryData(['auth-user']);
      queryClient.setQueryData(['auth-user'], (oldUser: any) => {
        if (!oldUser) return oldUser;
        const updatedUsername = newData.username || oldUser.username;
        return {
          ...oldUser,
          username: updatedUsername,
          profile: {
            ...(oldUser.profile || {}),
            ...newData,
          },
        };
      });
      return { previousUser };
    },
    onError: (_err, _newData, context: any) => {
      if (context?.previousUser) {
        queryClient.setQueryData(['auth-user'], context.previousUser);
      }
    },
    onSuccess: (result: any) => {
      queryClient.setQueryData(['auth-user'], (oldUser: any) => {
        if (!oldUser) return oldUser;
        if (result && result.username && result.role) {
          return {
            ...oldUser,
            ...result,
            profile: result.profile || oldUser.profile,
          };
        }
        return {
          ...oldUser,
          profile: {
            ...(oldUser.profile || {}),
            ...result,
          },
        };
      });
      queryClient.invalidateQueries({ queryKey: ['auth-user'] });
      queryClient.invalidateQueries({ queryKey: ['my-posts'] });
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });

  const uploadAvatarMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post('/users/me/avatar', formData);
      return response;
    },
    onSuccess: (updatedProfile: any) => {
      queryClient.setQueryData(['auth-user'], (oldUser: any) => {
        if (!oldUser) return oldUser;
        return {
          ...oldUser,
          profile: {
            ...(oldUser.profile || {}),
            ...updatedProfile,
          },
        };
      });
      queryClient.invalidateQueries({ queryKey: ['auth-user'] });
      queryClient.invalidateQueries({ queryKey: ['my-posts'] });
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
  });

  const removeAvatarMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.delete('/users/me/avatar');
      return response;
    },
    onSuccess: (updatedProfile: any) => {
      queryClient.setQueryData(['auth-user'], (oldUser: any) => {
        if (!oldUser) return oldUser;
        return {
          ...oldUser,
          profile: {
            ...(oldUser.profile || {}),
            ...updatedProfile,
          },
        };
      });
      queryClient.invalidateQueries({ queryKey: ['auth-user'] });
      queryClient.invalidateQueries({ queryKey: ['my-posts'] });
      queryClient.invalidateQueries({ queryKey: ['posts'] });
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

  const deleteAccountMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.delete('/users/me');
      return response;
    },
    onSuccess: () => {
      queryClient.clear();
    },
  });

  const requestPasswordOtpMutation = useMutation({
    mutationFn: async (payload: { current_password: string }) => {
      const response = await apiClient.post<{ message: string; cooldown_seconds: number; email: string }>(
        '/users/me/password/request-otp',
        payload
      );
      return response;
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: async (payload: { current_password: string; new_password: string; otp_code: string }) => {
      const response = await apiClient.put('/users/me/password', payload);
      return response;
    },
  });

  return {
    updateProfile: updateProfileMutation.mutateAsync,
    isUpdatingProfile: updateProfileMutation.isPending,
    uploadAvatar: uploadAvatarMutation.mutateAsync,
    isUploadingAvatar: uploadAvatarMutation.isPending,
    removeAvatar: removeAvatarMutation.mutateAsync,
    isRemovingAvatar: removeAvatarMutation.isPending,
    deleteAccount: deleteAccountMutation.mutateAsync,
    isDeletingAccount: deleteAccountMutation.isPending,
    requestPasswordOtp: requestPasswordOtpMutation.mutateAsync,
    isRequestingPasswordOtp: requestPasswordOtpMutation.isPending,
    changePassword: changePasswordMutation.mutateAsync,
    isChangingPassword: changePasswordMutation.isPending,
    myReports,
    isLoadingReports,
    myPosts,
    isLoadingPosts,
  };
}

