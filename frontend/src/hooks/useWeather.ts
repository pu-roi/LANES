import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';

export interface WeatherData {
  temp: number | string;
  feels_like: number | string;
  condition: string;
  icon: string;
  location: string;
  precip_mm?: number;
  showers_mm?: number;
}

export function useWeather() {
  return useQuery({
    queryKey: ['current-weather'],
    queryFn: async () => {
      // 1. Check if we have a valid cache in localStorage (prevents API call on hard reload)
      if (typeof window !== 'undefined') {
        const cached = localStorage.getItem('lanes_weather_cache_v3');
        if (cached) {
          try {
            const { data, timestamp } = JSON.parse(cached);
            // Cache is valid for 15 minutes
            if (Date.now() - timestamp < 15 * 60 * 1000) {
              return data as WeatherData;
            }
          } catch (e) {
            console.warn("Failed to parse weather cache");
          }
        }
      }

      // 2. Fetch fresh data from API
      const data = await apiClient.get<WeatherData>("/weather/current");
      
      // 3. Cache the successful result
      if (typeof window !== 'undefined') {
        localStorage.setItem('lanes_weather_cache_v3', JSON.stringify({
          data,
          timestamp: Date.now()
        }));
      }
      
      return data;
    },
    staleTime: 15 * 60 * 1000, // 15 minutes cache in React Query
    refetchOnWindowFocus: false, // Don't refetch automatically when switching tabs
  });
}
