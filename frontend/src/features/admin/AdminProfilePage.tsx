"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/useProfile";
import {
  Camera,
  Calendar,
  ShieldCheck,
  Mail,
  KeyRound,
  Lock,
  Eye,
  EyeOff,
  Edit3,
  Upload,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Loader2,
  MapPin,
  Phone,
  User as UserIcon,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ColorPicker, Button, Modal, ConfirmDialog, useToast, Input } from "@/shared/ui";
import { PasswordStrength } from "@/shared/ui/forms/PasswordStrength";
import { EditProfileForm } from "@/features/profile/components/EditProfileForm";
import PasswordOtpModal from "@/features/profile/components/PasswordOtpModal";

export default function AdminProfilePage() {
  const { user, isLoading: authLoading } = useAuth();
  const {
    updateProfile,
    isUpdatingProfile,
    uploadAvatar,
    isUploadingAvatar,
    removeAvatar,
    isRemovingAvatar,
    requestPasswordOtp,
    isRequestingPasswordOtp,
    changePassword,
    isChangingPassword,
  } = useProfile();

  const { success, error: showError } = useToast();

  const [activeTab, setActiveTab] = useState<"profile" | "security" | "privacy">("profile");
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showAvatarMenu, setShowAvatarMenu] = useState(false);
  const [showViewAvatarModal, setShowViewAvatarModal] = useState(false);
  const [showRemoveAvatarConfirm, setShowRemoveAvatarConfirm] = useState(false);

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [showPasswordOtpModal, setShowPasswordOtpModal] = useState(false);
  const [passwordOtpCooldown, setPasswordOtpCooldown] = useState(60);

  const avatarMenuRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Close avatar dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (avatarMenuRef.current && !avatarMenuRef.current.contains(event.target as Node)) {
        setShowAvatarMenu(false);
      }
    };
    if (showAvatarMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showAvatarMenu]);

  if (authLoading || !user) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const profile = (user as any).profile || {};
  const joinedDate = user.created_at
    ? new Date(user.created_at).toLocaleDateString("en-US", { month: "long", year: "numeric" })
    : "Recently";

  // Cover Color
  const handleSaveColor = async (color: string) => {
    try {
      await updateProfile({ cover_color: color });
      setShowColorPicker(false);
      success("Cover Updated", "Your profile cover color has been updated.");
    } catch (err: any) {
      showError("Update Failed", err?.message || "Failed to update cover color.");
    }
  };

  // Avatar Upload
  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      showError("Invalid File", "Please select a valid image file.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      showError("File Too Large", "Profile picture must be under 5MB.");
      return;
    }

    try {
      await uploadAvatar(file);
      success("Picture Updated", "Your profile picture has been updated.");
    } catch (err: any) {
      console.error(err);
      showError("Upload Failed", err?.message || "Failed to upload profile picture.");
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleConfirmRemoveAvatar = async () => {
    try {
      await removeAvatar();
      setShowRemoveAvatarConfirm(false);
      success("Picture Removed", "Your profile picture has been removed.");
    } catch (err: any) {
      console.error(err);
      showError("Removal Failed", err?.message || "Failed to remove profile picture.");
    }
  };

  // Profile Edit
  const handleEditProfileSubmit = async (payload: any) => {
    try {
      await updateProfile(payload);
      setIsEditingProfile(false);
      success("Profile Saved", "Your profile details have been successfully updated.");
    } catch (err: any) {
      console.error(err);
      showError("Save Failed", err?.response?.data?.detail || err?.message || "Failed to save profile.");
    }
  };

  // Password Change
  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError("");

    if (!currentPassword) {
      setPasswordError("Please enter your current password.");
      return;
    }
    if (newPassword.length < 6) {
      setPasswordError("New password must be at least 6 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }

    try {
      const res = await requestPasswordOtp({ current_password: currentPassword });
      setPasswordOtpCooldown(res.cooldown_seconds || 60);
      setShowPasswordOtpModal(true);
      success("Verification Code Sent", "We sent a 6-digit confirmation code to your email address.");
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Failed to send verification code.";
      setPasswordError(detail);
      showError("Verification Failed", detail);
    }
  };

  const handleVerifyPasswordOtp = async (code: string) => {
    await changePassword({
      current_password: currentPassword,
      new_password: newPassword,
      otp_code: code,
    });
    success("Password Updated", "Your password has been changed successfully.");
    setShowPasswordOtpModal(false);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
  };

  const handleResendPasswordOtp = async () => {
    const res = await requestPasswordOtp({ current_password: currentPassword });
    success("Code Resent", "A new 6-digit confirmation code has been sent to your email.");
    return res.cooldown_seconds || 60;
  };

  // Privacy toggles
  const handleNameDisplayToggle = async (e: React.ChangeEvent<HTMLInputElement>) => {
    try {
      await updateProfile({ display_full_name: e.target.checked });
      success("Setting Updated", `Full name will now be ${e.target.checked ? "visible" : "hidden"} on your profile.`);
    } catch (err: any) {
      showError("Update Failed", err?.message || "Failed to update privacy setting.");
    }
  };

  const handleHideProfilePictureToggle = async (e: React.ChangeEvent<HTMLInputElement>) => {
    try {
      await updateProfile({ hide_profile_picture: e.target.checked });
      success("Setting Updated", `Profile picture will now be ${e.target.checked ? "hidden" : "visible"}.`);
    } catch (err: any) {
      showError("Update Failed", err?.message || "Failed to update profile picture visibility.");
    }
  };

  return (
    <div className="min-h-full bg-slate-50 flex flex-col relative pb-16">
      {/* Cover Header */}
      <div className="relative">
        <div
          className="h-44 sm:h-56 w-full relative transition-colors duration-500"
          style={{ backgroundColor: profile.cover_color || "#3b82f6" }}
        >
          <div className="absolute inset-0 bg-gradient-to-t from-black/45 via-black/15 to-transparent"></div>
          <div className="absolute bottom-4 right-4 sm:right-8">
            <div className="relative">
              <button
                onClick={() => setShowColorPicker(!showColorPicker)}
                className="flex items-center gap-2 bg-white/25 backdrop-blur-md hover:bg-white/35 text-white px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-medium transition-all shadow-sm"
              >
                <Edit3 className="w-4 h-4" />
                <span>Change Cover</span>
              </button>
              {showColorPicker && (
                <div className="absolute right-0 bottom-full mb-2 z-50">
                  <ColorPicker
                    initialColor={profile.cover_color || "#3b82f6"}
                    onSave={handleSaveColor}
                    onCancel={() => setShowColorPicker(false)}
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Profile Info & Avatar */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative -mt-14 sm:-mt-20 mb-6 flex flex-col sm:flex-row items-center sm:items-end gap-4 sm:gap-6">
            {/* Avatar container */}
            <div className="relative group shrink-0" ref={avatarMenuRef}>
              <input
                type="file"
                ref={fileInputRef}
                accept="image/png,image/jpeg,image/webp,image/jpg"
                onChange={handleFileSelected}
                className="hidden"
              />

              <div
                className="w-28 h-28 sm:w-36 sm:h-36 rounded-full border-4 border-white shadow-xl overflow-hidden bg-white relative cursor-pointer group-hover:ring-4 group-hover:ring-blue-100 transition-all"
                onClick={() => profile.avatar_url && setShowViewAvatarModal(true)}
                title="Click to view profile picture"
              >
                {isUploadingAvatar || isRemovingAvatar ? (
                  <div className="w-full h-full bg-slate-100 flex flex-col items-center justify-center text-blue-600 gap-1">
                    <Loader2 className="w-7 h-7 animate-spin" />
                    <span className="text-[10px] font-semibold">Updating...</span>
                  </div>
                ) : profile.avatar_url && !profile.hide_profile_picture ? (
                  <img
                    src={profile.avatar_url}
                    alt={user.username}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center text-blue-600 text-3xl sm:text-5xl font-bold select-none">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>

              {profile.hide_profile_picture && (
                <div
                  title="Profile picture is private"
                  className="absolute top-1 left-1 bg-slate-900/80 backdrop-blur-sm text-amber-300 p-1.5 rounded-full shadow border border-white/20"
                >
                  <EyeOff className="w-3.5 h-3.5" />
                </div>
              )}

              {/* Camera Trigger */}
              <button
                onClick={() => setShowAvatarMenu(!showAvatarMenu)}
                disabled={isUploadingAvatar || isRemovingAvatar}
                aria-label="Profile picture actions"
                className="absolute bottom-1 right-1 bg-slate-900 text-white p-2 rounded-full shadow-lg hover:bg-slate-800 transition-colors disabled:opacity-50"
              >
                {isUploadingAvatar ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Camera className="w-4 h-4" />
                )}
              </button>

              {/* Avatar Menu */}
              {showAvatarMenu && (
                <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-52 bg-white rounded-xl shadow-xl border border-slate-100 py-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
                  {profile.avatar_url && (
                    <button
                      className="w-full text-left px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-2.5"
                      onClick={() => {
                        setShowAvatarMenu(false);
                        setShowViewAvatarModal(true);
                      }}
                    >
                      <Eye className="w-4 h-4 text-slate-500" />
                      <span>View Profile Picture</span>
                    </button>
                  )}
                  <button
                    className="w-full text-left px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-2.5"
                    onClick={() => {
                      setShowAvatarMenu(false);
                      fileInputRef.current?.click();
                    }}
                  >
                    <Upload className="w-4 h-4 text-slate-500" />
                    <span>Change Profile Picture</span>
                  </button>
                  {profile.avatar_url && (
                    <>
                      <div className="border-t border-slate-100 my-1"></div>
                      <button
                        className="w-full text-left px-4 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2.5"
                        onClick={() => {
                          setShowAvatarMenu(false);
                          setShowRemoveAvatarConfirm(true);
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                        <span>Remove Picture</span>
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* User Meta */}
            <div className="flex-1 text-center sm:text-left mt-1 sm:mt-4">
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
                <h1 className="text-xl sm:text-2xl font-bold text-slate-900">
                  {profile.first_name && profile.display_full_name !== false
                    ? `${profile.first_name} ${profile.last_name || ""}`.trim()
                    : user.username}
                </h1>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  {(user as any)?.role?.name || "Staff Member"}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-500 flex items-center justify-center sm:justify-start gap-1.5 mt-1">
                <Calendar className="w-3.5 h-3.5" /> Joined {joinedDate}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 mb-6 gap-6">
          <button
            onClick={() => {
              setActiveTab("profile");
              setIsEditingProfile(false);
            }}
            className={`pb-3 text-sm font-semibold transition-colors relative ${
              activeTab === "profile"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Personal Information
          </button>
          <button
            onClick={() => setActiveTab("security")}
            className={`pb-3 text-sm font-semibold transition-colors relative ${
              activeTab === "security"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Password & Security
          </button>
          <button
            onClick={() => setActiveTab("privacy")}
            className={`pb-3 text-sm font-semibold transition-colors relative ${
              activeTab === "privacy"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Privacy Settings
          </button>
        </div>

        {/* Tab 1: Personal Information */}
        {activeTab === "profile" && (
          <div>
            {isEditingProfile ? (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
                <div className="flex items-center justify-between pb-6 mb-6 border-b border-slate-100">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">Edit Profile Details</h2>
                    <p className="text-sm text-slate-500">Update your name, contact information, and address</p>
                  </div>
                </div>
                <EditProfileForm
                  initialProfile={profile}
                  initialUsername={user.username}
                  isUpdating={isUpdatingProfile}
                  onSubmit={handleEditProfileSubmit}
                  onCancel={() => setIsEditingProfile(false)}
                />
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Card: Staff Summary */}
                <div className="lg:col-span-1 space-y-6">
                  <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
                      Staff Identification
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <div className="text-xs text-slate-500">Official Role</div>
                        <div className="text-sm font-bold text-slate-900 flex items-center gap-1.5 mt-0.5">
                          <ShieldCheck className="w-4 h-4 text-blue-600" />
                          {(user as any)?.role?.name || "Staff"}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Staff Account ID</div>
                        <div className="text-sm font-mono font-medium text-slate-800 mt-0.5">
                          #{user.id}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Verified Email</div>
                        <div className="text-sm font-medium text-slate-800 mt-0.5 truncate">
                          {user.email}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Account Status</div>
                        <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 mt-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          Active
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Card: Profile & Address Details */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
                      <div>
                        <h2 className="text-lg font-bold text-slate-900">Personal Details</h2>
                        <p className="text-xs sm:text-sm text-slate-500">
                          Your administrative identity and contact details
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        onClick={() => setIsEditingProfile(true)}
                        className="flex items-center gap-2 rounded-xl text-xs sm:text-sm"
                      >
                        <Edit3 className="w-4 h-4 text-slate-600" />
                        Edit Profile
                      </Button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div>
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          Full Name
                        </div>
                        <div className="text-sm font-medium text-slate-900 mt-1">
                          {profile.first_name || profile.last_name
                            ? `${profile.first_name || ""} ${profile.middle_initial ? profile.middle_initial + "." : ""} ${profile.last_name || ""} ${profile.suffix || ""}`.trim()
                            : "Not specified"}
                        </div>
                      </div>

                      <div>
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          Username
                        </div>
                        <div className="text-sm font-medium text-slate-900 mt-1">
                          @{user.username}
                        </div>
                      </div>

                      <div>
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          Contact Number
                        </div>
                        <div className="text-sm font-medium text-slate-900 mt-1 flex items-center gap-1.5">
                          <Phone className="w-3.5 h-3.5 text-slate-400" />
                          {profile.contact_number || "Not specified"}
                        </div>
                      </div>

                      <div>
                        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                          Birthdate
                        </div>
                        <div className="text-sm font-medium text-slate-900 mt-1 flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          {profile.birthdate
                            ? new Date(profile.birthdate).toLocaleDateString("en-US", {
                                month: "long",
                                day: "numeric",
                                year: "numeric",
                              })
                            : "Not specified"}
                        </div>
                      </div>
                    </div>

                    <div className="border-t border-slate-100 my-6"></div>

                    <div>
                      <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-blue-600" />
                        Official Address
                      </h3>
                      {profile.address && (profile.address.city_municipality || profile.address.province) ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-xs text-slate-500 block">Street / House No.</span>
                            <span className="font-medium text-slate-800">
                              {[profile.address.house_number, profile.address.street].filter(Boolean).join(" ") || "—"}
                            </span>
                          </div>
                          <div>
                            <span className="text-xs text-slate-500 block">Barangay</span>
                            <span className="font-medium text-slate-800">
                              {profile.address.barangay || "—"}
                            </span>
                          </div>
                          <div>
                            <span className="text-xs text-slate-500 block">City / Municipality</span>
                            <span className="font-medium text-slate-800">
                              {profile.address.city_municipality || "—"}
                            </span>
                          </div>
                          <div>
                            <span className="text-xs text-slate-500 block">Province & Postal Code</span>
                            <span className="font-medium text-slate-800">
                              {[profile.address.province, profile.address.postal_code].filter(Boolean).join(", ") || "—"}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs sm:text-sm text-slate-500 italic">
                          No address has been provided yet. Click "Edit Profile" above to configure your official address.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Password & Security */}
        {activeTab === "security" && (
          <div className="max-w-2xl bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-slate-100">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <KeyRound className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">Change Password</h2>
                <p className="text-xs sm:text-sm text-slate-500">
                  Ensure your staff account stays secure with a strong password.
                </p>
              </div>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-5">
              {passwordError && (
                <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-xs sm:text-sm text-red-700 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-red-500" />
                  <span>{passwordError}</span>
                </div>
              )}

              {/* Current Password */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Current Password
                </label>
                <Input
                  type={showCurrentPassword ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                  required
                  rightIcon={
                    <button
                      type="button"
                      onMouseDown={() => setShowCurrentPassword(true)}
                      onMouseUp={() => setShowCurrentPassword(false)}
                      onMouseLeave={() => setShowCurrentPassword(false)}
                      onTouchStart={() => setShowCurrentPassword(true)}
                      onTouchEnd={() => setShowCurrentPassword(false)}
                      onTouchCancel={() => setShowCurrentPassword(false)}
                      className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none select-none cursor-pointer p-1"
                      tabIndex={-1}
                      aria-label="Hold to view current password"
                      title="Hold to view current password"
                    >
                      {showCurrentPassword ? <Eye className="w-4 h-4 text-blue-600" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                  }
                />
              </div>

              {/* New Password */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  New Password
                </label>
                <Input
                  type={showNewPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter strong new password"
                  required
                  rightIcon={
                    <button
                      type="button"
                      onMouseDown={() => setShowNewPassword(true)}
                      onMouseUp={() => setShowNewPassword(false)}
                      onMouseLeave={() => setShowNewPassword(false)}
                      onTouchStart={() => setShowNewPassword(true)}
                      onTouchEnd={() => setShowNewPassword(false)}
                      onTouchCancel={() => setShowNewPassword(false)}
                      className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none select-none cursor-pointer p-1"
                      tabIndex={-1}
                      aria-label="Hold to view new password"
                      title="Hold to view new password"
                    >
                      {showNewPassword ? <Eye className="w-4 h-4 text-blue-600" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                  }
                />
                <div className="mt-2">
                  <PasswordStrength password={newPassword} />
                </div>
              </div>

              {/* Confirm New Password */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Confirm New Password
                </label>
                <Input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                  required
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


              <div className="pt-4 flex justify-end">
                <Button
                  type="submit"
                  disabled={isChangingPassword || isRequestingPasswordOtp}
                  className="rounded-xl px-6 flex items-center gap-2"
                >
                  {isRequestingPasswordOtp ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Sending Code...
                    </>
                  ) : isChangingPassword ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    <>
                      <Lock className="w-4 h-4" />
                      Update Password
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Tab 3: Privacy Settings */}
        {activeTab === "privacy" && (
          <div className="max-w-2xl bg-white rounded-2xl shadow-sm border border-slate-200 p-6 sm:p-8">
            <h2 className="text-lg font-bold text-slate-900 mb-1">Privacy Preferences</h2>
            <p className="text-xs sm:text-sm text-slate-500 mb-6">
              Configure how your profile information is shown across the platform.
            </p>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl border border-slate-100 bg-slate-50/60">
                <div>
                  <p className="font-medium text-slate-900 text-sm sm:text-base">Display Full Name</p>
                  <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                    Show your real name on audit logs, reports, and administrative activities. If disabled, your username will be displayed instead.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer shrink-0 ml-4">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={profile.display_full_name ?? true}
                    onChange={handleNameDisplayToggle}
                    disabled={isUpdatingProfile}
                  />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between p-4 rounded-xl border border-slate-100 bg-slate-50/60">
                <div>
                  <p className="font-medium text-slate-900 text-sm sm:text-base">Hide Profile Picture</p>
                  <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                    Hide your profile picture across all interfaces. A fallback initial badge will be shown instead.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer shrink-0 ml-4">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={profile.hide_profile_picture ?? false}
                    onChange={handleHideProfilePictureToggle}
                    disabled={isUpdatingProfile}
                  />
                  <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* View Avatar Modal */}
      <Modal
        isOpen={showViewAvatarModal}
        onClose={() => setShowViewAvatarModal(false)}
        title="Profile Picture"
      >
        <div className="flex justify-center p-4">
          <img
            src={profile.avatar_url}
            alt={user.username}
            className="max-w-full max-h-[70vh] rounded-2xl object-contain shadow-lg"
          />
        </div>
      </Modal>

      {/* Remove Avatar Confirmation */}
      <ConfirmDialog
        isOpen={showRemoveAvatarConfirm}
        onCancel={() => setShowRemoveAvatarConfirm(false)}
        onConfirm={handleConfirmRemoveAvatar}
        title="Remove Profile Picture"
        message="Are you sure you want to remove your profile picture? A letter avatar will be used instead."
        confirmLabel="Remove Picture"
        cancelLabel="Cancel"
        variant="destructive"
        isLoading={isRemovingAvatar}
      />

      {/* Email OTP Verification Modal */}
      <PasswordOtpModal
        isOpen={showPasswordOtpModal}
        onClose={() => setShowPasswordOtpModal(false)}
        email={user?.email || ""}
        onVerify={handleVerifyPasswordOtp}
        onResendOtp={handleResendPasswordOtp}
        initialCooldown={passwordOtpCooldown}
      />
    </div>
  );
}

