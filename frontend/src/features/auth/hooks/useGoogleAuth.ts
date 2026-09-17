"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/shared/ui";
import { authClient } from "../api/authClient";

declare global {
  interface Window {
    google?: any;
  }
}

export interface GoogleUserProfile {
  access_token: string;
  email: string;
  given_name?: string;
  family_name?: string;
  name?: string;
  picture?: string;
}

export function useGoogleAuth() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { success, error: showError, info } = useToast();
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isGsiLoaded, setIsGsiLoaded] = useState(false);
  const tokenClientRef = useRef<any>(null);

  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

  // Load Google Identity Services script
  useEffect(() => {
    if (typeof window === "undefined") return;

    if (window.google?.accounts?.oauth2) {
      setIsGsiLoaded(true);
      return;
    }

    const existingScript = document.getElementById("google-identity-services");
    if (existingScript) {
      existingScript.addEventListener("load", () => setIsGsiLoaded(true));
      return;
    }

    const script = document.createElement("script");
    script.id = "google-identity-services";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => setIsGsiLoaded(true);
    script.onerror = () => console.error("Failed to load Google Identity Services");
    document.head.appendChild(script);
  }, []);

  /**
   * Used on the Login page (/login).
   * Verifies that the Google account already exists in LANES.
   * If not registered, displays a simple error toast without creating a blank account.
   */
  const signInWithGoogle = async (redirectTo?: string) => {
    if (!googleClientId) {
      info(
        "Google Sign-In Notice",
        "Google Client ID is not configured yet. Please check your environment variables."
      );
      return;
    }

    if (typeof window === "undefined" || !window.google?.accounts?.oauth2) {
      info("Loading Google Services", "Google services are still initializing, please try again in a moment.");
      return;
    }

    setIsGoogleLoading(true);

    try {
      tokenClientRef.current = window.google.accounts.oauth2.initTokenClient({
        client_id: googleClientId,
        scope: "openid email profile",
        callback: async (tokenResponse: any) => {
          if (tokenResponse.error) {
            setIsGoogleLoading(false);
            if (tokenResponse.error !== "popup_closed_by_user") {
              showError("Google Auth Error", tokenResponse.error_description || tokenResponse.error);
            }
            return;
          }

          try {
            const data = await authClient.loginWithGoogle({
              access_token: tokenResponse.access_token,
              mode: "login",
            });

            // Store token in localStorage per project PWA rules
            localStorage.setItem("lanes_token", data.access_token);

            // Invalidate React Query cache so user profile is immediately available
            await queryClient.invalidateQueries({ queryKey: ["auth-user"] });

            // Fetch current user details to inspect roles
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
            const profileRes = await fetch(`${baseUrl}/auth/test-token`, {
              method: "POST",
              headers: { Authorization: `Bearer ${data.access_token}` },
            });

            let roleName = "Commuter";
            if (profileRes.ok) {
              const profileData = await profileRes.json();
              roleName = profileData.role?.name || "Commuter";
            }

            const isAdminRole = Boolean(
              roleName && (
                roleName === "Super Admin" ||
                roleName === "DRRM Officer" ||
                roleName === "Moderator" ||
                roleName.toLowerCase().includes("admin")
              )
            );

            success("Welcome Back!", "Successfully signed in with your Google account.");

            // Handle navigation
            if (isAdminRole) {
              if (typeof window !== "undefined") {
                sessionStorage.removeItem("lanes_post_intent");
              }
              if (redirectTo && redirectTo.startsWith("/admin")) {
                router.push(redirectTo);
              } else {
                router.push("/admin/dashboard");
              }
              return;
            }

            if (typeof window !== "undefined" && sessionStorage.getItem("lanes_post_intent")) {
              sessionStorage.removeItem("lanes_post_intent");
              router.push("/feed?openPostModal=true");
              return;
            }

            if (redirectTo && redirectTo.startsWith("/") && redirectTo !== "/" && !redirectTo.startsWith("/admin")) {
              router.push(redirectTo);
              return;
            }

            router.push("/map");
          } catch (err: any) {
            const message = err.message || "";
            if (message.includes("No registered account found") || message.includes("not found")) {
              showError(
                "Account Not Found",
                "No registered account found with this Google email. Please sign up first."
              );
            } else {
              showError("Sign-In Failed", message || "Failed to authenticate with Google.");
            }
          } finally {
            setIsGoogleLoading(false);
          }
        },
        error_callback: (err: any) => {
          setIsGoogleLoading(false);
          if (err?.type !== "popup_closed") {
            showError("Google Sign-In", "Could not open Google Sign-In popup. Please disable popup blockers.");
          }
        },
      });

      tokenClientRef.current.requestAccessToken({ prompt: "" });
    } catch (err: any) {
      setIsGoogleLoading(false);
      showError("Google Sign-In Error", err.message || "Failed to initialize Google authentication.");
    }
  };

  /**
   * Used on the Register page (/register).
   * Prompts the Google account popup and returns verified profile data to pre-fill the form.
   */
  const getGoogleUserProfile = async (): Promise<GoogleUserProfile | null> => {
    if (!googleClientId) {
      info(
        "Google Sign-Up Notice",
        "Google Client ID is not configured yet. Please check your environment variables."
      );
      return null;
    }

    if (typeof window === "undefined" || !window.google?.accounts?.oauth2) {
      info("Loading Google Services", "Google services are still initializing, please try again in a moment.");
      return null;
    }

    setIsGoogleLoading(true);

    return new Promise((resolve) => {
      try {
        const client = window.google.accounts.oauth2.initTokenClient({
          client_id: googleClientId,
          scope: "openid email profile",
          callback: async (tokenResponse: any) => {
            if (tokenResponse.error) {
              setIsGoogleLoading(false);
              if (tokenResponse.error !== "popup_closed_by_user") {
                showError("Google Auth Error", tokenResponse.error_description || tokenResponse.error);
              }
              resolve(null);
              return;
            }

            try {
              // Fetch Google userinfo
              const res = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
                headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
              });

              if (!res.ok) {
                throw new Error("Failed to fetch Google profile information");
              }

              const infoData = await res.json();
              resolve({
                access_token: tokenResponse.access_token,
                email: infoData.email,
                given_name: infoData.given_name,
                family_name: infoData.family_name,
                name: infoData.name,
                picture: infoData.picture,
              });
            } catch (err: any) {
              showError("Profile Error", err.message || "Failed to retrieve Google profile.");
              resolve(null);
            } finally {
              setIsGoogleLoading(false);
            }
          },
          error_callback: (err: any) => {
            setIsGoogleLoading(false);
            if (err?.type !== "popup_closed") {
              showError("Google Sign-Up", "Could not open Google popup. Please disable popup blockers.");
            }
            resolve(null);
          },
        });

        client.requestAccessToken({ prompt: "" });
      } catch (err: any) {
        setIsGoogleLoading(false);
        showError("Google Sign-Up Error", err.message || "Failed to initialize Google authentication.");
        resolve(null);
      }
    });
  };

  return {
    signInWithGoogle,
    getGoogleUserProfile,
    isGoogleLoading,
    isGsiLoaded,
  };
}
