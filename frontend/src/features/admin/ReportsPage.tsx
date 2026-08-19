"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  getReports, 
  approveReport, 
  rejectReport, 
  FloodReport,
  ReportGeometry
} from "./adminApi";
import { useToast, Button, Input, Select, Pagination, Tabs, MediaViewer, MultiSelect, DatePicker } from "@/shared/ui";
import { ReportDetailsModal } from "./components/ReportDetailsModal";
import { 
  Loader2, 
  CheckCircle, 
  XCircle, 
  MapPin, 
  Search, 
  Filter, 
  ChevronLeft, 
  ChevronRight,
  TrendingDown,
  TrendingUp,
  AlertOctagon,
  RefreshCw,
  Eye,
  Map as MapIcon,
  X
} from "lucide-react";

const LIMIT = 8;

export default function ReportsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>("all");
  const [severity, setSeverity] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("newest");
  const [timeRange, setTimeRange] = useState("all");
  const [customDateFrom, setCustomDateFrom] = useState("");
  const [customDateTo, setCustomDateTo] = useState("");
  const [selectedRegions, setSelectedRegions] = useState<(string | number)[]>([]);
  const [selectedCities, setSelectedCities] = useState<(string | number)[]>([]);
  const [selectedBarangays, setSelectedBarangays] = useState<(string | number)[]>([]);

  // 1. Fetch Regions
  const { data: regionsData } = useQuery({
    queryKey: ["psgc-regions"],
    queryFn: async () => {
      const res = await fetch("https://psgc.gitlab.io/api/regions/");
      if (!res.ok) return [];
      return res.json();
    },
    staleTime: Infinity, // PSGC data rarely changes
  });
  
  const regionOptions = (regionsData || [])
    .map((r: any) => ({ label: r.name, value: r.code, isPinned: r.code === "130000000" }))
    .sort((a: any, b: any) => {
      if (a.value === "130000000") return -1;
      if (b.value === "130000000") return 1;
      return a.label.localeCompare(b.label);
    });

  // 2. Fetch Cities for selected regions
  const { data: citiesData } = useQuery({
    queryKey: ["psgc-cities", selectedRegions],
    queryFn: async () => {
      if (selectedRegions.length === 0) return [];
      const promises = selectedRegions.map(code => 
        fetch(`https://psgc.gitlab.io/api/regions/${code}/cities-municipalities/`).then(res => res.ok ? res.json() : [])
      );
      const results = await Promise.all(promises);
      return results.flat();
    },
    enabled: selectedRegions.length > 0,
    staleTime: Infinity,
  });
  
  const cityOptions = (citiesData || [])
    .map((c: any) => ({ label: c.name, value: c.code, isPinned: c.code === "137403000" }))
    .sort((a: any, b: any) => {
      if (a.value === "137403000") return -1;
      if (b.value === "137403000") return 1;
      return a.label.localeCompare(b.label);
    });

  // 3. Fetch Barangays for selected cities
  const { data: barangaysData } = useQuery({
    queryKey: ["psgc-barangays", selectedCities],
    queryFn: async () => {
      if (selectedCities.length === 0) return [];
      const promises = selectedCities.map(code => 
        fetch(`https://psgc.gitlab.io/api/cities-municipalities/${code}/barangays/`).then(res => res.ok ? res.json() : [])
      );
      const results = await Promise.all(promises);
      return results.flat();
    },
    enabled: selectedCities.length > 0,
    staleTime: Infinity,
  });
  
  const barangayOptions = (barangaysData || [])
    .map((b: any) => ({ label: b.name, value: b.code }))
    .sort((a: any, b: any) => a.label.localeCompare(b.label));

  const handleRegionChange = (values: (string | number)[]) => {
    setSelectedRegions(values);
    // Clearing a region means we must filter out selected cities that belong to removed regions
    // We can just clear the city/barangay selection if a region is deselected to keep it simple, 
    // or wait for the new citiesData to arrive. Resetting is safest:
    setSelectedCities([]);
    setSelectedBarangays([]);
  };

  const handleCityChange = (values: (string | number)[]) => {
    setSelectedCities(values);
    setSelectedBarangays([]);
  };

  const [selectedMedia, setSelectedMedia] = useState<{ urls: string[], index: number } | null>(null);
  const [selectedReport, setSelectedReport] = useState<FloodReport | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);

  const getDateRange = () => {
    const now = new Date();
    let from: string | undefined = undefined;
    let to: string | undefined = undefined;
    switch (timeRange) {
      case "today":
        from = new Date(now.setHours(0, 0, 0, 0)).toISOString();
        break;
      case "last7days":
        from = new Date(now.setDate(now.getDate() - 7)).toISOString();
        break;
      case "last30days":
        from = new Date(now.setDate(now.getDate() - 30)).toISOString();
        break;
      case "thisYear":
        from = new Date(now.getFullYear(), 0, 1).toISOString();
        break;
      case "custom":
        from = customDateFrom ? new Date(customDateFrom).toISOString() : undefined;
        to = customDateTo ? new Date(`${customDateTo}T23:59:59.999Z`).toISOString() : undefined;
        break;
    }
    return { from, to };
  };

  const { from: computedDateFrom, to: computedDateTo } = getDateRange();

  /**
   * Returns a human-readable coordinate label for a report geometry.
   * Points show the exact lat/lng; LineStrings show the midpoint prefixed with "~".
   */
  const getGeometryLabel = (geometry: ReportGeometry): string => {
    if (geometry.type === "Point") {
      const [lng, lat] = geometry.coordinates;
      return `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    }
    // LineString — use the midpoint coordinate as a representative location
    const mid = geometry.coordinates[Math.floor(geometry.coordinates.length / 2)];
    return `~${mid[1].toFixed(5)}, ${mid[0].toFixed(5)}`;
  };

  // Convert selected barangay PSGC codes back to their names for the backend
  const computedBarangaysToFetch = selectedBarangays.length > 0 
    ? selectedBarangays.map(code => barangayOptions.find(o => o.value === code)?.label).filter(Boolean) as string[]
    : selectedCities.length > 0 
      ? barangayOptions.map(o => o.label)
      : [];

  const { data, isLoading, isPlaceholderData, refetch } = useQuery({
    queryKey: ["adminReports", page, status, severity, search, sortBy, timeRange, customDateFrom, customDateTo, computedBarangaysToFetch],
    queryFn: () => getReports({ 
      page, limit: LIMIT, status, severity, search, sortBy,
      date_from: computedDateFrom,
      date_to: computedDateTo,
      barangays: computedBarangaysToFetch as string[]
    }),
    placeholderData: (prev) => prev,
    refetchInterval: 15000, // 15s background polling fallback
  });

  // Auto-open modal if report_id is provided in URL search parameters
  useEffect(() => {
    const reportIdParam = searchParams.get("report_id");
    if (reportIdParam && data?.reports) {
      const target = data.reports.find((r) => r.id === Number(reportIdParam));
      if (target) {
        setSelectedReport(target);
        setIsDetailsModalOpen(true);
      }
    }
  }, [searchParams, data?.reports]);

  const approveMutation = useMutation({
    mutationFn: (id: number) => approveReport(id),
    onSuccess: () => {
      success("Report approved successfully");
      queryClient.invalidateQueries({ queryKey: ["adminReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setIsDetailsModalOpen(false);
    },
    onError: (err: any) => {
      error("Approval Failed", err.message || "Failed to approve report");
    }
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => rejectReport(id),
    onSuccess: () => {
      success("Report rejected");
      queryClient.invalidateQueries({ queryKey: ["adminReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setIsDetailsModalOpen(false);
    },
    onError: (err: any) => {
      error("Rejection Failed", err.message || "Failed to reject report");
    }
  });

  const handleViewOnMap = (report: FloodReport) => {
    router.push(`/admin/map?focus_report_id=${report.id}`);
  };

  const handleOpenDetails = (report: FloodReport) => {
    setSelectedReport(report);
    setIsDetailsModalOpen(true);
  };

  const handleTabChange = (newStatus: string) => {
    setStatus(newStatus);
    setPage(1);
  };

  const handleSeverityChange = (newSeverity: string) => {
    setSeverity(newSeverity);
    setPage(1);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleSortChange = (newSort: string) => {
    setSortBy(newSort);
    setPage(1);
  };

  const reports = data?.reports || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / LIMIT);

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "low":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-200">
            Passable (White)
          </span>
        );
      case "medium":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-200">
            Warning (Yellow)
          </span>
        );
      case "high":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-800 border border-orange-200">
            Hazardous (Orange)
          </span>
        );
      case "extreme":
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200 animate-pulse">
            Impassable (Red)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-800 border border-gray-200">
            Unknown
          </span>
        );
    }
  };

  const getStatusBadge = (stat: string) => {
    switch (stat) {
      case "pending":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            Pending
          </span>
        );
      case "approved":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
            Approved
          </span>
        );
      case "rejected":
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-800">
            Rejected
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Flood Reports Moderation</h1>
          <p className="text-gray-500 text-sm mt-1">
            Moderate, filter, and search all ingested Taglish news feeds and citizen flood alerts.
          </p>
        </div>
        <Button 
          onClick={() => refetch()} 
          variant="outline" 
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Feed
        </Button>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: "all", label: "All Reports" },
          { id: "pending", label: "Pending" },
          { id: "approved", label: "Approved" },
          { id: "rejected", label: "Rejected" },
        ]}
        activeTab={status}
        onChange={handleTabChange}
        variant="underline"
        layoutId="admin-reports-tab-indicator"
      />

      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        {/* Search */}
        <Input
          containerClassName="w-full sm:max-w-xs"
          leftIcon={<Search className="w-4 h-4 text-gray-400" />}
          type="text"
          placeholder="Search report feeds..."
          value={search}
          onChange={handleSearchChange}
        />

        {/* Filters */}
        <div className="flex w-full sm:w-auto items-center gap-3 justify-end">
          {/* Severity Dropdown */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400 hidden md:block" />
            <Select
              value={severity}
              onChange={(e) => handleSeverityChange(String(e.target.value))}
              className="w-48"
              options={[
                { label: "All Severities", value: "all" },
                { label: "Passable (White)", value: "low" },
                { label: "Warning (Yellow)", value: "medium" },
                { label: "Hazardous (Orange)", value: "high" },
                { label: "Impassable (Red)", value: "extreme" }
              ]}
            />
          </div>

          {/* Location Filters */}
          <div className="flex items-center gap-2">
            <MultiSelect
              value={selectedRegions}
              onChange={handleRegionChange}
              options={regionOptions}
              placeholder="Region"
              className="w-40"
            />
            <MultiSelect
              value={selectedCities}
              onChange={handleCityChange}
              options={cityOptions}
              placeholder="City"
              className="w-40"
              disabled={selectedRegions.length === 0}
            />
            <MultiSelect
              value={selectedBarangays}
              onChange={setSelectedBarangays}
              options={barangayOptions}
              placeholder="Barangay"
              className="w-40"
              disabled={selectedCities.length === 0}
            />
          </div>

          {/* Time Range Filter */}
          <div className="flex items-center gap-2">
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(String(e.target.value))}
              className="w-40"
              options={[
                { label: "All Time", value: "all" },
                { label: "Today", value: "today" },
                { label: "Last 7 Days", value: "last7days" },
                { label: "Last 30 Days", value: "last30days" },
                { label: "This Year", value: "thisYear" },
                { label: "Custom...", value: "custom" }
              ]}
            />
          </div>
          
          {/* Custom Date Pickers */}
          {timeRange === "custom" && (
            <div className="flex items-center gap-2">
              <DatePicker 
                value={customDateFrom} 
                onChange={(e) => setCustomDateFrom(e.target.value)} 
                className="w-32"
              />
              <span className="text-sm text-gray-500">to</span>
              <DatePicker 
                value={customDateTo} 
                onChange={(e) => setCustomDateTo(e.target.value)} 
                className="w-32"
              />
            </div>
          )}

          {/* Sort Toggles */}
          <div className="border-l border-gray-200 pl-3 flex gap-1">
            <button
              onClick={() => handleSortChange("newest")}
              className={`p-2 rounded-lg transition-colors ${
                sortBy === "newest"
                  ? "bg-gray-100 text-gray-800"
                  : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"
              }`}
              title="Sort Newest First"
            >
              <TrendingDown className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleSortChange("oldest")}
              className={`p-2 rounded-lg transition-colors ${
                sortBy === "oldest"
                  ? "bg-gray-100 text-gray-800"
                  : "text-gray-400 hover:text-gray-600 hover:bg-gray-50"
              }`}
              title="Sort Oldest First"
            >
              <TrendingUp className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Reports Grid */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-xl shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
          <p className="text-sm text-gray-500">Loading reports...</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center shadow-sm">
          <AlertOctagon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900">No reports found</h3>
          <p className="text-gray-500 mt-1 max-w-sm mx-auto text-sm">
            Try adjusting your search query, status tabs, or severity filter levels.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {reports.map((report: FloodReport) => (
            <div 
              key={report.id} 
              onClick={() => handleOpenDetails(report)}
              className={`bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col md:flex-row transition-all duration-150 cursor-pointer hover:border-blue-300 hover:shadow-md ${
                isPlaceholderData ? "opacity-60" : "opacity-100"
              }`}
            >
              <div className="p-6 flex-1 flex flex-col sm:flex-row gap-6">
                {/* Optional Image Thumbnail */}
                {report.media_urls && report.media_urls.length > 0 && (
                  <div 
                    className="shrink-0 flex items-center justify-center bg-gray-50 rounded-lg overflow-hidden border border-gray-200 cursor-pointer hover:opacity-90 transition-opacity relative"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (report.media_urls) {
                        setSelectedMedia({ urls: report.media_urls, index: 0 });
                      }
                    }}
                  >
                    {report.media_urls[0].match(/\.(mp4|webm|mov|ogg)$/i) || report.media_urls[0].includes('/video/upload/') ? (
                      <video src={report.media_urls[0]} className="w-full sm:w-32 h-32 object-cover" />
                    ) : (
                      <img 
                        src={report.media_urls[0]} 
                        alt="Flood evidence" 
                        className="w-full sm:w-32 h-32 object-cover"
                      />
                    )}
                    {report.media_urls.length > 1 && (
                      <div className="absolute top-2 right-2 bg-black/60 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-md backdrop-blur-md">
                        +{report.media_urls.length - 1}
                      </div>
                    )}
                  </div>
                )}
                
                <div className="flex-1 space-y-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-gray-900">Report #{report.id}</span>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-200 uppercase tracking-wider">
                          {report.source}
                        </span>
                        {getStatusBadge(report.status)}
                      </div>
                      <span className="text-xs text-gray-400 font-medium">
                        {new Date(report.created_at).toLocaleString()}
                      </span>
                    </div>
                    
                    <p className="text-gray-900 font-medium text-sm leading-relaxed">
                      "{report.raw_text}"
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 pt-2">
                    {getSeverityBadge(report.severity)}
                    {report.depth && (
                      <div className="flex items-center text-xs font-medium text-gray-700 bg-gray-100 border border-gray-200 px-2.5 py-1 rounded-full">
                        Depth: {report.depth.replace(/_/g, ' ')}
                      </div>
                    )}
                    {report.geometry ? (
                      <div className="flex items-center text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-100 px-2.5 py-1 rounded-full">
                        <MapPin className="w-3.5 h-3.5 mr-1" />
                        {getGeometryLabel(report.geometry)}
                      </div>
                    ) : (
                      <div className="flex items-center text-xs font-medium text-gray-500 bg-gray-50 border border-gray-100 px-2.5 py-1 rounded-full">
                        No coordinates mapped
                      </div>
                    )}
                    {report.reporter_name && (
                      <div className="text-xs text-gray-500 font-medium">
                        By <span className="font-semibold text-gray-800">{report.reporter_name}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Column */}
              <div className="bg-gray-50/70 border-t md:border-t-0 md:border-l border-gray-200 p-5 flex flex-row md:flex-col items-center justify-center gap-2.5 md:w-52">
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewOnMap(report);
                  }}
                  variant="outline"
                  className="w-full flex items-center justify-center gap-1.5 text-blue-600 border-blue-200 hover:bg-blue-50 text-xs font-semibold py-2"
                >
                  <MapIcon className="w-3.5 h-3.5" />
                  View on Map
                </Button>

                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpenDetails(report);
                  }}
                  variant="outline"
                  className="w-full flex items-center justify-center gap-1.5 text-gray-700 border-gray-300 hover:bg-gray-100 text-xs font-semibold py-2"
                >
                  <Eye className="w-3.5 h-3.5" />
                  Details
                </Button>

                {report.status === "pending" && (
                  <div className="w-full flex gap-2 pt-1 border-t border-gray-200">
                    <Button 
                      onClick={(e) => {
                        e.stopPropagation();
                        approveMutation.mutate(report.id);
                      }}
                      disabled={approveMutation.isPending}
                      className="flex-1 flex items-center justify-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-xs font-semibold py-1.5 px-2"
                    >
                      {approveMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                      Approve
                    </Button>
                    <Button 
                      onClick={(e) => {
                        e.stopPropagation();
                        rejectMutation.mutate(report.id);
                      }}
                      disabled={rejectMutation.isPending}
                      variant="outline"
                      className="flex-1 flex items-center justify-center gap-1 text-rose-600 border-rose-200 hover:bg-rose-50 text-xs font-semibold py-1.5 px-2"
                    >
                      {rejectMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
                      Reject
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <Pagination 
        page={page} 
        totalPages={totalPages} 
        onPageChange={setPage} 
      />

      {/* Rich Report Details Modal */}
      <ReportDetailsModal
        report={selectedReport}
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        onViewOnMap={handleViewOnMap}
        onApprove={(id) => approveMutation.mutate(id)}
        onReject={(id) => rejectMutation.mutate(id)}
        isApproveLoading={approveMutation.isPending}
        isRejectLoading={rejectMutation.isPending}
        onOpenMedia={(urls, idx) => setSelectedMedia({ urls, index: idx })}
      />

      {/* Lightbox Modal */}
      <MediaViewer 
        mediaUrls={selectedMedia ? selectedMedia.urls : []}
        initialIndex={selectedMedia ? selectedMedia.index : 0}
        isOpen={!!selectedMedia}
        onClose={() => setSelectedMedia(null)}
      />
    </div>
  );
}
