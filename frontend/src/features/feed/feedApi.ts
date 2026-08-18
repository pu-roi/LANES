import { apiClient } from '@/lib/apiClient';

export interface FeedPost {
  id: number;
  content: string;
  media_urls?: string[];
  location_tag?: string;
  created_at: string;
  
  upvotes: number;
  downvotes: number;
  distance_meters?: number;
  user_interaction?: 'upvote' | 'downvote';
  author_name?: string;
  author_avatar?: string;
  comment_count: number;
  
  report?: {
    id: number;
    raw_text: string;
    source: string;
    severity: 'low' | 'medium' | 'high' | 'extreme';
    status: string;
    media_urls?: string[];
    human_readable_location?: string;
    geometry?: {
      type: 'Point' | 'LineString';
      coordinates: number[] | number[][];
    };
  };
}

export interface FeedResponse {
  posts: FeedPost[];
  total: number;
  has_more: boolean;
}

export interface CommentResponse {
  id: number;
  content: string;
  created_at: string;
  edited_at?: string | null;
  author_name: string;
  parent_id?: number | null;
  upvotes: number;
  downvotes: number;
  user_interaction?: 'upvote' | 'downvote' | null;
  is_deleted?: boolean;
  is_pinned?: boolean;
  pinned_by?: string | null;
}

export interface TopReporter {
  rank: number;
  user_id: number;
  username: string;
  avatar_url: string | null;
  report_count: number;
}

export interface TopReportersResponse {
  reporters: TopReporter[];
}

export const getFeed = async (
  lat?: number, 
  lng?: number, 
  tab: 'recent' | 'nearby' = 'recent', 
  skip = 0, 
  limit = 20
): Promise<FeedResponse> => {
  const searchParams = new URLSearchParams();
  searchParams.append('tab', tab);
  searchParams.append('skip', skip.toString());
  searchParams.append('limit', limit.toString());
  
  if (lat !== undefined && lng !== undefined) {
    searchParams.append('lat', lat.toString());
    searchParams.append('lng', lng.toString());
  }
  
  return apiClient.get<FeedResponse>(`/feed?${searchParams.toString()}`);
};

export const votePost = async (postId: number, interactionType: 'upvote' | 'downvote') => {
  return apiClient.post(`/feed/${postId}/vote`, {
    post_id: postId,
    interaction_type: interactionType,
  });
};

export const getPost = async (postId: number): Promise<FeedPost> => {
  return apiClient.get<FeedPost>(`/posts/${postId}`);
};

export const getComments = async (postId: number): Promise<CommentResponse[]> => {
  return apiClient.get<CommentResponse[]>(`/posts/${postId}/comments`);
};

export const postComment = async (postId: number, content: string, parent_id?: number): Promise<CommentResponse> => {
  return apiClient.post<CommentResponse>(`/posts/${postId}/comments`, { content, parent_id });
};

export const deleteComment = async (commentId: number): Promise<void> => {
  await apiClient.delete(`/posts/comments/${commentId}`);
};

export const editComment = async (commentId: number, content: string): Promise<CommentResponse> => {
  return apiClient.patch<CommentResponse>(`/posts/comments/${commentId}`, { content });
};

export const pinComment = async (commentId: number): Promise<{ is_pinned: boolean; pinned_by: string | null }> => {
  return apiClient.post(`/posts/comments/${commentId}/pin`, {});
};

export const searchUsers = async (query: string): Promise<string[]> => {
  const result = await apiClient.get<{ usernames: string[] }>(`/users/search?q=${encodeURIComponent(query)}`);
  return result.usernames;
};

export const voteComment = async (commentId: number, interactionType: 'upvote' | 'downvote') => {
  return apiClient.post(`/posts/comments/${commentId}/vote`, {
    type: interactionType,
  });
};

export const getTopReporters = async (limit: number = 5): Promise<TopReportersResponse> => {
  return apiClient.get<TopReportersResponse>(`/feed/leaderboard?limit=${limit}`);
};

export interface CreatePostRequest {
  content: string;
  images?: File[];
  location_tag?: string;
}

export const createPost = async (request: CreatePostRequest): Promise<FeedPost> => {
  const formData = new FormData();
  formData.append('content', request.content);
  if (request.location_tag) {
    formData.append('location_tag', request.location_tag);
  }
  if (request.images && request.images.length > 0) {
    request.images.forEach((image) => {
      formData.append('images', image);
    });
  }
  return apiClient.post<FeedPost>(`/posts`, formData);
};

