"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Input } from "@/shared/ui";
import { Button } from "@/shared/ui";
import { Loader2, Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { FcGoogle } from "react-icons/fc";
import { useGoogleAuth } from "./hooks/useGoogleAuth";
import ForgotPasswordForm from "./components/ForgotPasswordForm";

interface LoginFormProps {
  initialView?: "login" | "forgot";
  onViewChange?: (view: "login" | "forgot") => void;
}

export default function LoginForm({ initialView, onViewChange }: LoginFormProps = {}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect');
  const isForgotQuery = searchParams.get('forgot') === 'true';

  const [internalView, setInternalView] = useState<"login" | "forgot">(
    initialView || (isForgotQuery ? "forgot" : "login")
  );
  const currentView = initialView !== undefined ? initialView : internalView;

  const changeView = (nextView: "login" | "forgot") => {
    setInternalView(nextView);
    if (onViewChange) {
      onViewChange(nextView);
    }
  };

  const { login, isLoggingIn } = useAuth();
  const { signInWithGoogle, isGoogleLoading } = useGoogleAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  if (currentView === "forgot") {
    return (
      <ForgotPasswordForm
        initialEmail={username.includes("@") ? username : ""}
        onBackToLogin={(prefilledEmail) => {
          changeView("login");
          if (prefilledEmail) {
            setUsername(prefilledEmail);
          }
        }}
      />
    );
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      const data = await login(formData);
      
      // Determine role by fetching profile
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const profileResponse = await fetch(`${baseUrl}/auth/test-token`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${data.access_token}` }
      });
      
      if (profileResponse.ok) {
        const profile = await profileResponse.json();
        const roleName = profile.role?.name;
        const isAdminRole = Boolean(
          roleName && (
            roleName === "Super Admin" ||
            roleName === "DRRM Officer" ||
            roleName === "Moderator" ||
            roleName.toLowerCase().includes("admin")
          )
        );

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
        return;
      } else {
        router.push("/map");
        return;
      }
    } catch (err: any) {
      try {
        const parsed = JSON.parse(err.message);
        if (parsed.code === "UNVERIFIED_ACCOUNT") {
          const resendUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
          await fetch(`${resendUrl}/auth/resend-otp`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: parsed.email })
          });
          router.push(`/verify?email=${encodeURIComponent(parsed.email)}`);
          return;
        }
      } catch (e) {
        // Not a JSON string
      }
      setErrorMsg(err.message || "Login failed. Please check your credentials.");
    }
  };

  return (
    <form onSubmit={handleLogin} className="space-y-4">
      {errorMsg && (
        <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg font-medium">
          {errorMsg}
        </div>
      )}
      <Input
        label="Email or Username"
        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
        type="text"
        placeholder="Enter your email or username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      <Input
        label="Password"
        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
        type={showPassword ? "text" : "password"}
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        className="text-gray-900 bg-white"
        rightIcon={
          <button
            type="button"
            onMouseDown={() => setShowPassword(true)}
            onMouseUp={() => setShowPassword(false)}
            onMouseLeave={() => setShowPassword(false)}
            onTouchStart={() => setShowPassword(true)}
            onTouchEnd={() => setShowPassword(false)}
            onTouchCancel={() => setShowPassword(false)}
            className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none select-none cursor-pointer"
            tabIndex={-1}
            aria-label="Hold to view password"
            title="Hold to view password"
          >
            {showPassword ? <Eye className="w-4 h-4 text-blue-600" /> : <EyeOff className="w-4 h-4" />}
          </button>
        }
      />
      <div className="flex justify-end mt-1">
        <button
          type="button"
          onClick={() => changeView("forgot")}
          className="text-sm text-blue-200 lg:text-blue-600 font-medium hover:text-white lg:hover:text-blue-500 hover:underline transition-colors cursor-pointer"
        >
          Forgot password?
        </button>
      </div>
      <div className="pt-2">
        <Button type="submit" className="w-full" disabled={isLoggingIn || isGoogleLoading}>
          {isLoggingIn ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Signing in...
            </>
          ) : (
            "Sign In"
          )}
        </Button>
      </div>
      
      <div className="relative flex items-center py-2">
        <div className="flex-grow border-t border-white/20 lg:border-slate-200"></div>
        <span className="flex-shrink-0 mx-4 text-white/80 lg:text-slate-400 text-sm font-medium">or</span>
        <div className="flex-grow border-t border-white/20 lg:border-slate-200"></div>
      </div>

      <div>
        <button
          type="button"
          onClick={() => signInWithGoogle(redirectTo || undefined)}
          disabled={isLoggingIn || isGoogleLoading}
          className="w-full flex items-center justify-center gap-2 bg-white text-slate-700 border border-slate-300 font-medium py-2.5 rounded-lg hover:bg-slate-50 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
        >
          {isGoogleLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin text-slate-500" />
              Connecting to Google...
            </>
          ) : (
            <>
              <FcGoogle className="w-5 h-5" />
              Sign in with Google
            </>
          )}
        </button>
      </div>

      <div className="text-center pt-2">
        <p className="text-sm text-blue-100 lg:text-slate-600">
          Don't have an account?{" "}
          <Link
            href={redirectTo ? `/register?redirect=${encodeURIComponent(redirectTo)}` : "/register"}
            className="text-white lg:text-blue-600 font-bold lg:font-semibold hover:text-blue-200 lg:hover:text-blue-700 hover:underline transition-colors"
          >
            Sign up
          </Link>
        </p>
      </div>
    </form>
  );
}
