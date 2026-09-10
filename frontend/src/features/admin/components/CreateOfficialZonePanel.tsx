"use client";

import React from "react";
import { OfficialZoneDrawer, type OfficialZoneDrawerProps } from "./zones";
import type { AvoidanceZone } from "../adminApi";

export interface CreateOfficialZonePanelProps {
  isOpen: boolean;
  onClose: () => void;
  isAdminMode?: boolean;
  onAdminSubmit?: (payloads: any) => Promise<void>;
  mapInstance?: any;
  editingZone?: AvoidanceZone | null;
  onZoneUpdated?: () => void;
}

export function CreateOfficialZonePanel({
  isOpen,
  onClose,
  mapInstance,
  editingZone,
  onAdminSubmit,
  onZoneUpdated,
}: CreateOfficialZonePanelProps) {
  return (
    <OfficialZoneDrawer
      isOpen={isOpen}
      onClose={onClose}
      mapInstance={mapInstance}
      editingZone={editingZone}
      onAdminSubmit={onAdminSubmit}
      onZoneUpdated={onZoneUpdated}
    />
  );
}

export default CreateOfficialZonePanel;
