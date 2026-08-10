import { apiClient } from '@/lib/apiClient';

export interface SavedPlace {
    id: number;
    user_id: number;
    name: string;
    icon: string;
    address?: string;
    latitude: number;
    longitude: number;
    created_at: string;
}

export interface SavedPlaceCreate {
    name: string;
    icon: string;
    address?: string;
    latitude: number;
    longitude: number;
}

export const savedPlacesApi = {
    getSavedPlaces: async (): Promise<SavedPlace[]> => {
        const response = await apiClient.get<SavedPlace[]>('/users/me/places');
        return response;
    },

    createSavedPlace: async (data: SavedPlaceCreate): Promise<SavedPlace> => {
        const response = await apiClient.post<SavedPlace>('/users/me/places', data);
        return response;
    },

    deleteSavedPlace: async (id: number): Promise<void> => {
        await apiClient.delete(`/users/me/places/${id}`);
    }
};
