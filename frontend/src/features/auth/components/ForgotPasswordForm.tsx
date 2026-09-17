"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Input, Button, PasswordStrength, useToast } from "@/shared/ui";
import { authClient } from "../api/authClient";
import { Eye, EyeOff, ChevronLeft, Loader2, CheckCircle2 } from "lucide-react";

interface ForgotPasswordFormProps {
  initialEmail?: string;
  onBackToLogin: (prefilledEmail?: string) => void;
}

type ForgotPhase = "email" | "otp" | "password" | "success";

export default function ForgotPasswordForm({
  initialEmail = "",
  onBackToLogin,
}: ForgotPasswordFormProps) {
  const { success, error: showError } = useToast();

  const [phase, setPhase] = useState<ForgotPhase>("email");
  const [email, setEmail] = useState(initialEmail);
  const [loading, setLoading] = useState(false);

  // OTP State
  const [otpCode, setOtpCode] = useState("");
  const [otpLoading, setOtpLoading] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);

  // Reset Token & Password State
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const isSubmittingOtpRef = useRef(false);

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const timer = setInterval(() => {
      setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldownSeconds]);

  const formatCooldown = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}m ${s.toString().padStart(2, "0")}s`;
  };

  // Phase 1: Request OTP
  const handleRequestOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!email || !email.includes("@")) {
      showError("Validation Error", "Please enter a valid email address.");
      return;
    }

    setLoading(true);
    try {
      const res = await authClient.requestPasswordResetOtp(email);
      success(
        "Verification Code Sent",
        "If your email is registered, a 6-digit code has been sent to your inbox."
      );
      setCooldownSeconds(res.cooldown_seconds || 60);
      setOtpCode("");
      setPhase("otp");
    } catch (err: any) {
      if (err.status === 429) {
        showError("Too Many Requests", err.message || "Please wait before requesting another code.");
      } else {
        showError("Request Failed", err.message || "Could not send verification code.");
      }
    } finally {
      setLoading(false);
    }
  };

  // Phase 2: Verify OTP
  const handleVerifyOtp = async (codeToVerify?: string) => {
    const code = codeToVerify || otpCode;
    if (code.length !== 6) {
      showError("Validation Error", "Please enter the complete 6-digit code.");
      return;
    }
    if (isSubmittingOtpRef.current) return;

    isSubmittingOtpRef.current = true;
    setOtpLoading(true);

    try {
      const res = await authClient.verifyPasswordResetOtp(email, code);
      setResetToken(res.reset_token);
      success("Code Verified", "Please enter your new password.");
      setPhase("password");
    } catch (err: any) {
      setOtpCode("");
      setTimeout(() => {
        document.getElementById("forgot-otp-digit-0")?.focus();
      }, 100);

      const errMessage = err.message || "Invalid or expired code.";
      if (err.status === 410) {
        showError("Code Expired", errMessage);
      } else if (err.status === 429) {
        showError("Verification Locked", errMessage);
      } else {
        showError("Incorrect Code", errMessage);
      }
    } finally {
      isSubmittingOtpRef.current = false;
      setOtpLoading(false);
    }
  };

  // Phase 3: Submit New Password
  const handleResetPassword = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    if (newPassword.length < 6) {
      showError("Validation Error", "Password must be at least 6 characters long.");
      return;
    }
    if (/\s/.test(newPassword)) {
      showError("Validation Error", "Password must not contain spaces.");
      return;
    }
    if (newPassword !== confirmPassword) {
      showError("Validation Error", "Passwords do not match.");
      return;
    }
    if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d\s])/.test(newPassword)) {
      showError(
        "Validation Error",
        "Password must contain an uppercase letter, a lowercase letter, a number, and a special character."
      );
      return;
    }

    setLoading(true);
    try {
      await authClient.resetPassword(resetToken, newPassword);
      success("Password Reset Successful", "You can now sign in with your new password.");
      setPhase("success");
    } catch (err: any) {
      showError("Reset Failed", err.message || "Could not reset password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {/* PHASE 1: EMAIL */}
        {phase === "email" && (
          <motion.div
            key="phase-email"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25 }}
            className="space-y-5"
          >
            <div className="text-center lg:text-left space-y-1 mb-6">
              <h3 className="text-xl sm:text-2xl font-bold text-white lg:text-slate-900 tracking-tight drop-shadow-sm">
                Reset your password
              </h3>
              <p className="text-sm text-blue-100 lg:text-slate-500">
                Enter your email address and we will send you a 6-digit verification code.
              </p>
            </div>

            <form onSubmit={handleRequestOtp} className="space-y-4">
              <Input
                label="Email Address"
                labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                type="email"
                placeholder="juan@example.com"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />

              <div className="pt-2 space-y-3">
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Sending code...
                    </>
                  ) : (
                    "Send Reset Code"
                  )}
                </Button>

                <button
                  type="button"
                  onClick={() => onBackToLogin()}
                  className="w-full flex items-center justify-center text-sm font-medium text-blue-200 lg:text-slate-600 hover:text-white lg:hover:text-slate-900 transition-colors py-1.5 cursor-pointer"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Back to Sign In
                </button>
              </div>
            </form>
          </motion.div>
        )}

        {/* PHASE 2: OTP VERIFICATION */}
        {phase === "otp" && (
          <motion.div
            key="phase-otp"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25 }}
            className="space-y-6 pt-1"
          >
            <div className="text-center space-y-1">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-50 text-blue-600 mb-2 ring-8 ring-blue-50/50">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-white lg:text-slate-900 drop-shadow-sm">
                Check your inbox
              </h3>
              <p className="text-sm text-blue-100 lg:text-slate-500">
                We sent a 6-digit password reset code to<br />
                <span className="font-semibold text-white lg:text-slate-900 break-all">{email}</span>
              </p>
            </div>

            {/* 6-box Digit Inputs matching RegisterForm pixel-for-pixel */}
            <div className="flex justify-center items-center gap-2 sm:gap-3 py-2">
              {[0, 1, 2, 3, 4, 5].map((index) => {
                const digit = otpCode[index] || "";
                return (
                  <input
                    key={index}
                    id={`forgot-otp-digit-${index}`}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    disabled={otpLoading}
                    autoFocus={index === 0}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, "");
                      const newOtp = otpCode.split("");
                      newOtp[index] = val;
                      const joined = newOtp.join("").slice(0, 6);
                      setOtpCode(joined);
                      if (val && index < 5) {
                        const nextInput = document.getElementById(`forgot-otp-digit-${index + 1}`);
                        nextInput?.focus();
                      }
                      if (joined.length === 6) {
                        handleVerifyOtp(joined);
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Backspace" && !digit && index > 0) {
                        const prevInput = document.getElementById(`forgot-otp-digit-${index - 1}`);
                        prevInput?.focus();
                      }
                    }}
                    onPaste={(e) => {
                      e.preventDefault();
                      const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
                      setOtpCode(pasted);
                      if (pasted.length === 6) {
                        handleVerifyOtp(pasted);
                      } else if (pasted.length > 0) {
                        const targetIdx = Math.min(pasted.length, 5);
                        document.getElementById(`forgot-otp-digit-${targetIdx}`)?.focus();
                      }
                    }}
                    className={`w-11 h-13 sm:w-12 sm:h-14 text-center text-xl sm:text-2xl font-bold rounded-xl border transition-all duration-200 outline-none select-none ${
                      digit
                        ? "border-blue-600 bg-white text-blue-600 shadow-sm ring-2 ring-blue-100"
                        : "border-slate-200 bg-slate-50/80 text-slate-900 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
                    } ${otpLoading ? "opacity-60 cursor-wait" : ""}`}
                  />
                );
              })}
            </div>

            {/* Bottom Controls matching RegisterForm */}
            <div className="mt-4 flex items-center justify-between pt-4 border-t border-white/10 lg:border-slate-100">
              <button
                type="button"
                onClick={() => setPhase("email")}
                className="flex items-center text-sm font-semibold text-blue-200 lg:text-blue-600 hover:text-white lg:hover:text-blue-800 transition-colors cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Change Email
              </button>

              <div className="flex items-center gap-3">
                {otpLoading ? (
                  <span className="flex items-center gap-2 text-xs sm:text-sm text-blue-200 lg:text-blue-600 font-semibold">
                    <Loader2 className="animate-spin h-4 w-4 text-blue-500" />
                    Verifying...
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleRequestOtp()}
                    disabled={otpLoading || cooldownSeconds > 0}
                    className={`text-xs sm:text-sm font-semibold transition-colors px-3 py-1.5 rounded-lg border cursor-pointer ${
                      cooldownSeconds > 0
                        ? "border-slate-200/50 bg-slate-100/50 text-slate-400 cursor-not-allowed"
                        : "border-slate-300 bg-white hover:bg-slate-50 text-slate-700 shadow-sm"
                    }`}
                  >
                    {cooldownSeconds > 0 ? `Resend (${formatCooldown(cooldownSeconds)})` : "Resend Code"}
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* PHASE 3: NEW PASSWORD */}
        {phase === "password" && (
          <motion.div
            key="phase-password"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.25 }}
            className="space-y-4"
          >
            <div className="text-center lg:text-left space-y-1 mb-4">
              <h3 className="text-xl sm:text-2xl font-bold text-white lg:text-slate-900 tracking-tight drop-shadow-sm">
                Create New Password
              </h3>
              <p className="text-sm text-blue-100 lg:text-slate-500">
                Choose a strong password to secure your account.
              </p>
            </div>

            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <Input
                  label="New Password"
                  labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  required
                  autoFocus
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  rightIcon={
                    <button
                      type="button"
                      onMouseDown={() => setShowPassword(true)}
                      onMouseUp={() => setShowPassword(false)}
                      onMouseLeave={() => setShowPassword(false)}
                      onTouchStart={() => setShowPassword(true)}
                      onTouchEnd={() => setShowPassword(false)}
                      onTouchCancel={() => setShowPassword(false)}
                      className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none select-none cursor-pointer p-1"
                      tabIndex={-1}
                      aria-label="Hold to view password"
                      title="Hold to view password"
                    >
                      {showPassword ? <Eye className="w-4 h-4 text-blue-600" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                  }
                />
                <PasswordStrength password={newPassword} />
              </div>

              <Input
                label="Confirm New Password"
                labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                type={showConfirmPassword ? "text" : "password"}
                placeholder="••••••••"
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                rightIcon={
                  <button
                    type="button"
                    onMouseDown={() => setShowConfirmPassword(true)}
                    onMouseUp={() => setShowConfirmPassword(false)}
                    onMouseLeave={() => setShowConfirmPassword(false)}
                    onTouchStart={() => setShowConfirmPassword(true)}
                    onTouchEnd={() => setShowConfirmPassword(false)}
                    onTouchCancel={() => setShowConfirmPassword(false)}
                    className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none select-none cursor-pointer p-1"
                    tabIndex={-1}
                    aria-label="Hold to view confirm password"
                    title="Hold to view confirm password"
                  >
                    {showConfirmPassword ? <Eye className="w-4 h-4 text-blue-600" /> : <EyeOff className="w-4 h-4" />}
                  </button>
                }
              />

              <div className="pt-3 space-y-3">
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Updating password...
                    </>
                  ) : (
                    "Reset Password"
                  )}
                </Button>

                <button
                  type="button"
                  onClick={() => onBackToLogin()}
                  className="w-full flex items-center justify-center text-sm font-medium text-blue-200 lg:text-slate-600 hover:text-white lg:hover:text-slate-900 transition-colors py-1.5 cursor-pointer"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Cancel & Back to Sign In
                </button>
              </div>
            </form>
          </motion.div>
        )}

        {/* PHASE 4: SUCCESS */}
        {phase === "success" && (
          <motion.div
            key="phase-success"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="text-center py-4 space-y-5"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 ring-8 ring-emerald-50/50">
              <CheckCircle2 className="w-9 h-9" />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-2xl font-extrabold text-white lg:text-slate-900 tracking-tight">
                Password Reset Complete!
              </h3>
              <p className="text-sm text-blue-100 lg:text-slate-500 max-w-sm mx-auto">
                Your password has been successfully updated. You can now sign in with your new password.
              </p>
            </div>

            <div className="pt-2">
              <Button
                type="button"
                className="w-full"
                onClick={() => onBackToLogin(email)}
              >
                Back to Sign In
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
