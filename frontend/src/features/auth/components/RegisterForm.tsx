"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { authClient } from "../api/authClient";
import { LocationPickerModal, LocationItem } from "./LocationPickerModal";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import { Select } from "@/shared/ui/Select";
import { DatePicker } from "@/shared/ui/DatePicker";
import { useToast } from "@/shared/ui/Toast";
import { PasswordStrength } from "@/shared/ui/PasswordStrength";
import { motion, AnimatePresence } from "framer-motion";
import { Check, ChevronRight, ChevronLeft, Eye, EyeOff } from "lucide-react";
import { FcGoogle } from "react-icons/fc";

// Metro Manila constant
const METRO_MANILA_CODE = "130000000";

const steps = [
  { id: 1, name: "Account Setup" },
  { id: 2, name: "Personal Info" },
  { id: 3, name: "Address" }
];

export function RegisterForm({ redirectTo }: { redirectTo?: string }) {
  const router = useRouter();
  const { error: showError } = useToast();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [setupPhase, setSetupPhase] = useState<"email" | "otp" | "password">("email");
  const [otpCode, setOtpCode] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const { info, success } = useToast();
  const [otpLoading, setOtpLoading] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  
  const passwordReqRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Progressive cooldown interval ticker
  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const interval = setInterval(() => {
      setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [cooldownSeconds]);

  const formatCooldown = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}:${s.toString().padStart(2, "0")}` : `${s}s`;
  };

  const [activePicker, setActivePicker] = useState<"province" | "city" | "barangay" | null>(null);

  // PSGC State
  const [provinces, setProvinces] = useState<LocationItem[]>([]);
  const [cities, setCities] = useState<LocationItem[]>([]);
  const [barangays, setBarangays] = useState<LocationItem[]>([]);

  const [selectedProvinceCode, setSelectedProvinceCode] = useState("");

  const handleRequestOTP = async () => {
    if (!formData.user.email) {
      showError("Validation Error", "Email address is required.");
      return;
    }
    if (cooldownSeconds > 0) {
      info("Please Wait", `Please wait ${formatCooldown(cooldownSeconds)} before requesting another code. Check your spam folder.`);
      return;
    }
    setOtpLoading(true);
    try {
      const resUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const res = await fetch(`${resUrl}/auth/request-signup-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: formData.user.email })
      });
      if (!res.ok) {
        let errMessage = "Failed to send OTP";
        try {
          const errData = await res.json();
          errMessage = errData.detail || errMessage;
        } catch {
          const text = await res.text().catch(() => "");
          if (text) errMessage = text;
        }
        if (res.status === 429) {
          info("Cooldown Active", errMessage);
        } else {
          showError("Delivery Failed", errMessage);
        }
        return;
      }
      const data = await res.json().catch(() => ({}));
      const nextCooldown = data.cooldown_seconds || 60;
      setCooldownSeconds(nextCooldown);
      setSetupPhase("otp");
      success("Code Sent", "A fresh 6-digit verification code was sent to your email. Check your spam folder if delayed.");
    } catch (err: any) {
      showError("Connection Error", err.message || "Failed to reach server. Please check your connection.");
    } finally {
      setOtpLoading(false);
    }
  };

  const handleVerifyOTP = async (codeToVerify?: string) => {
    const code = codeToVerify || otpCode;
    if (!code || code.length < 6) {
      showError("Validation Error", "Please enter the complete 6-digit OTP code.");
      return;
    }
    setOtpLoading(true);
    try {
      const resUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const res = await fetch(`${resUrl}/auth/verify-signup-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: formData.user.email, otp_code: code })
      });
      if (!res.ok) {
        let errMessage = "Invalid OTP";
        try {
          const errData = await res.json();
          errMessage = errData.detail || errMessage;
        } catch {
          const text = await res.text().catch(() => "");
          if (text) errMessage = text;
        }
        // Auto-clear the boxes on failed attempt and focus the first box
        setOtpCode("");
        setTimeout(() => {
          document.getElementById("otp-digit-0")?.focus();
        }, 100);

        if (res.status === 410) {
          showError("Code Expired", errMessage);
        } else if (res.status === 429) {
          showError("Verification Locked", errMessage);
        } else {
          showError("Incorrect Code", errMessage);
        }
        return;
      }
      success("Email Verified", "Email verified successfully! Let's complete your profile.");
      setSetupPhase("password");
    } catch (err: any) {
      setOtpCode("");
      setTimeout(() => {
        document.getElementById("otp-digit-0")?.focus();
      }, 100);
      showError("Error", err.message || "An unexpected error occurred during verification.");
    } finally {
      setOtpLoading(false);
    }
  };
  const [selectedCityCode, setSelectedCityCode] = useState("");

  const [formData, setFormData] = useState({
    user: { username: "", email: "", password: "" },
    profile: { first_name: "", last_name: "", middle_initial: "", suffix: "", contact_number: "", birthdate: "" },
    address: { house_number: "", street: "", barangay: "", city_municipality: "", province: "", postal_code: "", country: "Philippines" },
  });

  const showPasswordReqs = formData.user.password.length > 0;

  // Immediately scroll down when the password requirements show up
  useEffect(() => {
    if (currentStep === 1 && setupPhase === "password" && showPasswordReqs && scrollContainerRef.current) {
      requestAnimationFrame(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTo({
            top: scrollContainerRef.current.scrollHeight,
            behavior: "smooth"
          });
        }
      });
    }
  }, [showPasswordReqs, currentStep, setupPhase]);

  // Load draft from session storage on mount (never restore password for security & UX)
  useEffect(() => {
    const draft = sessionStorage.getItem("lanes_registration_draft");
    if (draft) {
      try {
        const parsed = JSON.parse(draft);
        setFormData({
          ...parsed,
          user: {
            ...parsed.user,
            password: "", // Always clear password on reload / mount
          },
        });
        setConfirmPassword("");
      } catch (err: any) {
        showError("Draft Error", "Failed to load saved registration draft.");
      }
    }
  }, []);

  // Save draft to session storage on change (exclude sensitive password fields)
  useEffect(() => {
    // Only save if there's actually some data
    if (formData.user.username || formData.profile.first_name || formData.address.province) {
      const sanitizedDraft = {
        ...formData,
        user: {
          ...formData.user,
          password: "", // Never store plain password in sessionStorage
        },
      };
      sessionStorage.setItem("lanes_registration_draft", JSON.stringify(sanitizedDraft));
    }
  }, [formData]);

  // 1. Fetch Provinces on Mount
  useEffect(() => {
    async function fetchProvinces() {
      try {
        const res = await fetch("https://psgc.gitlab.io/api/provinces/");
        const data = await res.json();
        const mappedProvinces = data.map((p: any) => ({
          code: p.code,
          name: p.name,
        }));
        
        // Add Metro Manila manually
        mappedProvinces.push({
          code: METRO_MANILA_CODE,
          name: "Metro Manila",
          isPinned: true,
        });
        
        setProvinces(mappedProvinces.sort((a: any, b: any) => a.name.localeCompare(b.name)));
      } catch (err: any) {
        showError("Location Error", "Failed to fetch provinces. Please check your connection.");
      }
    }
    fetchProvinces();
  }, []);

  // 2. Fetch Cities when Province changes
  useEffect(() => {
    if (!selectedProvinceCode) {
      setCities([]);
      return;
    }
    async function fetchCities() {
      try {
        let url = `https://psgc.gitlab.io/api/provinces/${selectedProvinceCode}/cities-municipalities/`;
        if (selectedProvinceCode === METRO_MANILA_CODE) {
          url = `https://psgc.gitlab.io/api/regions/${METRO_MANILA_CODE}/cities-municipalities/`;
        }
        const res = await fetch(url);
        const data = await res.json();
        
        const normalizeCityName = (name: string) => {
          if (name.startsWith("City of ")) {
            return name.replace("City of ", "") + " City";
          }
          return name;
        };

        setCities(data.map((c: any) => ({ code: c.code, name: normalizeCityName(c.name) })));
      } catch (err: any) {
        showError("Location Error", "Failed to fetch cities. Please check your connection.");
      }
    }
    fetchCities();
  }, [selectedProvinceCode]);

  // 3. Fetch Barangays when City changes
  useEffect(() => {
    if (!selectedCityCode) {
      setBarangays([]);
      return;
    }
    async function fetchBarangays() {
      try {
        const url = `https://psgc.gitlab.io/api/cities-municipalities/${selectedCityCode}/barangays/`;
        const res = await fetch(url);
        const data = await res.json();
        setBarangays(data.map((b: any) => ({ code: b.code, name: b.name })));
      } catch (err: any) {
        showError("Location Error", "Failed to fetch barangays. Please check your connection.");
      }
    }
    fetchBarangays();
  }, [selectedCityCode]);

  const handleChange = (section: "user" | "profile" | "address", field: string, value: any) => {
    let finalValue = value;

    if (section === "profile") {
      if (field === "first_name" || field === "last_name") {
        finalValue = value.replace(/(?:^|\s)[a-z]/g, (char: string) => char.toUpperCase());
      } else if (field === "middle_initial") {
        const prevVal = formData.profile.middle_initial || "";
        const rawLetters = value.replace(/[^a-zA-Z]/g, "").toUpperCase().slice(0, 3);
        const prevLetters = prevVal.replace(/[^a-zA-Z]/g, "").toUpperCase();

        if (rawLetters.length < prevLetters.length) {
          // User is deleting / backspacing: update directly with the remaining letters + dots
          finalValue = rawLetters ? rawLetters.split("").map((c: string) => c + ".").join("") : "";
        } else if (rawLetters.length > prevLetters.length) {
          // User typed a new letter: append dot
          finalValue = rawLetters.split("").map((c: string) => c + ".").join("");
        } else {
          // Same letter count, preserve current formatted value
          finalValue = value ? value.toUpperCase().slice(0, 6) : "";
        }
      } else if (field === "contact_number") {
        finalValue = value.replace(/\D/g, "").substring(0, 11);
      }
    }

    setFormData((prev) => ({
      ...prev,
      [section]: { ...prev[section as keyof typeof prev], [field]: finalValue },
    }));
  };

  const handleProvinceSelect = (item: LocationItem) => {
    if (selectedProvinceCode !== item.code) {
      setSelectedProvinceCode(item.code);
      handleChange("address", "province", item.name);
      
      setSelectedCityCode("");
      handleChange("address", "city_municipality", "");
      handleChange("address", "barangay", "");
    }
    setActivePicker(null);
  };

  const handleCitySelect = (item: LocationItem) => {
    if (selectedCityCode !== item.code) {
      setSelectedCityCode(item.code);
      handleChange("address", "city_municipality", item.name);
      
      handleChange("address", "barangay", "");
    }
    setActivePicker(null);
  };

  const handleBarangaySelect = (item: LocationItem) => {
    handleChange("address", "barangay", item.name);
    setActivePicker(null);
  };

  const validateStep = () => {
    if (currentStep === 1) {
      if (setupPhase !== "password") return false;
      if (!formData.user.username) {
        showError("Validation Error", "Username is required.");
        return false;
      }
      if (!formData.user.password) {
        showError("Validation Error", "Password is required.");
        return false;
      }
      if (formData.user.password !== confirmPassword) {
        showError("Validation Error", "Passwords do not match.");
        return false;
      }
      const pwd = formData.user.password;
      if (pwd.length < 6) {
        showError("Validation Error", "Password must be at least 6 characters long.");
        return false;
      }
      if (/\s/.test(pwd)) {
        showError("Validation Error", "Password must not contain spaces.");
        return false;
      }
      if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d\s])/.test(pwd)) {
        showError("Validation Error", "Password must contain an uppercase letter, a lowercase letter, a number, and a special character.");
        return false;
      }
    } else if (currentStep === 2) {
      if (!formData.profile.first_name) {
        showError("Validation Error", "First name is required.");
        return false;
      }
      if (!formData.profile.last_name) {
        showError("Validation Error", "Last name is required.");
        return false;
      }
      if (!formData.profile.birthdate) {
        showError("Validation Error", "Birthdate is required.");
        return false;
      }
      if (formData.profile.contact_number && formData.profile.contact_number.length !== 11) {
        showError("Validation Error", "Contact number must be exactly 11 digits.");
        return false;
      }
    } else if (currentStep === 3) {
      if (!formData.address.province) {
        showError("Validation Error", "Province / Region is required.");
        return false;
      }
      if (!formData.address.city_municipality) {
        showError("Validation Error", "City / Municipality is required.");
        return false;
      }
      if (!formData.address.barangay) {
        showError("Validation Error", "Barangay is required.");
        return false;
      }
    }
    return true;
  };

  const nextStep = () => {
    if (validateStep()) setCurrentStep(s => s + 1);
  };

  const prevStep = () => {
    setCurrentStep(s => s - 1);
  };

  const handleCreate = async () => {
    if (currentStep !== 3) return;
    if (!validateStep()) return;

    setLoading(true);

    try {
      await authClient.register(formData);
      sessionStorage.removeItem("lanes_registration_draft");
      
      // Auto login
      const loginData = new URLSearchParams();
      loginData.append("username", formData.user.email);
      loginData.append("password", formData.user.password);
      
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      try {
        const loginRes = await fetch(`${baseUrl}/auth/login/access-token`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: loginData.toString()
        });
        if (loginRes.ok) {
          const d = await loginRes.json().catch(() => null);
          if (d?.access_token) {
            localStorage.setItem("lanes_token", d.access_token);
            const destination = redirectTo && redirectTo.startsWith('/') ? redirectTo : '/map';
            window.location.href = destination;
            return;
          }
        }
      } catch (loginErr) {
        console.warn("Auto-login failed after registration, redirecting to login page", loginErr);
      }
      
      router.push("/login");
    } catch (err: any) {
      showError("Registration Failed", err.message || "An error occurred during registration.");
    } finally {
      setLoading(false);
    }
  };

  // Determine modal props
  let modalTitle = "";
  let modalItems: LocationItem[] = [];
  let handleSelect = (item: LocationItem) => {};

  if (activePicker === "province") {
    modalTitle = "Select Province";
    modalItems = provinces;
    handleSelect = handleProvinceSelect;
  } else if (activePicker === "city") {
    modalTitle = "Select City/Municipality";
    modalItems = cities;
    handleSelect = handleCitySelect;
  } else if (activePicker === "barangay") {
    modalTitle = "Select Barangay";
    modalItems = barangays;
    handleSelect = handleBarangaySelect;
  }

  return (
    <>
      <div className="w-full max-w-xl mx-auto bg-white/10 backdrop-blur-sm lg:bg-white rounded-2xl shadow-2xl lg:shadow-[0_8px_40px_rgba(59,130,246,0.15)] border border-white/20 lg:border-slate-200/80 border-t-4 border-t-blue-600 lg:ring-1 lg:ring-blue-100/50">
        {/* Stepper Header */}
        <div className="bg-transparent lg:bg-slate-50 px-5 sm:px-6 pt-5 pb-7 border-b border-white/10 lg:border-slate-100 rounded-t-2xl select-none">
          <h2 className="text-xl font-bold text-white lg:text-slate-900 mb-5 text-center drop-shadow-md lg:drop-shadow-none">Create your Citizen Account</h2>
          <div className="flex items-center justify-between relative px-2">
            <div className="absolute left-2 right-2 top-4 -translate-y-1/2 h-[2px] bg-white/20 lg:bg-slate-200 z-0"></div>
            <div 
              className="absolute left-2 top-4 -translate-y-1/2 h-[2px] bg-blue-500 lg:bg-blue-600 z-0 transition-all duration-500"
              style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 96}%` }}
            ></div>
            
            {steps.map((step) => (
              <div key={step.id} className="relative z-10 flex flex-col items-center">
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors duration-300 ${
                    currentStep > step.id 
                      ? "bg-blue-600 text-white shadow-sm" 
                      : currentStep === step.id 
                        ? "bg-blue-600 text-white ring-4 ring-blue-500/30 lg:ring-blue-100 shadow-md" 
                        : "bg-white/15 border border-white/30 text-white/70 lg:bg-white lg:border-2 lg:border-slate-200 lg:text-slate-400"
                  }`}
                >
                  {currentStep > step.id ? <Check className="w-4 h-4" /> : step.id}
                </div>
                <span className={`absolute top-9 text-[11px] sm:text-xs font-medium whitespace-nowrap transition-colors duration-300 ${
                  currentStep >= step.id ? "text-white lg:text-slate-900 font-semibold drop-shadow-sm" : "text-white/60 lg:text-slate-400"
                }`}>
                  {step.name}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Form Body */}
        <div className="p-5 sm:p-6 pt-5 sm:pt-6">
          <form 
            onSubmit={(e) => e.preventDefault()}
            className="relative flex flex-col w-full"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.target as HTMLElement).tagName !== 'BUTTON') {
                e.preventDefault();
                if (currentStep < 3) {
                  nextStep();
                } else {
                  handleCreate();
                }
              }
            }}
          >
            <div ref={scrollContainerRef} className="w-full">
              <AnimatePresence mode="wait">
              {currentStep === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  {setupPhase === "email" && (
                    <div className="space-y-4">
                      <Input 
                        label="Email Address"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        type="email" 
                        placeholder="juan@example.com" 
                        required
                        value={formData.user.email} 
                        onChange={e => handleChange("user", "email", e.target.value)}
                      />
                      <div className="relative flex items-center py-2">
                        <div className="flex-grow border-t border-white/20 lg:border-slate-200"></div>
                        <span className="flex-shrink-0 mx-4 text-white/80 lg:text-slate-400 text-sm font-medium">or</span>
                        <div className="flex-grow border-t border-white/20 lg:border-slate-200"></div>
                      </div>
                      <button
                        type="button"
                        onClick={() => info("Under Development", "Google Sign-Up is currently under development.")}
                        className="w-full flex items-center justify-center gap-2 bg-white text-slate-700 border border-slate-300 font-medium py-2.5 rounded-lg hover:bg-slate-50 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      >
                        <FcGoogle className="w-5 h-5" />
                        Sign up with Google
                      </button>
                    </div>
                  )}

                  {setupPhase === "otp" && (
                    <div className="space-y-6 pt-1">
                      <div className="text-center space-y-1">
                        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-50 text-blue-600 mb-2 ring-8 ring-blue-50/50">
                          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                        </div>
                        <h3 className="text-lg font-bold text-white lg:text-slate-900 drop-shadow-sm">Check your inbox</h3>
                        <p className="text-sm text-blue-100 lg:text-slate-500">
                          We sent a 6-digit verification code to<br />
                          <span className="font-semibold text-white lg:text-slate-900 break-all">{formData.user.email}</span>
                        </p>
                      </div>

                      {/* 6-box Digit Inputs */}
                      <div className="flex justify-center items-center gap-2 sm:gap-3 py-4">
                        {[0, 1, 2, 3, 4, 5].map((index) => {
                          const digit = otpCode[index] || "";
                          return (
                            <input
                              key={index}
                              id={`otp-digit-${index}`}
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
                                  const nextInput = document.getElementById(`otp-digit-${index + 1}`);
                                  nextInput?.focus();
                                }
                                // Auto-trigger verification when 6 digits are complete!
                                if (joined.length === 6) {
                                  handleVerifyOTP(joined);
                                }
                              }}
                              onKeyDown={(e) => {
                                if (e.key === "Backspace" && !digit && index > 0) {
                                  const prevInput = document.getElementById(`otp-digit-${index - 1}`);
                                  prevInput?.focus();
                                }
                              }}
                              onPaste={(e) => {
                                e.preventDefault();
                                const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
                                setOtpCode(pasted);
                                if (pasted.length === 6) {
                                  handleVerifyOTP(pasted);
                                } else if (pasted.length > 0) {
                                  const targetIdx = Math.min(pasted.length, 5);
                                  document.getElementById(`otp-digit-${targetIdx}`)?.focus();
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
                    </div>
                  )}

                  {setupPhase === "password" && (
                    <div className="space-y-4">
                      <Input 
                        label="Username"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        placeholder="juandelacruz" 
                        required
                        value={formData.user.username} 
                        onChange={e => handleChange("user", "username", e.target.value)}
                      />
                      <div>
                        <Input 
                          label="Password"
                          labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                          type={showPassword ? "text" : "password"}
                          placeholder="••••••••" 
                          required
                          autoComplete="new-password"
                          value={formData.user.password} 
                          onChange={e => handleChange("user", "password", e.target.value)}
                          onFocus={() => {
                            if (scrollContainerRef.current) {
                              setTimeout(() => {
                                scrollContainerRef.current?.scrollTo({
                                  top: scrollContainerRef.current.scrollHeight,
                                  behavior: "smooth"
                                });
                              }, 50);
                            }
                          }}
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
                        <div ref={passwordReqRef}>
                          <PasswordStrength password={formData.user.password} />
                        </div>
                      </div>
                      <Input 
                        label="Confirm Password"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        type={showConfirmPassword ? "text" : "password"}
                        placeholder="••••••••" 
                        required
                        autoComplete="new-password"
                        value={confirmPassword} 
                        onChange={e => setConfirmPassword(e.target.value)}
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
                    </div>
                  )}
                </motion.div>
              )}

              {currentStep === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1">
                      <Input 
                        label="First Name"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        placeholder="Juan" 
                        required
                        value={formData.profile.first_name} 
                        onChange={e => handleChange("profile", "first_name", e.target.value)}
                      />
                    </div>
                    <div className="flex-1">
                      <Input 
                        label="Last Name"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        placeholder="Dela Cruz" 
                        required
                        value={formData.profile.last_name} 
                        onChange={e => handleChange("profile", "last_name", e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1">
                      <Input 
                        label="M.I. (Optional)"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        placeholder="D.C." 
                        maxLength={5}
                        value={formData.profile.middle_initial} 
                        onChange={e => handleChange("profile", "middle_initial", e.target.value)}
                      />
                    </div>
                    <div className="flex-1">
                      <Select 
                        label="Suffix (Optional)"
                        placeholder="None"
                        value={formData.profile.suffix || ""}
                        onChange={(e) => handleChange("profile", "suffix", e.target.value)}
                        options={[
                          { label: "None", value: "" },
                          { label: "Jr.", value: "Jr." },
                          { label: "Sr.", value: "Sr." },
                          { label: "II", value: "II" },
                          { label: "III", value: "III" },
                          { label: "IV", value: "IV" },
                        ]}
                      />
                    </div>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1">
                      <Input 
                        label="Contact Number (Optional)"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        placeholder="09123456789"
                        value={formData.profile.contact_number} 
                        onChange={e => handleChange("profile", "contact_number", e.target.value)}
                      />
                    </div>
                    <div className="w-full sm:w-40">
                      <DatePicker 
                        label="Birthdate"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        required
                        value={formData.profile.birthdate} 
                        onChange={e => handleChange("profile", "birthdate", e.target.value)}
                        align="right"
                      />
                    </div>
                  </div>
                </motion.div>
              )}

              {currentStep === 3 && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1 space-y-1">
                      <label className="block text-sm font-semibold text-white lg:text-slate-700 drop-shadow-sm">
                        Province / Region <span className="text-red-500 ml-1">*</span>
                      </label>
                      <button 
                        type="button" 
                        onClick={() => setActivePicker("province")}
                        className="w-full p-2.5 text-left text-sm rounded-lg bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-slate-900 transition-all hover:bg-slate-100 truncate"
                      >
                        {formData.address.province || "Select Province"}
                      </button>
                    </div>

                    <div className="flex-1 space-y-1">
                      <label className="block text-sm font-semibold text-white lg:text-slate-700 drop-shadow-sm">
                        City / Municipality <span className="text-red-500 ml-1">*</span>
                      </label>
                      <button 
                        type="button" 
                        onClick={() => setActivePicker("city")}
                        disabled={!formData.address.province}
                        className="w-full p-2.5 text-left text-sm rounded-lg bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-slate-900 disabled:opacity-50 transition-all hover:bg-slate-100 truncate"
                      >
                        {formData.address.city_municipality || "Select City"}
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
                    <div className="flex-1 space-y-1">
                      <label className="block text-sm font-semibold text-white lg:text-slate-700 drop-shadow-sm">
                        Barangay <span className="text-red-500 ml-1">*</span>
                      </label>
                      <button 
                        type="button" 
                        onClick={() => setActivePicker("barangay")}
                        disabled={!formData.address.city_municipality}
                        className="w-full p-2.5 text-left text-sm rounded-lg bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-slate-900 disabled:opacity-50 transition-all hover:bg-slate-100 truncate"
                      >
                        {formData.address.barangay || "Select Barangay"}
                      </button>
                    </div>
                    <div className="w-full sm:w-1/3">
                      <Input 
                        label="Postal Code (Optional)"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        placeholder="1210" 
                        value={formData.address.postal_code} 
                        onChange={e => handleChange("address", "postal_code", e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
                    <div className="w-full sm:w-1/3">
                      <Input 
                        label="House No. (Optional)"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        placeholder="123"
                        value={formData.address.house_number} 
                        onChange={e => handleChange("address", "house_number", e.target.value)}
                      />
                    </div>
                    <div className="flex-1">
                      <Input 
                        label="Street (Optional)"
                        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
                        placeholder="Main St"
                        value={formData.address.street} 
                        onChange={e => handleChange("address", "street", e.target.value)}
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            </div>

            {/* Bottom Navigation */}
            <div className="mt-3 flex items-center justify-between pt-4 border-t border-slate-100 shrink-0">
              {currentStep === 1 && setupPhase === "otp" ? (
                <>
                  <button 
                    type="button" 
                    onClick={() => setSetupPhase("email")} 
                    className="flex items-center text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Change Email
                  </button>
                  <div className="flex items-center gap-3">
                    {otpLoading ? (
                      <span className="flex items-center gap-2 text-xs sm:text-sm text-blue-600 font-semibold">
                        <svg className="animate-spin h-4 w-4 text-blue-600" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Verifying...
                      </span>
                    ) : (
                      <button 
                        type="button" 
                        onClick={handleRequestOTP}
                        disabled={otpLoading || cooldownSeconds > 0}
                        className={`text-xs sm:text-sm font-semibold transition-colors px-3 py-1.5 rounded-lg border ${
                          cooldownSeconds > 0
                            ? "border-slate-200/50 bg-slate-100/50 text-slate-400 cursor-not-allowed"
                            : "border-slate-300 bg-white hover:bg-slate-50 text-slate-700 shadow-sm"
                        }`}
                      >
                        {cooldownSeconds > 0 ? `Resend (${formatCooldown(cooldownSeconds)})` : "Resend Code"}
                      </button>
                    )}
                  </div>
                </>
              ) : (
                <>
                  {currentStep > 1 ? (
                    <button
                      type="button"
                      onClick={prevStep}
                      className="flex items-center text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Back
                    </button>
                  ) : (
                    <div></div>
                  )}

                  {currentStep === 1 ? (
                    setupPhase === "email" ? (
                      <Button type="button" onClick={handleRequestOTP} disabled={otpLoading} className="pl-6 pr-4 py-2">
                        {otpLoading ? "Sending..." : "Send OTP"}
                        <ChevronRight className="w-4 h-4 ml-2 inline" />
                      </Button>
                    ) : (
                      <Button type="button" onClick={nextStep} className="pl-6 pr-4 py-2">
                        Next Step
                        <ChevronRight className="w-4 h-4 ml-2 inline" />
                      </Button>
                    )
                  ) : currentStep < 3 ? (
                    <Button type="button" onClick={nextStep} className="pl-6 pr-4 py-2">
                      Next Step
                      <ChevronRight className="w-4 h-4 ml-2 inline" />
                    </Button>
                  ) : (
                    <Button type="button" onClick={handleCreate} disabled={loading} className="px-6 py-2">
                      {loading ? "Registering..." : "Create Account"}
                    </Button>
                  )}
                </>
              )}
            </div>
          </form>
        </div>
      </div>

      <LocationPickerModal
        isOpen={activePicker !== null}
        onClose={() => setActivePicker(null)}
        title={modalTitle}
        items={modalItems}
        onSelect={handleSelect}
      />
    </>
  );
}
