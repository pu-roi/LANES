"use client";

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings, SystemSettings } from '@/features/admin/adminApi';
import toast from 'react-hot-toast';
import { Save, Settings2, Sliders, ShieldAlert, Clock, AlertTriangle } from 'lucide-react';
import { NumberInput } from '@/shared/ui';

export default function SystemSettingsPage() {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<SystemSettings>({});

  const { data: settings, isLoading, isError } = useQuery({
    queryKey: ['systemSettings'],
    queryFn: getSettings,
  });

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: (newSettings) => {
      queryClient.setQueryData(['systemSettings'], newSettings);
      toast.success('System settings saved successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to update system settings');
    }
  });

  const handleChange = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center gap-3">
        <AlertTriangle className="w-5 h-5" />
        <p>Failed to load system settings. Ensure you have the proper permissions.</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-8 pb-12">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">System Settings</h1>
        <p className="text-gray-500 mt-1">Configure global platform behavior and automated thresholds.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* NLP Settings */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-100 bg-gray-50/50 p-5 flex items-center gap-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Sliders className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">NLP Confidence Thresholds</h3>
              <p className="text-xs text-gray-500">Determine how strict the system is when automatically parsing social media data.</p>
            </div>
          </div>
          <div className="p-6 space-y-6">
            
            {/* Min Location Confidence */}
            <div>
              <div className="flex justify-between items-end mb-2">
                <label className="block text-sm font-semibold text-gray-700">Minimum Location Confidence</label>
                <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-md">
                  {formData.min_location_confidence ?? 0.6}
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-3">Reports below this confidence will require manual verification or will be discarded.</p>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={formData.min_location_confidence ?? 0.6}
                onChange={(e) => handleChange('min_location_confidence', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0.1 (Lenient)</span>
                <span>1.0 (Strict)</span>
              </div>
            </div>

            <hr className="border-gray-100" />

            {/* Min Severity Confidence */}
            <div>
              <div className="flex justify-between items-end mb-2">
                <label className="block text-sm font-semibold text-gray-700">Minimum Severity Confidence</label>
                <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-1 rounded-md">
                  {formData.min_severity_confidence ?? 0.5}
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-3">The confidence required to automatically categorize a report's flood severity level.</p>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={formData.min_severity_confidence ?? 0.5}
                onChange={(e) => handleChange('min_severity_confidence', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0.1 (Lenient)</span>
                <span>1.0 (Strict)</span>
              </div>
            </div>

          </div>
        </div>

        {/* Operational Settings */}
        <div className="space-y-8">
          
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="border-b border-gray-100 bg-gray-50/50 p-5 flex items-center gap-3">
              <div className="bg-emerald-100 p-2 rounded-lg">
                <Clock className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Flood Zone Configuration</h3>
                <p className="text-xs text-gray-500">Manage rules for active avoidance zones.</p>
              </div>
            </div>
            <div className="p-6 space-y-6">
              
              {/* Expiry Hours */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Zone Expiry (Hours)</label>
                <p className="text-xs text-gray-500 mb-3">Automatically deactivate flood zones after this many hours of no new reports.</p>
                <div className="w-48">
                  <NumberInput
                    min={1}
                    max={168}
                    value={formData.flood_zone_expiry_hours ?? 24}
                    onChange={(e) => handleChange('flood_zone_expiry_hours', parseInt(e.target.value))}
                    rightAddon="hours"
                  />
                </div>
              </div>

              <hr className="border-gray-100" />

              {/* Auto Approve */}
              <div>
                <div className="flex justify-between items-end mb-2">
                  <label className="block text-sm font-semibold text-gray-700">Auto-Approve Threshold</label>
                  <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">
                    {formData.auto_approve_threshold ?? 0.9}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-3">Reports exceeding this total confidence score skip manual verification.</p>
                <input
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.05"
                  value={formData.auto_approve_threshold ?? 0.9}
                  onChange={(e) => handleChange('auto_approve_threshold', parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>0.5 (Frequent auto-approvals)</span>
                  <span>1.0 (Strictly manual)</span>
                </div>
              </div>

            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="border-b border-gray-100 bg-gray-50/50 p-5 flex items-center gap-3">
              <div className="bg-purple-100 p-2 rounded-lg">
                <ShieldAlert className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Sub-Admin Restrictions</h3>
                <p className="text-xs text-gray-500">Configure what lower-level administrators can do.</p>
              </div>
            </div>
            <div className="p-6">
              <p className="text-sm text-gray-600 mb-4">
                Sub-admin restrictions are now managed via the robust Role-Based Access Control (RBAC) system. 
                Please navigate to the Roles page to define specific permissions for different administrator tiers.
              </p>
              <a href="/admin/roles" className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                Manage Roles
              </a>
            </div>
          </div>

        </div>
      </div>

      <div className="flex justify-end pt-4 border-t border-gray-200">
        <button
          onClick={handleSave}
          disabled={updateMutation.isPending}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 shadow-sm"
        >
          {updateMutation.isPending ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <Save className="w-4 h-4" />
          )}
          {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

    </div>
  );
}
