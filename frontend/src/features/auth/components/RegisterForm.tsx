"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { authClient } from "../api/authClient";
import { LocationPickerModal, LocationItem } from "./LocationPickerModal";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
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

export function RegisterForm() {
  const router = useRouter();
  const { error: showError } = useToast();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [showPassword, setShowPassword] = useState(false);
  const [setupPhase, setSetupPhase] = useState<"email" | "otp" | "password">("email");
  const [otpCode, setOtpCode] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const { info } = useToast();
  const [otpLoading, setOtpLoading] = useState(false);
  
  const passwordReqRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

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
    setOtpLoading(true);
    try {
      const resUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const res = await fetch(`${resUrl}/auth/request-signup-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: formData.user.email })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to send OTP");
      }
      setSetupPhase("otp");
      info("OTP Sent", "Check your email for the verification code.");
    } catch (err: any) {
      showError("Error", err.message);
    } finally {
      setOtpLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otpCode) {
      showError("Validation Error", "OTP is required.");
      return;
    }
    setOtpLoading(true);
    try {
      const resUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const res = await fetch(`${resUrl}/auth/verify-signup-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: formData.user.email, otp_code: otpCode })
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Invalid OTP");
      }
      setSetupPhase("password");
    } catch (err: any) {
      showError("Error", err.message);
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
    if (currentStep === 3 && showPasswordReqs && scrollContainerRef.current) {
      requestAnimationFrame(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTo({
            top: scrollContainerRef.current.scrollHeight,
            behavior: "smooth"
          });
        }
      });
    }
  }, [showPasswordReqs, currentStep]);

  // Load draft from session storage on mount
  useEffect(() => {
    const draft = sessionStorage.getItem("lanes_registration_draft");
    if (draft) {
      try {
        setFormData(JSON.parse(draft));
      } catch (err: any) {
        showError("Draft Error", "Failed to load saved registration draft.");
      }
    }
  }, []);

  // Save draft to session storage on change
  useEffect(() => {
    // Only save if there's actually some data
    if (formData.user.username || formData.profile.first_name || formData.address.province) {
      sessionStorage.setItem("lanes_registration_draft", JSON.stringify(formData));
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
        finalValue = value.replace(/[^a-zA-Z]/g, "").charAt(0).toUpperCase();
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
      const loginRes = await fetch(`${baseUrl}/auth/login/access-token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: loginData.toString()
      });
      if (loginRes.ok) {
        const d = await loginRes.json();
        localStorage.setItem("lanes_access_token", d.access_token);
        // Force reload to get auth state
        window.location.href = "/map";
      } else {
        router.push("/login");
      }
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
      <div className="w-full max-w-xl mx-auto bg-white/20 backdrop-blur-2xl lg:bg-white rounded-2xl shadow-2xl lg:shadow-[0_8px_40px_rgba(59,130,246,0.15)] lg:border lg:border-slate-200/80 border border-white/40 border-t-4 border-t-blue-600 lg:ring-1 lg:ring-blue-100/50">
        {/* Stepper Header */}
        <div className="bg-transparent lg:bg-slate-50 px-8 py-6 border-b border-slate-200/50 lg:border-slate-100 rounded-t-2xl select-none">
          <h2 className="text-xl font-bold text-white lg:text-slate-900 mb-6 text-center">Create your Citizen Account</h2>
          <div className="flex items-center justify-between relative">
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-[2px] bg-slate-200 z-0"></div>
            <div 
              className="absolute left-0 top-1/2 -translate-y-1/2 h-[2px] bg-blue-600 z-0 transition-all duration-500"
              style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
            ></div>
            
            {steps.map((step) => (
              <div key={step.id} className="relative z-10 flex flex-col items-center">
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors duration-300 ${
                    currentStep > step.id 
                      ? "bg-blue-600 text-white" 
                      : currentStep === step.id 
                        ? "bg-blue-600 text-white ring-4 ring-blue-100" 
                        : "bg-white border-2 border-slate-200 text-slate-400"
                  }`}
                >
                  {currentStep > step.id ? <Check className="w-4 h-4" /> : step.id}
                </div>
                <span className={`absolute top-10 text-xs font-medium whitespace-nowrap transition-colors duration-300 ${
                  currentStep >= step.id ? "text-white lg:text-slate-900" : "text-white/50 lg:text-slate-400"
                }`}>
                  {step.name}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Form Body */}
        <div className="p-8 pt-10">
          <form 
            onSubmit={(e) => e.preventDefault()}
            className="relative flex flex-col h-auto min-h-[320px] sm:h-[320px]"
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
            <div ref={scrollContainerRef} className="flex-1 overflow-y-auto overflow-x-hidden p-1 -m-1">
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
                        type="email" 
                        placeholder="juan@example.com" 
                        required
                        value={formData.user.email} 
                        onChange={e => handleChange("user", "email", e.target.value)}
                      />
                      <div className="relative flex items-center py-2">
                        <div className="flex-grow border-t border-slate-200 lg:border-slate-200 border-white/30"></div>
                        <span className="flex-shrink-0 mx-4 text-white/80 lg:text-slate-400 text-sm font-medium">or</span>
                        <div className="flex-grow border-t border-slate-200 lg:border-slate-200 border-white/30"></div>
                      </div>
                      <button
                        type="button"
                        onClick={() => info("Under Development", "Google Sign-Up is currently under development.")}
                        className="w-full flex items-center justify-center gap-2 bg-white text-slate-700 border border-slate-200 lg:border-slate-300 font-medium py-2.5 rounded-lg hover:bg-slate-50 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                      >
                        <FcGoogle className="w-5 h-5" />
                        Sign up with Google
                      </button>
                    </div>
                  )}

                  {setupPhase === "otp" && (
                    <div className="space-y-4">
                      <p className="text-sm text-slate-600 mb-2">We sent a verification code to <strong>{formData.user.email}</strong>.</p>
                      <Input 
                        label="6-Digit OTP Code"
                        type="text" 
                        placeholder="123456" 
                        maxLength={6}
                        required
                        value={otpCode} 
                        onChange={e => setOtpCode(e.target.value.replace(/\D/g, ''))}
                      />
                      <button type="button" onClick={() => setSetupPhase("email")} className="text-sm text-blue-600 font-medium hover:underline">Change Email</button>
                    </div>
                  )}

                  {setupPhase === "password" && (
                    <div className="space-y-4">
                      <Input 
                        label="Username"
                        labelClassName="text-white lg:text-gray-700" 
                        placeholder="juandelacruz" 
                        required
                        value={formData.user.username} 
                        onChange={e => handleChange("user", "username", e.target.value)}
                      />
                      <div>
                        <Input 
                          label="Password"
                          labelClassName="text-white lg:text-gray-700"
                          type={showPassword ? "text" : "password"}
                          placeholder="••••••••" 
                          required
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
                              onClick={() => setShowPassword(prev => !prev)}
                              className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none"
                              tabIndex={-1}
                            >
                              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                          }
                        />
                        <div ref={passwordReqRef}>
                          <PasswordStrength password={formData.user.password} />
                        </div>
                      </div>
                      <Input 
                        label="Confirm Password"
                        labelClassName="text-white lg:text-gray-700"
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••" 
                        required
                        value={confirmPassword} 
                        onChange={e => setConfirmPassword(e.target.value)}
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
                        labelClassName="text-white lg:text-gray-700" 
                        placeholder="Juan" 
                        required
                        value={formData.profile.first_name} 
                        onChange={e => handleChange("profile", "first_name", e.target.value)}
                      />
                    </div>
                    <div className="flex-1">
                      <Input 
                        label="Last Name"
                        labelClassName="text-white lg:text-gray-700" 
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
                        labelClassName="text-white lg:text-gray-700" 
                        placeholder="A" 
                        maxLength={2}
                        value={formData.profile.middle_initial} 
                        onChange={e => handleChange("profile", "middle_initial", e.target.value)}
                      />
                    </div>
                    <div className="flex-1">
                      <Input 
                        label="Suffix (Optional)"
                        labelClassName="text-white lg:text-gray-700" 
                        placeholder="Jr."
                        list="suffix-options"
                        value={formData.profile.suffix} 
                        onChange={e => handleChange("profile", "suffix", e.target.value)}
                      />
                      <datalist id="suffix-options">
                        <option value="Jr." />
                        <option value="Sr." />
                        <option value="II" />
                        <option value="III" />
                        <option value="IV" />
                      </datalist>
                    </div>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1">
                      <Input 
                        label="Contact Number (Optional)"
                        labelClassName="text-white lg:text-gray-700" 
                        placeholder="09123456789"
                        value={formData.profile.contact_number} 
                        onChange={e => handleChange("profile", "contact_number", e.target.value)}
                      />
                    </div>
                    <div className="w-full sm:w-40">
                      <DatePicker 
                        label="Birthdate"
                        labelClassName="text-white lg:text-gray-700"
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
                      <label className="block text-sm font-medium text-white lg:text-slate-700">
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
                      <label className="block text-sm font-medium text-white lg:text-slate-700">
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
                      <label className="block text-sm font-medium text-white lg:text-slate-700">
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
                        labelClassName="text-white lg:text-gray-700" 
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
                        labelClassName="text-white lg:text-gray-700" 
                        placeholder="123"
                        value={formData.address.house_number} 
                        onChange={e => handleChange("address", "house_number", e.target.value)}
                      />
                    </div>
                    <div className="flex-1">
                      <Input 
                        label="Street (Optional)"
                        labelClassName="text-white lg:text-gray-700" 
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
            <div className="mt-4 flex items-center justify-between pt-6 border-t border-slate-100 shrink-0">
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
                <div></div> // Empty div for flex spacing
              )}

              {currentStep === 1 ? (
                setupPhase === "email" ? (
                  <Button type="button" onClick={handleRequestOTP} disabled={otpLoading} className="pl-6 pr-4 py-2">
                    {otpLoading ? "Sending..." : "Send OTP"}
                    <ChevronRight className="w-4 h-4 ml-2 inline" />
                  </Button>
                ) : setupPhase === "otp" ? (
                  <Button type="button" onClick={handleVerifyOTP} disabled={otpLoading} className="pl-6 pr-4 py-2">
                    {otpLoading ? "Verifying..." : "Verify OTP"}
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
