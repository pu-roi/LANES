import { apiClient } from "@/lib/apiClient";

export interface ProfileCreate {
  first_name: string;
  last_name: string;
  middle_initial?: string;
  suffix?: string;
  contact_number?: string;
  birthdate?: string;
}

export interface AddressCreate {
  house_number?: string;
  street?: string;
  barangay: string;
  city_municipality: string;
  province: string;
  postal_code?: string;
  country?: string;
}

export interface RegistrationRequest {
  user: {
    username: string;
    email: string;
    password: string;
  };
  profile: ProfileCreate;
  address: AddressCreate;
}

export const authClient = {
  register: async (data: RegistrationRequest) => {
    return await apiClient.post("/auth/register", data);
  },

  verifyOtp: async (email: string, otpCode: string) => {
    return await apiClient.post("/auth/verify-otp", { email, otp_code: otpCode });
  },

  resendOtp: async (email: string) => {
    return await apiClient.post("/auth/resend-otp", { email });
  }
};
