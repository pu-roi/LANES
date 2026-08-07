"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/useProfile";
import { 
  Camera, MapPin, Calendar, Activity, 
  ShieldCheck, AlertTriangle, FileText, 
  MessageSquare, Settings, CheckCircle, 
  XCircle, Loader2, Edit3 
} from "lucide-react";
import { ColorPicker } from "@/shared/ui/ColorPicker";
import { EditProfileForm } from "./components/EditProfileForm";

export default function ProfileView() {
  const { user, isLoading: authLoading } = useAuth();
  const { 
    updateProfile, isUpdatingProfile, 
    myReports, isLoadingReports, 
    myPosts, isLoadingPosts 
  } = useProfile();
  
  const [activeTab, setActiveTab] = useState<"reports" | "posts" | "settings">("reports");
  const [showAvatarMenu, setShowAvatarMenu] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showSettingsColorPicker, setShowSettingsColorPicker] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  if (authLoading) {
    return (
      <div className="flex-1 bg-slate-50 flex items-center justify-center p-4">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex-1 bg-slate-50 flex items-center justify-center p-4">
        <div className="text-slate-500">Please log in to view your profile.</div>
      </div>
    );
  }

  const profile = user.profile || {};
  const joinedDate = new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" }).format(new Date(user.created_at));
  
  const formatDate = (dateStr: string) => {
    return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" }).format(new Date(dateStr));
  };

  // Handlers
  const handleSaveColor = async (newColor: string, fromSettings: boolean = false) => {
    if (fromSettings) {
      setShowSettingsColorPicker(false);
    } else {
      setShowColorPicker(false);
    }
    
    if (newColor !== profile.cover_color) {
      try {
        await updateProfile({ cover_color: newColor });
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handlePrivacyToggle = async () => {
    try {
      await updateProfile({ is_public: !profile.is_public });
    } catch (err) {
      console.error(err);
    }
  };

  const handleEditProfileStart = () => {
    setIsEditingProfile(true);
  };

  const handleEditProfileSubmit = async (payload: any) => {
    try {
      await updateProfile(payload);
      setIsEditingProfile(false);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex-1 bg-slate-50 overflow-y-auto">
      {/* Header / Cover */}
      <div 
        className="h-64 w-full relative transition-colors duration-500" 
        style={{ backgroundColor: profile.cover_color || "#3b82f6" }}
      >
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
        <div className="absolute bottom-4 right-4 flex justify-end">
          <div className="relative">
            <button 
              onClick={() => setShowColorPicker(!showColorPicker)}
              className="flex items-center gap-2 bg-white/20 backdrop-blur-md hover:bg-white/30 text-white px-4 py-2 rounded-full text-sm font-medium transition-all"
            >
              <Edit3 className="w-4 h-4" />
              Change Cover
            </button>
            {showColorPicker && (
              <ColorPicker 
                initialColor={profile.cover_color || "#3b82f6"} 
                onSave={(color) => handleSaveColor(color)}
                onCancel={() => setShowColorPicker(false)}
              />
            )}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        {/* Profile Info & Avatar */}
        <div className="relative mb-8 flex flex-col sm:flex-row gap-4 sm:gap-6">
          <div className="shrink-0 w-32 sm:w-40 mx-auto sm:mx-0">
            <div className="relative -mt-16 sm:-mt-24 group">
              <div className="w-32 h-32 sm:w-40 sm:h-40 rounded-full border-4 border-white shadow-xl overflow-hidden bg-white">
                {profile.avatar_url ? (
                  <img src={profile.avatar_url} alt={user.username} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-blue-100 to-indigo-50 flex items-center justify-center text-blue-500 text-5xl font-bold">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              {/* Avatar Dropdown Trigger */}
              <button 
                onClick={() => setShowAvatarMenu(!showAvatarMenu)}
                className="absolute bottom-2 right-2 bg-slate-800 text-white p-2 rounded-full shadow-lg hover:bg-slate-700 transition-colors"
              >
                <Camera className="w-5 h-5" />
              </button>

              {/* Avatar Dropdown Menu */}
              {showAvatarMenu && (
                <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-48 bg-white rounded-xl shadow-xl border border-slate-100 py-2 z-50">
                  <button className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors" onClick={() => setShowAvatarMenu(false)}>
                    View Profile Picture
                  </button>
                  <button className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors" onClick={() => setShowAvatarMenu(false)}>
                    Change Profile Picture
                  </button>
                </div>
              )}
            </div>
          </div>
          
          <div className="flex-1 text-center sm:text-left mt-2 sm:mt-4">
            <h1 className="text-2xl font-bold text-slate-900">{profile.first_name ? `${profile.first_name} ${profile.last_name}` : user.username}</h1>
            <p className="text-sm text-slate-500 flex items-center justify-center sm:justify-start gap-2 mt-1">
              <Calendar className="w-4 h-4" /> Joined {joinedDate}
            </p>
          </div>
        </div>

        {/* 2-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Details & Metrics */}
          <div className="lg:col-span-1">
            <div className="space-y-6 sticky top-6">
              
              {/* Trust Score & Accuracy */}
              <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                <h3 className="text-base font-semibold text-slate-900 mb-6 flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-indigo-500" />
                  Reputation Metrics
                </h3>
                
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between items-end mb-2">
                      <span className="text-sm font-medium text-slate-600">Trust Score</span>
                      <span className="text-xl font-bold text-indigo-600">{profile.trust_score || 0}</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div 
                        className="bg-indigo-500 h-2 rounded-full" 
                        style={{ width: `${Math.min((profile.trust_score || 0), 100)}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-end mb-2">
                      <span className="text-sm font-medium text-slate-600">Accuracy Rate</span>
                      <span className="text-xl font-bold text-emerald-600">
                        {profile.accuracy_rate ? (profile.accuracy_rate * 100).toFixed(0) : 0}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div 
                        className="bg-emerald-500 h-2 rounded-full" 
                        style={{ width: `${(profile.accuracy_rate || 0) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Reporting Stats */}
              <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                <h3 className="text-base font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-500" />
                  Reporting Activity
                </h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-blue-50 p-4 rounded-xl">
                    <div className="text-blue-500 mb-1"><FileText className="w-5 h-5" /></div>
                    <div className="text-2xl font-bold text-slate-900">{profile.reports_submitted || 0}</div>
                    <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Submitted</div>
                  </div>
                  <div className="bg-emerald-50 p-4 rounded-xl">
                    <div className="text-emerald-500 mb-1"><CheckCircle className="w-5 h-5" /></div>
                    <div className="text-2xl font-bold text-slate-900">{profile.reports_approved || 0}</div>
                    <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Approved</div>
                  </div>
                  <div className="bg-red-50 p-4 rounded-xl">
                    <div className="text-red-500 mb-1"><XCircle className="w-5 h-5" /></div>
                    <div className="text-2xl font-bold text-slate-900">{profile.reports_rejected || 0}</div>
                    <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Rejected</div>
                  </div>
                </div>
              </div>

              {/* About / Personal Details */}
              <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                <h3 className="text-base font-semibold text-slate-900 mb-4">Personal Details</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <div className="text-slate-400 mt-0.5"><MessageSquare className="w-4 h-4" /></div>
                    <div>
                      <div className="text-sm font-medium text-slate-900">Email</div>
                      <div className="text-sm text-slate-500">{user.email}</div>
                    </div>
                  </li>
                  {profile.address && (
                    <li className="flex items-start gap-3">
                      <div className="text-slate-400 mt-0.5"><MapPin className="w-4 h-4" /></div>
                      <div>
                        <div className="text-sm font-medium text-slate-900">Location</div>
                        <div className="text-sm text-slate-500">
                          {profile.address.city_municipality || profile.address.province || "Philippines"}
                        </div>
                      </div>
                    </li>
                  )}
                </ul>
              </div>
              
            </div>
          </div>

          {/* Right Column: Tabs */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Tabs Navigation */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-2 flex overflow-x-auto">
              <button
                onClick={() => { setActiveTab("reports"); setIsEditingProfile(false); }}
                className={`flex-1 min-w-[120px] flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-medium transition-all ${
                  activeTab === "reports" ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <AlertTriangle className="w-4 h-4" /> Hazard Reports
              </button>
              <button
                onClick={() => { setActiveTab("posts"); setIsEditingProfile(false); }}
                className={`flex-1 min-w-[120px] flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-medium transition-all ${
                  activeTab === "posts" ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <MessageSquare className="w-4 h-4" /> Community Posts
              </button>
              <button
                onClick={() => setActiveTab("settings")}
                className={`flex-1 min-w-[120px] flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-medium transition-all ${
                  activeTab === "settings" ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <Settings className="w-4 h-4" /> Settings
              </button>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 min-h-[400px]">
              
              {activeTab === "reports" && (
                <div className="p-6">
                  <h3 className="text-base font-bold text-slate-900 mb-4">My Hazard Reports</h3>
                  {isLoadingReports ? (
                    <div className="py-12 flex justify-center"><Loader2 className="w-6 h-6 text-slate-400 animate-spin" /></div>
                  ) : myReports?.length > 0 ? (
                    <div className="space-y-4">
                      {myReports.map((report: any) => (
                        <div key={report.id} className="p-4 rounded-xl border border-slate-100 hover:border-blue-100 hover:bg-blue-50/50 transition-colors">
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-sm font-medium bg-white px-2 py-1 border border-slate-200 rounded-md shadow-sm text-slate-700">
                              {report.severity.toUpperCase()}
                            </span>
                            <span className="text-xs text-slate-500">{formatDate(report.created_at)}</span>
                          </div>
                          <p className="text-slate-700 line-clamp-2">{report.raw_text}</p>
                          <div className="mt-3 flex items-center gap-2 text-xs font-medium">
                            Status: <span className={
                              report.status === "Approved" ? "text-emerald-600" : 
                              report.status === "Rejected" ? "text-red-600" : "text-amber-600"
                            }>{report.status}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-50 mb-3 text-slate-400">
                        <AlertTriangle className="w-6 h-6" />
                      </div>
                      <p className="text-slate-500">You haven't submitted any hazard reports yet.</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "posts" && (
                <div className="p-6">
                  <h3 className="text-base font-bold text-slate-900 mb-4">My Community Posts</h3>
                  {isLoadingPosts ? (
                    <div className="py-12 flex justify-center"><Loader2 className="w-6 h-6 text-slate-400 animate-spin" /></div>
                  ) : myPosts?.posts?.length > 0 ? (
                    <div className="space-y-4">
                      {myPosts.posts.map((post: any) => (
                        <div key={post.id} className="p-4 rounded-xl border border-slate-100 hover:border-blue-100 hover:bg-blue-50/50 transition-colors">
                          <p className="text-slate-700">{post.content}</p>
                          <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                            <span>{formatDate(post.created_at)}</span>
                            <div className="flex gap-4">
                              <span>↑ {post.upvotes}</span>
                              <span>💬 {post.comment_count}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-50 mb-3 text-slate-400">
                        <MessageSquare className="w-6 h-6" />
                      </div>
                      <p className="text-slate-500">You haven't posted in the community yet.</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "settings" && !isEditingProfile && (
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-base font-bold text-slate-900">Profile Settings</h3>
                    <button 
                      onClick={handleEditProfileStart}
                      className="text-sm font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
                    >
                      <Edit3 className="w-4 h-4" /> Edit Profile
                    </button>
                  </div>
                  
                  <div className="space-y-8">
                    {/* Privacy Settings */}
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Privacy</h4>
                      <div className="flex items-center justify-between p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                        <div>
                          <p className="font-medium text-slate-900">Public Profile</p>
                          <p className="text-sm text-slate-500 mt-1">Allow your profile and approved reports to be visible to other community members.</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer shrink-0">
                          <input 
                            type="checkbox" 
                            className="sr-only peer"
                            checked={profile.is_public ?? true}
                            onChange={handlePrivacyToggle}
                            disabled={isUpdatingProfile}
                          />
                          <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    </div>

                    {/* Customization */}
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Customization</h4>
                      <div className="flex items-center justify-between p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                        <div>
                          <p className="font-medium text-slate-900">Cover Color</p>
                          <p className="text-sm text-slate-500 mt-1">Personalize your profile header background color.</p>
                        </div>
                        <div className="relative flex items-center gap-3">
                          <div 
                            className="w-10 h-10 rounded-full border-2 border-white shadow-sm shrink-0 cursor-pointer"
                            style={{ backgroundColor: profile.cover_color || "#3b82f6" }}
                            onClick={() => setShowSettingsColorPicker(!showSettingsColorPicker)}
                          ></div>
                          <span className="text-xs font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded">
                            {profile.cover_color || "#3b82f6"}
                          </span>
                          
                          {showSettingsColorPicker && (
                            <ColorPicker 
                              initialColor={profile.cover_color || "#3b82f6"} 
                              onSave={(color) => handleSaveColor(color, true)}
                              onCancel={() => setShowSettingsColorPicker(false)}
                            />
                          )}
                        </div>
                      </div>
                    </div>

                  </div>
                </div>
              )}

              {activeTab === "settings" && isEditingProfile && (
                <div className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-base font-bold text-slate-900">Edit Profile</h3>
                  </div>
                  
                  <EditProfileForm 
                    initialProfile={profile} 
                    isUpdating={isUpdatingProfile} 
                    onSubmit={handleEditProfileSubmit} 
                    onCancel={() => setIsEditingProfile(false)} 
                  />
                </div>
              )}

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
