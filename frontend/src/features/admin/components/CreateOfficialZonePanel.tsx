"use client";

import React from "react";
import { OfficialZoneDrawer, type ZoneSubmissionItem } from "./zones";
import type { AvoidanceZone } from "../adminApi";
import type { ZoneEditorProposal } from "@/features/hazards/zoneUpdatesApi";

export interface CreateOfficialZonePanelProps {
  isOpen: boolean;
  onClose: () => void;
  isAdminMode?: boolean;
  onAdminSubmit?: (items: ZoneSubmissionItem[]) => Promise<void>;
  mapInstance?: any;
  editingZone?: AvoidanceZone | null;
  communityProposal?: ZoneEditorProposal | null;
  onZoneUpdated?: () => void;
  onSwitchWorkspace?: () => void;
  switchWorkspaceLabel?: string;
  onShowMap?: () => void;
  onReturnToZones?: () => void;
}

export function CreateOfficialZonePanel({
  isOpen,
  onClose,
  mapInstance,
  editingZone,
  communityProposal,
  onAdminSubmit,
  onZoneUpdated,
  onSwitchWorkspace,
  switchWorkspaceLabel,
  onShowMap,
  onReturnToZones,
}: CreateOfficialZonePanelProps) {
  return (
    <OfficialZoneDrawer
      isOpen={isOpen}
      onClose={onClose}
      mapInstance={mapInstance}
      editingZone={editingZone}
      communityProposal={communityProposal}
      onAdminSubmit={onAdminSubmit}
      onZoneUpdated={onZoneUpdated}
      onSwitchWorkspace={onSwitchWorkspace}
      switchWorkspaceLabel={switchWorkspaceLabel}
      onShowMap={onShowMap}
      onReturnToZones={onReturnToZones}
    />
  );
}

export default CreateOfficialZonePanel;
