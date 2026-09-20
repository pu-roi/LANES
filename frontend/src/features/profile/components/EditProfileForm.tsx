"use client";

import { useState, useEffect } from "react";
import { LocationPickerModal, LocationItem } from "@/features/auth/components/LocationPickerModal";
import { DatePicker } from "@/shared/ui";
import { Input } from "@/shared/ui";
import { Select } from "@/shared/ui";
import { CheckCircle, Loader2, ShieldCheck, AlertCircle } from "lucide-react";
import { useToast } from "@/shared/ui";
import { toNameCase } from "@/lib/utils";

// Metro Manila constant
const METRO_MANILA_CODE = "130000000";

interface EditProfileFormProps {
  initialProfile: any;
  initialUsername?: string;
  isUpdating: boolean;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
}

export function EditProfileForm({
  initialProfile,
  initialUsername = "",
  isUpdating,
  onSubmit,
  onCancel,
}: EditProfileFormProps) {
  const { error: showError } = useToast();

  const [activePicker, setActivePicker] = useState<"province" | "city" | "barangay" | null>(null);

  // Username State & Verification
  const [username, setUsername] = useState(initialUsername || "");
  const [usernameStatus, setUsernameStatus] = useState<"idle" | "checking" | "available" | "taken" | "invalid">("idle");
  const [usernameFeedback, setUsernameFeedback] = useState("");
  const [verifiedUsername, setVerifiedUsername] = useState(initialUsername || "");
  const [isVerifying, setIsVerifying] = useState(false);

  // PSGC State
  const [provinces, setProvinces] = useState<LocationItem[]>([]);
  const [cities, setCities] = useState<LocationItem[]>([]);
  const [barangays, setBarangays] = useState<LocationItem[]>([]);

  const [selectedProvinceCode, setSelectedProvinceCode] = useState("");
  const [selectedCityCode, setSelectedCityCode] = useState("");

  const [formData, setFormData] = useState({
    profile: {
      first_name: initialProfile.first_name || "",
      last_name: initialProfile.last_name || "",
      middle_initial: initialProfile.middle_initial || "",
      suffix: initialProfile.suffix || "",
      contact_number: initialProfile.contact_number || "",
      birthdate: initialProfile.birthdate ? new Date(initialProfile.birthdate).toISOString().split("T")[0] : "",
    },
    address: {
      house_number: initialProfile.address?.house_number || "",
      street: initialProfile.address?.street || "",
      barangay: initialProfile.address?.barangay || "",
      city_municipality: initialProfile.address?.city_municipality || "",
      province: initialProfile.address?.province || "",
      postal_code: initialProfile.address?.postal_code || "",
      country: "Philippines",
    },
  });

  // Keep state synced if initial props change
  useEffect(() => {
    if (initialUsername) {
      setUsername(initialUsername);
      setVerifiedUsername(initialUsername);
    }
  }, [initialUsername]);

  // Fetch Provinces on Mount
  useEffect(() => {
    async function fetchProvinces() {
      try {
        const res = await fetch("https://psgc.gitlab.io/api/provinces/");
        const data = await res.json();
        const mappedProvinces = data.map((p: any) => ({
          code: p.code,
          name: p.name,
        }));

        mappedProvinces.push({
          code: METRO_MANILA_CODE,
          name: "Metro Manila",
          isPinned: true,
        });

        setProvinces(mappedProvinces.sort((a: any, b: any) => a.name.localeCompare(b.name)));

        if (initialProfile.address?.province) {
          const found = mappedProvinces.find((p: any) => p.name === initialProfile.address?.province);
          if (found) setSelectedProvinceCode(found.code);
        }
      } catch (err: any) {
        showError("Location Error", "Failed to fetch provinces.");
      }
    }
    fetchProvinces();
  }, [initialProfile.address?.province, showError]);

  // Fetch Cities when Province changes
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

        const mappedCities = data.map((c: any) => ({ code: c.code, name: normalizeCityName(c.name) }));
        setCities(mappedCities);

        if (initialProfile.address?.city_municipality) {
          const found = mappedCities.find((c: any) => c.name === initialProfile.address?.city_municipality);
          if (found) setSelectedCityCode(found.code);
        }
      } catch (err: any) {
        showError("Location Error", "Failed to fetch cities.");
      }
    }
    fetchCities();
  }, [selectedProvinceCode, initialProfile.address?.city_municipality, showError]);

  // Fetch Barangays when City changes
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
        showError("Location Error", "Failed to fetch barangays.");
      }
    }
    fetchBarangays();
  }, [selectedCityCode, showError]);

  const handleUsernameChange = (val: string) => {
    // Sanitize in real-time: lowercase, only alphanumeric, dots, underscores
    const sanitized = val.toLowerCase().replace(/[^a-zA-Z0-9._]/g, "").slice(0, 30);
    setUsername(sanitized);

    if (sanitized === (initialUsername || "").toLowerCase()) {
      setUsernameStatus("idle");
      setUsernameFeedback("");
      setVerifiedUsername(sanitized);
    } else {
      setUsernameStatus("idle");
      setUsernameFeedback("");
      setVerifiedUsername("");
    }
  };

  const handleVerifyUsername = async () => {
    const clean = username.trim().toLowerCase();
    if (!clean) {
      setUsernameStatus("invalid");
      setUsernameFeedback("Please enter a username to verify.");
      return;
    }
    if (clean.length < 3) {
      setUsernameStatus("invalid");
      setUsernameFeedback("Username must be at least 3 characters long.");
      return;
    }
    if (clean.length > 30) {
      setUsernameStatus("invalid");
      setUsernameFeedback("Username must not exceed 30 characters.");
      return;
    }
    if (!/^[a-zA-Z0-9._]+$/.test(clean)) {
      setUsernameStatus("invalid");
      setUsernameFeedback("Username can only contain letters, numbers, dots, and underscores.");
      return;
    }
    if (clean.startsWith(".") || clean.startsWith("_") || clean.endsWith(".") || clean.endsWith("_") || clean.includes("..") || clean.includes("__")) {
      setUsernameStatus("invalid");
      setUsernameFeedback("Username cannot start/end with symbols or contain consecutive symbols.");
      return;
    }

    if (clean === (initialUsername || "").toLowerCase()) {
      setUsernameStatus("available");
      setUsernameFeedback("This is your current username.");
      setVerifiedUsername(clean);
      return;
    }

    setIsVerifying(true);
    setUsernameStatus("checking");
    setUsernameFeedback("Checking availability...");
    try {
      const resUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const token = typeof window !== "undefined" ? localStorage.getItem("lanes_token") : null;
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${resUrl}/users/check-username?username=${encodeURIComponent(clean)}`, {
        headers,
      });
      const data = await res.json();
      if (data.available) {
        setUsernameStatus("available");
        setUsernameFeedback(data.message || `Username @${clean} is available!`);
        setVerifiedUsername(clean);
      } else {
        setUsernameStatus("taken");
        setUsernameFeedback(data.message || "Username is already taken. Please choose another.");
        setVerifiedUsername("");
      }
    } catch (err: any) {
      setUsernameStatus("invalid");
      setUsernameFeedback("Unable to check username availability. Please try again.");
      setVerifiedUsername("");
    } finally {
      setIsVerifying(false);
    }
  };

  const handleChange = (section: "profile" | "address", field: string, value: any) => {
    let finalValue = value;

    if (section === "profile") {
      if (field === "first_name" || field === "last_name") {
        finalValue = toNameCase(value);
      } else if (field === "middle_initial") {
        const prevVal = formData.profile.middle_initial || "";
        const rawLetters = value.replace(/[^a-zA-Z]/g, "").toUpperCase().slice(0, 3);
        const prevLetters = prevVal.replace(/[^a-zA-Z]/g, "").toUpperCase();

        if (rawLetters.length < prevLetters.length) {
          finalValue = rawLetters ? rawLetters.split("").map((c: string) => c + ".").join("") : "";
        } else if (rawLetters.length > prevLetters.length) {
          finalValue = rawLetters.split("").map((c: string) => c + ".").join("");
        } else {
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const cleanUsername = username.trim().toLowerCase();
    const isUsernameChanged = cleanUsername !== (initialUsername || "").toLowerCase();

    // Enforce username uniqueness verification
    if (isUsernameChanged) {
      if (verifiedUsername !== cleanUsername || usernameStatus !== "available") {
        showError(
          "Username Not Verified",
          "Please click 'Verify Availability' to ensure your new username is unique before saving."
        );
        return;
      }
    }

    if (formData.profile.contact_number && formData.profile.contact_number.length !== 11) {
      showError("Validation Error", "Contact number must be exactly 11 digits.");
      return;
    }

    if (formData.address.province && (!formData.address.city_municipality || !formData.address.barangay)) {
      showError("Validation Error", "Please complete the city and barangay selections.");
      return;
    }

    const payload: any = {
      ...formData.profile,
      birthdate: formData.profile.birthdate || null,
    };

    if (isUsernameChanged) {
      payload.username = cleanUsername;
    }

    if (formData.address.province && formData.address.city_municipality && formData.address.barangay) {
      payload.address = formData.address;
    }

    onSubmit(payload);
  };

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

  const isUsernameChanged = username.trim().toLowerCase() !== (initialUsername || "").toLowerCase();
  const isUsernameNeedsVerification = isUsernameChanged && (verifiedUsername !== username.trim().toLowerCase() || usernameStatus !== "available");

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Account Username */}
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 sm:p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-3">
            <div>
              <label className="text-sm font-semibold text-slate-900 block">
                Username <span className="text-red-500">*</span>
              </label>
              <p className="text-xs text-slate-500">
                Your unique 1-to-1 handle across LANES. Must be verified before updating.
              </p>
            </div>
            {initialUsername && username.trim().toLowerCase() === initialUsername.toLowerCase() && (
              <span className="self-start sm:self-auto text-[11px] font-medium bg-blue-50 text-blue-700 px-2.5 py-0.5 rounded-full border border-blue-200/60">
                Current Handle
              </span>
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-semibold text-sm select-none">
                @
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => handleUsernameChange(e.target.value)}
                placeholder="juandelacruz"
                maxLength={30}
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck={false}
                className={`w-full pl-8 pr-3 py-2.5 text-sm rounded-xl border bg-white shadow-sm outline-none transition-all ${
                  usernameStatus === "available" && isUsernameChanged
                    ? "border-emerald-500 ring-2 ring-emerald-100"
                    : usernameStatus === "taken" || usernameStatus === "invalid"
                    ? "border-red-500 ring-2 ring-red-100"
                    : "border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                }`}
              />
            </div>

            <button
              type="button"
              onClick={handleVerifyUsername}
              disabled={isVerifying || isUpdating || !username.trim() || (!isUsernameChanged && usernameStatus === "idle")}
              className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all flex items-center justify-center gap-1.5 shrink-0 ${
                isUsernameNeedsVerification
                  ? "bg-blue-600 hover:bg-blue-700 text-white shadow-sm ring-2 ring-blue-200 cursor-pointer"
                  : "bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              }`}
            >
              {isVerifying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span>Checking...</span>
                </>
              ) : usernameStatus === "available" && isUsernameChanged ? (
                <>
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span className="text-emerald-700">Verified</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Verify Availability</span>
                </>
              )}
            </button>
          </div>

          {/* Feedback message */}
          {usernameFeedback && (
            <div
              className={`mt-2.5 text-xs flex items-center gap-1.5 font-medium ${
                usernameStatus === "available"
                  ? "text-emerald-600"
                  : usernameStatus === "taken" || usernameStatus === "invalid"
                  ? "text-red-600"
                  : "text-slate-500"
              }`}
            >
              {usernameStatus === "available" ? (
                <CheckCircle className="w-3.5 h-3.5 shrink-0 text-emerald-600" />
              ) : usernameStatus === "taken" || usernameStatus === "invalid" ? (
                <AlertCircle className="w-3.5 h-3.5 shrink-0 text-red-600" />
              ) : null}
              <span>{usernameFeedback}</span>
            </div>
          )}
        </div>

        <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-2">Personal Information</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="First Name"
            labelClassName="text-slate-700 font-medium"
            required
            autoCapitalize="words"
            autoComplete="given-name"
            value={formData.profile.first_name}
            onChange={(e) => handleChange("profile", "first_name", e.target.value)}
            onBlur={(e) => handleChange("profile", "first_name", e.target.value.trim())}
          />
          <Input
            label="Last Name"
            labelClassName="text-slate-700 font-medium"
            required
            autoCapitalize="words"
            autoComplete="family-name"
            value={formData.profile.last_name}
            onChange={(e) => handleChange("profile", "last_name", e.target.value)}
            onBlur={(e) => handleChange("profile", "last_name", e.target.value.trim())}
          />
          <Input
            label="M.I. (Optional)"
            labelClassName="text-slate-700 font-medium"
            placeholder="D.C."
            maxLength={5}
            value={formData.profile.middle_initial}
            onChange={(e) => handleChange("profile", "middle_initial", e.target.value)}
          />
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
          <Input
            label="Contact Number (Optional)"
            labelClassName="text-slate-700 font-medium"
            type="tel"
            placeholder="09123456789"
            value={formData.profile.contact_number}
            onChange={(e) => handleChange("profile", "contact_number", e.target.value)}
          />
          <div className="w-full sm:mt-1">
            <DatePicker
              label="Birthdate"
              labelClassName="text-slate-700"
              required
              value={formData.profile.birthdate}
              onChange={(e) => handleChange("profile", "birthdate", e.target.value)}
              align="right"
            />
          </div>
        </div>

        <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-2 mt-6">Address Information</h4>
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Province / Region <span className="text-red-500">*</span>
              </label>
              <button
                type="button"
                onClick={() => setActivePicker("province")}
                className="w-full px-4 py-2.5 text-left rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all hover:bg-slate-50 truncate"
              >
                {formData.address.province || "Select Province"}
              </button>
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">
                City / Municipality <span className="text-red-500">*</span>
              </label>
              <button
                type="button"
                onClick={() => setActivePicker("city")}
                disabled={!formData.address.province}
                className="w-full px-4 py-2.5 text-left rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 transition-all hover:bg-slate-50 truncate"
              >
                {formData.address.city_municipality || "Select City"}
              </button>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Barangay <span className="text-red-500">*</span>
              </label>
              <button
                type="button"
                onClick={() => setActivePicker("barangay")}
                disabled={!formData.address.city_municipality}
                className="w-full px-4 py-2.5 text-left rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 transition-all hover:bg-slate-50 truncate"
              >
                {formData.address.barangay || "Select Barangay"}
              </button>
            </div>
            <div className="w-full sm:w-1/3 space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Postal Code <span className="text-gray-400 font-normal ml-1">(Optional)</span>
              </label>
              <input
                type="text"
                value={formData.address.postal_code}
                onChange={(e) => handleChange("address", "postal_code", e.target.value)}
                placeholder="1210"
                className="w-full border border-slate-200 rounded-lg px-4 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              />
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="w-full sm:w-1/3 space-y-2">
              <label className="text-sm font-medium text-slate-700">
                House No. <span className="text-gray-400 font-normal ml-1">(Optional)</span>
              </label>
              <input
                type="text"
                value={formData.address.house_number}
                onChange={(e) => handleChange("address", "house_number", e.target.value)}
                placeholder="123"
                className="w-full border border-slate-200 rounded-lg px-4 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              />
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Street <span className="text-gray-400 font-normal ml-1">(Optional)</span>
              </label>
              <input
                type="text"
                value={formData.address.street}
                onChange={(e) => handleChange("address", "street", e.target.value)}
                placeholder="Main St"
                className="w-full border border-slate-200 rounded-lg px-4 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              />
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end gap-3 mt-8">
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-2.5 rounded-xl font-medium text-slate-600 hover:bg-slate-50 border border-transparent transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isUpdating || isUsernameNeedsVerification}
            className="px-6 py-2.5 rounded-xl font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isUpdating ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            Save Changes
          </button>
        </div>
      </form>

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
