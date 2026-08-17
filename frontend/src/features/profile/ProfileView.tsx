"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/useProfile";
import { 
  Camera, MapPin, Calendar, Activity, 
  ShieldCheck, AlertTriangle, FileText, 
  MessageSquare, Settings, CheckCircle, 
  XCircle, Loader2, Edit3, LogOut
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ColorPicker } from "@/shared/ui/ColorPicker";
import { EditProfileForm } from "./components/EditProfileForm";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { votePost, FeedPost } from "../feed/feedApi";
import { PostItem } from "../feed/PostItem";
import { PostDetailPage } from "../feed/PostDetailPage";
import { LeftSidebar } from "../feed/LeftSidebar";
import { RightSidebar } from "../feed/RightSidebar";
import { useToast, Button, Tabs, TabContentPanel } from "@/shared/ui";

export default function ProfileView() {
  const { user, isLoading: authLoading, logout } = useAuth();
  const { 
    updateProfile, isUpdatingProfile, 
    myReports, isLoadingReports, 
    myPosts, isLoadingPosts 
  } = useProfile();
  
  // "stats" is only used on mobile. On desktop, stats are always visible in the sidebar.
  const TABS = ["stats", "posts", "reports", "settings"];
  const [activeTab, setActiveTab] = useState<"stats" | "reports" | "posts" | "settings">("posts");
  const [tabDirection, setTabDirection] = useState(1);
  
  const handleTabChange = (newTab: "stats" | "reports" | "posts" | "settings") => {
    const currentIndex = TABS.indexOf(activeTab);
    const newIndex = TABS.indexOf(newTab);
    setTabDirection(newIndex > currentIndex ? 1 : -1);
    setActiveTab(newTab);
    setIsEditingProfile(false);
  };

  const [showAvatarMenu, setShowAvatarMenu] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [viewingPostId, setViewingPostId] = useState<number | null>(null);

  const sidebarRef = useRef<HTMLDivElement>(null);
  const [sidebarTop, setSidebarTop] = useState("1.5rem");

  useEffect(() => {
    const handleResize = () => {
      if (sidebarRef.current) {
        const height = sidebarRef.current.offsetHeight;
        const scrollContainer = sidebarRef.current.closest('.overflow-y-auto');
        const containerHeight = scrollContainer ? scrollContainer.clientHeight : window.innerHeight;
        
        if (height > containerHeight - 48) {
          setSidebarTop(`${containerHeight - height - 24}px`);
        } else {
          setSidebarTop("6rem");
        }
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [user, myReports, myPosts]);

  const queryClient = useQueryClient();
  const router = useRouter();
  const { error: showError } = useToast();

  const voteMutation = useMutation({
    mutationFn: ({ postId, type }: { postId: number, type: 'upvote' | 'downvote' }) => votePost(postId, type),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-posts'] });
    },
    onError: (err: any) => {
      if (err.status === 401) {
        showError('Login Required', 'Please log in first to interact with posts!');
      } else {
        showError('Failed to vote', err.message);
      }
    }
  });

  const handleVote = (postId: number, type: 'upvote' | 'downvote') => {
    voteMutation.mutate({ postId, type });
  };

  const handleViewMap = (lat: number, lng: number) => {
    router.push(`/map?lat=${lat}&lng=${lng}&zoom=16`);
  };

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

  const handleSaveColor = async (newColor: string) => {
    setShowColorPicker(false);
    
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

  const handleNameDisplayToggle = async () => {
    try {
      await updateProfile({ display_full_name: !(profile.display_full_name ?? true) });
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

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 20 : -20,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction > 0 ? -20 : 20,
      opacity: 0,
    }),
  };

  const renderStats = () => (
    <>
      {/* Trust Score & Accuracy */}
      <div className="lg:bg-white lg:rounded-2xl lg:shadow-sm border-b lg:border border-slate-100 lg:p-6 pb-6 mb-6">
        <h3 className="text-sm font-semibold tracking-wider uppercase text-slate-500 mb-6 flex items-center gap-2">
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
                {profile.accuracy_rate ? Number(profile.accuracy_rate).toFixed(0) : 0}%
              </span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div 
                className="bg-emerald-500 h-2 rounded-full" 
                style={{ width: `${Math.min(Math.max(profile.accuracy_rate || 0, 0), 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Reporting Stats */}
      <div className="lg:bg-white lg:rounded-2xl lg:shadow-sm border-b lg:border border-slate-100 lg:p-6 pb-6 mb-6">
        <h3 className="text-sm font-semibold tracking-wider uppercase text-slate-500 mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-500" />
          Reporting Activity
        </h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 p-4 rounded-xl">
            <div className="text-blue-500 mb-1"><FileText className="w-5 h-5" /></div>
            <div className="text-xl font-bold text-slate-900">{profile.reports_submitted || 0}</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Submitted</div>
          </div>
          <div className="bg-emerald-50 p-4 rounded-xl">
            <div className="text-emerald-500 mb-1"><CheckCircle className="w-5 h-5" /></div>
            <div className="text-xl font-bold text-slate-900">{profile.reports_approved || 0}</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Approved</div>
          </div>
          <div className="bg-red-50 p-4 rounded-xl">
            <div className="text-red-500 mb-1"><XCircle className="w-5 h-5" /></div>
            <div className="text-xl font-bold text-slate-900">{profile.reports_rejected || 0}</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Rejected</div>
          </div>
        </div>
      </div>

      {/* About / Personal Details */}
      <div className="lg:bg-white lg:rounded-2xl lg:shadow-sm lg:border border-slate-100 lg:p-6">
        <h3 className="text-sm font-semibold tracking-wider uppercase text-slate-500 mb-4">Personal Details</h3>
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
    </>
  );

  const renderReports = () => (
    <div className="p-6">
      <h3 className="text-base font-bold text-slate-900 mb-4 hidden lg:block">My Hazard Reports</h3>
      {isLoadingReports ? (
        <div className="py-12 flex justify-center"><Loader2 className="w-6 h-6 text-slate-400 animate-spin" /></div>
      ) : (myReports as any[])?.length > 0 ? (
        <div className="space-y-4">
          {(myReports as any[]).map((report: any) => (
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
  );

  const renderPosts = () => (
    <div className="pb-6">
      <h3 className="text-base font-bold text-slate-900 mb-2 px-6 pt-6 hidden lg:block">My Community Posts</h3>
      {isLoadingPosts ? (
        <div className="py-12 flex justify-center"><Loader2 className="w-6 h-6 text-slate-400 animate-spin" /></div>
      ) : (myPosts as any)?.posts?.length > 0 ? (
        <div className="flex flex-col">
          {(myPosts as any).posts.map((post: FeedPost) => (
            <PostItem 
              key={post.id}
              post={post} 
              onVote={handleVote}
              onViewMap={handleViewMap}
              onPostClick={(postId) => setViewingPostId(postId)}
            />
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
  );

  const renderSettings = () => {
    if (isEditingProfile) {
      return (
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
      );
    }
    
    return (
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-bold text-slate-900 hidden lg:block">Profile Settings</h3>
          <Button 
            variant="secondary"
            onClick={handleEditProfileStart}
            className="flex items-center gap-2"
          >
            <Edit3 className="w-4 h-4" /> Edit Profile
          </Button>
        </div>
        
        <div className="space-y-8">
          {/* Privacy Settings */}
          <div>
            <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Privacy</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                <div>
                  <p className="font-medium text-slate-900">Public Profile</p>
                  <p className="text-sm text-slate-500 mt-1">Allow your profile and approved reports to be visible to other community members.</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer shrink-0 ml-4">
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
              
              <div className="flex items-center justify-between p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                <div>
                  <p className="font-medium text-slate-900">Display Full Name</p>
                  <p className="text-sm text-slate-500 mt-1">Show your real name on your profile and posts. If disabled, your username will be used instead.</p>
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
            </div>
          </div>
          
          {/* Account Actions */}
          <div className="pt-4 mt-8 border-t border-slate-100 lg:hidden">
            <Button
              variant="danger"
              onClick={() => setShowLogoutConfirm(true)}
              className="w-full"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Log Out
            </Button>
          </div>
        </div>
      </div>
    );
  };

  if (viewingPostId !== null) {
    return (
      <>
        <style>{`
          @media (max-width: 640px) {
            #notification-bell {
              display: none !important;
            }
          }
        `}</style>
        {/* Background Mask for FloatingNav to match the community feed layout */}
        <div className="fixed top-0 left-0 right-0 h-[70px] bg-gray-50/75 backdrop-blur-lg border-b border-gray-200 z-40 hidden sm:block"></div>
        
        <div className="bg-transparent text-gray-900 flex flex-col items-center w-full mt-0 sm:mt-2 relative fade-in sm:pt-[70px]">
          <div className="flex w-full px-0 sm:px-4 lg:px-4 xl:px-8 pt-0 sm:pt-2 max-w-[1600px]">
          <LeftSidebar />
          <div className="flex-1 flex justify-center min-w-0 px-0 sm:px-4 lg:px-8 gap-6">
            <main className="w-full max-w-[720px] bg-transparent relative">
              <PostDetailPage postId={viewingPostId} onBack={() => setViewingPostId(null)} />
            </main>
            <RightSidebar />
          </div>
        </div>
      </div>
      </>
    );
  }

  return (
    <div className="flex-1 bg-slate-50 flex flex-col min-h-screen relative pb-20 lg:pb-8">
      {/* Common Header / Cover */}
      <div className="transition-all block">
        <div 
          className="h-48 sm:h-64 w-full relative transition-colors duration-500" 
          style={{ backgroundColor: profile.cover_color || "#3b82f6" }}
        >
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
          <div className="absolute bottom-4 right-4 flex justify-end">
            <div className="relative">
              <button 
                onClick={() => setShowColorPicker(!showColorPicker)}
                className="flex items-center gap-2 bg-white/20 backdrop-blur-md hover:bg-white/30 text-white px-3 py-1.5 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-medium transition-all"
              >
                <Edit3 className="w-4 h-4" />
                <span className="hidden sm:inline">Change Cover</span>
                <span className="sm:hidden">Edit</span>
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

        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Profile Info & Avatar */}
          <div className="relative mb-4 sm:mb-8 flex flex-col sm:flex-row gap-3 sm:gap-6">
            <div className="shrink-0 w-24 sm:w-40 mx-auto sm:mx-0">
              <div className="relative -mt-12 sm:-mt-24 group">
                <div className="w-24 h-24 sm:w-40 sm:h-40 rounded-full border-4 border-white shadow-xl overflow-hidden bg-white">
                  {profile.avatar_url ? (
                    <img src={profile.avatar_url} alt={user.username} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-blue-100 to-indigo-50 flex items-center justify-center text-blue-500 text-4xl sm:text-5xl font-bold">
                      {user.username.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>
                <button 
                  onClick={() => setShowAvatarMenu(!showAvatarMenu)}
                  className="absolute bottom-1 right-1 sm:bottom-2 sm:right-2 bg-slate-800 text-white p-1.5 sm:p-2 rounded-full shadow-lg hover:bg-slate-700 transition-colors"
                >
                  <Camera className="w-4 h-4 sm:w-5 sm:h-5" />
                </button>
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
            
            <div className="flex-1 text-center sm:text-left mt-1 sm:mt-4">
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900">
                {(profile.first_name && (profile.display_full_name !== false)) 
                  ? `${profile.first_name} ${profile.last_name}` 
                  : user.username}
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 flex items-center justify-center sm:justify-start gap-1.5 mt-1">
                <Calendar className="w-3.5 h-3.5" /> Joined {joinedDate}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl w-full mx-auto px-0 sm:px-6 lg:px-8 pb-12 flex-1 pt-2 sm:pt-4">
        
        {/* DESKTOP LAYOUT */}
        <div className="hidden lg:grid lg:grid-cols-3 gap-8">
          {/* Left Column: Details & Metrics */}
          <div className="lg:col-span-1">
            <div ref={sidebarRef} className="sticky" style={{ top: sidebarTop, transition: 'top 0.2s ease-out' }}>
              {renderStats()}
            </div>
          </div>

          {/* Right Column: Tabs */}
          <div className="lg:col-span-2 space-y-6">
            {/* Desktop Tabs Navigation */}
            <Tabs<"posts" | "reports" | "settings">
              tabs={[
                { id: "posts", label: "Community Posts", icon: MessageSquare },
                { id: "reports", label: "Hazard Reports", icon: AlertTriangle },
                { id: "settings", label: "Settings", icon: Settings },
              ]}
              activeTab={activeTab === "stats" ? "posts" : activeTab}
              onChange={(tab) => handleTabChange(tab)}
              variant="underline"
              layoutId="profile-desktop-tab-indicator"
              fullWidth
              className="mb-6"
            />

            {/* Tab Content */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 min-h-[400px] overflow-hidden">
              <TabContentPanel tabKey={activeTab} direction={tabDirection}>
                {activeTab === "stats" && (
                  <div className="p-6 text-center text-slate-500">
                    Stats are visible in the left sidebar on large screens.
                  </div>
                )}
                {activeTab === "reports" && renderReports()}
                {activeTab === "posts" && renderPosts()}
                {activeTab === "settings" && renderSettings()}
              </TabContentPanel>
            </div>
          </div>
        </div>

        {/* MOBILE LAYOUT */}
        <div className="block lg:hidden w-full px-4 sm:px-0">
          
          {/* Mobile Horizontal Tabs Navigation */}
          <Tabs<"stats" | "posts" | "reports" | "settings">
            tabs={[
              { id: "stats", label: "Stats", icon: ShieldCheck, hideLabelOnMobile: true },
              { id: "posts", label: "Posts", icon: MessageSquare, hideLabelOnMobile: true },
              { id: "reports", label: "Reports", icon: AlertTriangle, hideLabelOnMobile: true },
              { id: "settings", label: "Settings", icon: Settings, hideLabelOnMobile: true },
            ]}
            activeTab={activeTab}
            onChange={(tab) => handleTabChange(tab)}
            variant="underline"
            layoutId="profile-mobile-tab-indicator"
            fullWidth
            className="mb-4 w-full"
          />

          {/* Mobile Tab Content */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 min-h-[50vh] p-4 sm:p-6 pb-[calc(1.5rem+env(safe-area-inset-bottom))] overflow-hidden">
            <TabContentPanel tabKey={activeTab} direction={tabDirection}>
              {activeTab === "stats" && (
                <div className="mt-2">
                  <h3 className="text-base font-bold text-slate-900 mb-6 px-2">My Overview</h3>
                  <div>
                    {renderStats()}
                  </div>
                </div>
              )}
              {activeTab === "reports" && (
                <div className="mt-2">
                  <h3 className="text-base font-bold text-slate-900 mb-4 px-2">Hazard Reports</h3>
                  {renderReports()}
                </div>
              )}
              {activeTab === "posts" && (
                <div className="mt-2">
                  <h3 className="text-base font-bold text-slate-900 mb-4 px-2">Community Posts</h3>
                  {renderPosts()}
                </div>
              )}
              {activeTab === "settings" && (
                <div className="mt-2">
                  <h3 className="text-base font-bold text-slate-900 mb-4 px-2">Account Settings</h3>
                  {renderSettings()}
                </div>
              )}
            </TabContentPanel>
          </div>
        </div>
      </div>

      {/* Logout Confirmation Modal */}
      <AnimatePresence>
        {showLogoutConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="bg-white rounded-3xl shadow-xl w-full max-w-sm overflow-hidden border border-slate-100"
            >
              <div className="p-6 text-center">
                <div className="w-14 h-14 rounded-full bg-red-50 text-red-500 flex items-center justify-center mx-auto mb-4">
                  <LogOut className="w-7 h-7" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Log Out</h3>
                <p className="text-sm text-slate-500 mb-6 leading-relaxed">
                  Are you sure you want to log out of your account? You will need to log back in to report hazards or interact with the community.
                </p>
                <div className="flex gap-3 mt-2">
                  <Button 
                    variant="secondary"
                    onClick={() => setShowLogoutConfirm(false)}
                    className="flex-1 bg-slate-100 hover:bg-slate-200 border-0"
                  >
                    Cancel
                  </Button>
                  <Button 
                    variant="danger"
                    onClick={() => {
                      setShowLogoutConfirm(false);
                      logout();
                    }}
                    className="flex-1 shadow-sm shadow-red-200"
                  >
                    Yes, Log Out
                  </Button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
