import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/api';

export interface HotlineNumber {
  raw: string;
  display: string;
}

export interface HotlineGroup {
  name: string;
  numbers: HotlineNumber[];
}

export interface FullHotlineData {
  national: HotlineGroup[];
  pasig_city: HotlineGroup[];
  pasig_barangay: HotlineGroup[];
}

// --- Sidebar widget: only national hotlines ---
const fetchHotlines = async (): Promise<HotlineGroup[]> => {
  return apiClient.get('/hotlines/');
};

export const useHotlines = () => {
  return useQuery({
    queryKey: ['hotlines'],
    queryFn: fetchHotlines,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};

// --- Full directory modal: all hotlines (lazy, only fetched when modal opens) ---
const fetchFullHotlines = async (): Promise<FullHotlineData> => {
  return apiClient.get('/hotlines/full');
};

export const useFullHotlines = (enabled: boolean) => {
  return useQuery({
    queryKey: ['hotlines-full'],
    queryFn: fetchFullHotlines,
    staleTime: 1000 * 60 * 60, // 1 hour
    enabled,
  });
};
