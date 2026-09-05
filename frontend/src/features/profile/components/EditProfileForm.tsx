"use client";

import { useState, useEffect } from "react";
import { LocationPickerModal, LocationItem } from "@/features/auth/components/LocationPickerModal";
import { DatePicker } from "@/shared/ui/DatePicker";
import { Input } from "@/shared/ui/Input";
import { Select } from "@/shared/ui/Select";
import { CheckCircle, Loader2 } from "lucide-react";
import { useToast } from "@/shared/ui/Toast";

// Metro Manila constant
const METRO_MANILA_CODE = "130000000";

interface EditProfileFormProps {
  initialProfile: any;
  isUpdating: boolean;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
}

export function EditProfileForm({ initialProfile, isUpdating, onSubmit, onCancel }: EditProfileFormProps) {
  const { error: showError } = useToast();
  
  const [activePicker, setActivePicker] = useState<"province" | "city" | "barangay" | null>(null);

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
      birthdate: initialProfile.birthdate ? new Date(initialProfile.birthdate).toISOString().split('T')[0] : "",
    },
    address: {
      house_number: initialProfile.address?.house_number || "",
      street: initialProfile.address?.street || "",
      barangay: initialProfile.address?.barangay || "",
      city_municipality: initialProfile.address?.city_municipality || "",
      province: initialProfile.address?.province || "",
      postal_code: initialProfile.address?.postal_code || "",
      country: "Philippines",
    }
  });

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

  const handleChange = (section: "profile" | "address", field: string, value: any) => {
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
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

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-6">
        <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-2">Personal Information</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input 
            label="First Name"
            labelClassName="text-slate-700 font-medium"
            required
            value={formData.profile.first_name}
            onChange={(e) => handleChange("profile", "first_name", e.target.value)}
          />
          <Input 
            label="Last Name"
            labelClassName="text-slate-700 font-medium"
            required
            value={formData.profile.last_name}
            onChange={(e) => handleChange("profile", "last_name", e.target.value)}
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
              onChange={e => handleChange("profile", "birthdate", e.target.value)}
              align="right"
            />
          </div>
        </div>

        <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-2 mt-6">Address Information</h4>
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">Province / Region <span className="text-red-500">*</span></label>
              <button 
                type="button" 
                onClick={() => setActivePicker("province")}
                className="w-full px-4 py-2.5 text-left rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all hover:bg-slate-50 truncate"
              >
                {formData.address.province || "Select Province"}
              </button>
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">City / Municipality <span className="text-red-500">*</span></label>
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
              <label className="text-sm font-medium text-slate-700">Barangay <span className="text-red-500">*</span></label>
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
              <label className="text-sm font-medium text-slate-700">Postal Code <span className="text-gray-400 font-normal ml-1">(Optional)</span></label>
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
              <label className="text-sm font-medium text-slate-700">House No. <span className="text-gray-400 font-normal ml-1">(Optional)</span></label>
              <input 
                type="text" 
                value={formData.address.house_number}
                onChange={(e) => handleChange("address", "house_number", e.target.value)}
                placeholder="123"
                className="w-full border border-slate-200 rounded-lg px-4 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              />
            </div>
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium text-slate-700">Street <span className="text-gray-400 font-normal ml-1">(Optional)</span></label>
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
            className="px-6 py-2.5 rounded-xl font-medium text-slate-600 hover:bg-slate-50 border border-transparent transition-colors"
          >
            Cancel
          </button>
          <button 
            type="submit"
            disabled={isUpdating}
            className="px-6 py-2.5 rounded-xl font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-colors flex items-center gap-2 disabled:opacity-50"
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
