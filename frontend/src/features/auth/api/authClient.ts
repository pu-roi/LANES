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
  },

  loginWithGoogle: async (payload: {
    credential?: string;
    access_token?: string;
    mode?: "login" | "register";
    user?: any;
    profile?: any;
    address?: any;
  }) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    const res = await fetch(`${baseUrl}/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => null);
      throw new Error(errData?.detail || "Google authentication failed");
    }
    return await res.json();
  },

  requestPasswordResetOtp: async (email: string) => {
    return await apiClient.post<{ msg: string; cooldown_seconds: number }>("/auth/forgot-password/request-otp", { email });
  },

  verifyPasswordResetOtp: async (email: string, otp_code: string) => {
    return await apiClient.post<{ msg: string; reset_token: string }>("/auth/forgot-password/verify-otp", { email, otp_code });
  },

  resetPassword: async (reset_token: string, new_password: string) => {
    return await apiClient.post<{ msg: string }>("/auth/forgot-password/reset", { reset_token, new_password });
  }
};

