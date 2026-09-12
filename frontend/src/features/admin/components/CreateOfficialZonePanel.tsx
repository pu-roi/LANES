"use client";

import React from "react";
import { OfficialZoneDrawer, type ZoneSubmissionItem } from "./zones";
import type { AvoidanceZone } from "../adminApi";

export interface CreateOfficialZonePanelProps {
  isOpen: boolean;
  onClose: () => void;
  isAdminMode?: boolean;
  onAdminSubmit?: (items: ZoneSubmissionItem[]) => Promise<void>;
  mapInstance?: any;
  editingZone?: AvoidanceZone | null;
  onZoneUpdated?: () => void;
  onSwitchWorkspace?: () => void;
  switchWorkspaceLabel?: string;
}

export function CreateOfficialZonePanel({
  isOpen,
  onClose,
  mapInstance,
  editingZone,
  onAdminSubmit,
  onZoneUpdated,
  onSwitchWorkspace,
  switchWorkspaceLabel,
}: CreateOfficialZonePanelProps) {
  return (
    <OfficialZoneDrawer
      isOpen={isOpen}
      onClose={onClose}
      mapInstance={mapInstance}
      editingZone={editingZone}
      onAdminSubmit={onAdminSubmit}
      onZoneUpdated={onZoneUpdated}
      onSwitchWorkspace={onSwitchWorkspace}
      switchWorkspaceLabel={switchWorkspaceLabel}
    />
  );
}

export default CreateOfficialZonePanel;
