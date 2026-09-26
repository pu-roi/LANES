# **LANES Flood Depth & Vehicle Passability Implementation Review**

**Document Version:** 1.1 (Unified Routing Policy)
**System Scope:** Frontend Routing Panel, Citizen Flood Reporting, PostGIS Spatial Zones, and Valhalla / ORS Routing Engines  
**Target Codebase:** LANES Metro Manila Flood-Aware Navigation Platform  
**Last Updated:** September 17, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

---

## 1. Executive Summary

This document provides a technical audit and operational reference detailing how **flood depths**, **vehicle profiles**, and **passability rules** are integrated across the LANES system. 

It explicitly resolves the question of **which vehicles can pass each flood depth level**, bridging the gap between:
1. **Public MMDA Flood Gauge Standards** (Gutter, Half-Knee, Half-Tire, Knee, Tires, Waist, Chest, Neck & Above).
2. **Citizen Flood Reporting Survey Options** ([`FloodReportPanel.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx)).
3. **The Active Backend Routing Policy** ([`flood_routing_policy.py`](file:///d:/Documents/Github/LANES/backend/app/services/flood_routing_policy.py)), shared by the Valhalla and ORS provider adapters.

---

## 2. The 8 MMDA Flood Depth Levels & LANES Severity Mapping

The Metropolitan Manila Development Authority (MMDA) monitors urban floods using body-relative and tire-relative flood gauge benchmarks. LANES translates these 8 real-world visual observations into 4 computational severity categories in PostGIS:

| MMDA Terminology | Gauge Depth (Inches) | Metric Depth (cm / m) | LANES Severity Zone | Visual Color Code | Official MMDA Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gutter** | 8" | 20.32 cm (0.20m) | **`low`** | 🟩 Lime / Yellow-Green | **PATV** (Passable to All Types of Vehicles) |
| **Half-Knee** | 10" | 25.40 cm (0.25m) | **`low`** | 🟩 Lime / Yellow-Green | **PATV** (Passable to All Types of Vehicles) |
| **Half-Tire** | 13" | 33.02 cm (0.33m) | **`medium`** | 🟨 Amber / Yellow | **NPLV** (Not Passable to Light Vehicles) |
| **Knee** | 19" | 48.26 cm (0.48m) | **`medium`** | 🟨 Amber / Yellow | **NPLV** (Not Passable to Light Vehicles) |
| **Tires** | 26" | 66.04 cm (0.66m) | **`high`** | 🟧 Orange | **NPATV** (Not Passable to All Types of Vehicles) |
| **Waist** | 37" | 93.98 cm (0.94m) | **`high`** | 🟧 Orange | **NPATV** (Not Passable to All Types of Vehicles) |
| **Chest** | 45" | 114.30 cm (1.14m) | **`high`** | 🟧 Orange | **NPATV** (Not Passable to All Types of Vehicles) |
| **Neck & Above** | >45" | >114.30 cm (>1.14m)| **`extreme`** | 🟥 Deep Red | **NPATV** (Critical Hazard / Emergency Only) |

---

## 3. Vehicle Profile Definitions Across the System

### A. Routing Planner UI ([`RoutePanel.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/routing/RoutePanel.tsx#L172-L177))
The navigation planner exposes 4 selectable vehicle profiles to the end user:
- **🚚 High Cl. (`heavy`):** SUVs, Pickups, Vans, 4x4s, and Light Commercial Trucks (water wading limit ~700mm–800mm).
- **🚗 Low Cl. (`light`):** Sedans, Hatchbacks, Compact Coupes, and City Cars (ground clearance ~130mm–160mm).
- **🏍️ Moto (`motorcycle`):** Commuter Scooters, Underbones, and Motorcycles (air intake & exhaust ~250mm–300mm).
- **🚶 Walk (`walk`):** Pedestrians, Commuters on foot, and Emergency Evacuees.

### B. Citizen Survey Checklist ([`FloodReportPanel.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx#L960-L967))
When citizens submit flood hazard reports, they can confirm vehicle safety through 6 community survey checkboxes:
1. `Pedestrians`
2. `Bicycles / E-Bikes`
3. `Motorcycles`
4. `Sedans / Hatchbacks`
5. `SUVs / Pickups`
6. `Large Trucks / Buses`

---

## 4. Master Passability & Routing Decision Table

The table below explains how the shared backend policy ([`flood_routing_policy.py`](file:///d:/Documents/Github/LANES/backend/app/services/flood_routing_policy.py)) evaluates every provider candidate for each profile. Safety scores are deterministic indicators, not probabilities.

An official passable-vehicle list can make a listed vehicle profile more restrictive, but a vehicle-only survey list does not silently prohibit Walking. Walking is restricted only by an explicit pedestrian/walking prohibition.

| Flood Level | Depth | Pedestrian (`walk`) | Motorcycle (`motorcycle`) | Low Clearance Sedan (`light`) | High Clearance SUV (`heavy`) | Engineering / Biological Justification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Gutter** | 8" (0.20m) | **Passable** (100%) | **Passable** (100%) | **Passable** (100%) | **Passable** (100%) | Water does not exceed sedan ground clearance (~15cm). Air intakes and exhausts remain clear. |
| **Half-Knee** | 10" (0.25m) | **Passable** (100%) | **Passable** (100%) | **Passable** (100%) | **Passable** (100%) | Within tolerable wading limit for slow traversal. Low zone is excluded from route avoidance polygons. |
| **Half-Tire** | 13" (0.33m) | **Penalized** (80% Safe) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | **Passable** (85% Safe) | **Moto/Sedan:** Water reaches scooter CVT intakes and car door seals; hydro-lock risk.<br>**Pedestrian:** DOH *Leptospira* health hazard advisory applies.<br>**SUV:** Safely within 700mm wading depth. |
| **Knee** | 19" (0.48m) | **Penalized** (80% Safe) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | **Passable** (85% Safe) | **Sedan:** Floods exhaust and cabin floorboards; loss of traction.<br>**Moto:** Engine stalls immediately.<br>**Pedestrian:** Heavily penalized due to Leptospirosis infection and open curb hazards.<br>**SUV:** Within wading limit. |
| **Tires** | 26" (0.66m) | **Strong caution** (40% Safe) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | Walking is a highly discouraged fallback; vehicle navigation remains unavailable. |
| **Waist** | 37" (0.94m) | **Strong caution** (40% Safe) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | Walking remains possible but exposed to currents, contaminated water, debris, and hidden hazards. |
| **Chest** | 45" (1.14m) | **Strong caution** (40% Safe) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | This is the strongest public walking warning; vehicle navigation remains blocked. |
| **Neck & Above** | >45" (>1.14m) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | 🚫 **BLOCKED** (0%) | **100% IMPASSABLE TO ALL PROFILES.** Complete road closure; extreme danger of drowning and total vehicle submersion. |

---

## 5. Implementation Nuances: Code vs. MMDA Standards

When reviewing the implementation against theoretical documentation, three key design decisions stand out:

### 1. Orange Is a Vehicle Closure and Strong Walking Warning
* **MMDA View:** MMDA classifies **Tires (26")**, **Waist (37")**, and **Chest (45")** as **NPATV** (Not Passable to All Types of Vehicles).
* **LANES Implementation:** `high`/Orange is a 40% safety, strongly cautioned fallback for Walking only. It remains hard-blocked for Bike/Motorcycle, Low Clearance, and High Clearance routes. `extreme`/Red is hard-blocked for every public profile.
* **Reasoning:** A person may remain above water at Orange depth, but hazards still make it a last-choice route. Vehicle wading specifications cannot account for currents, debris, open manholes, visibility, or local road condition.

### 2. Provider Adapters Share One Eligibility Decision
* **Valhalla (`valhalla_service.py`):** Receives hard-exclusion polygons through documented `exclude_polygons` and may use native motorcycle/pedestrian costing.
* **ORS (`ors_service.py`):** Receives the same hard-exclusion polygons as GeoJSON `options.avoid_polygons`; it uses `driving-car` for public vehicle profiles and `foot-walking` for Walking.
* **Shared evaluation:** Provider output is evaluated against authoritative active-zone geometry after routing. This determines route eligibility, deterministic safety score (100 dry, 95 low, 85 cautious Heavy/Medium, 80 cautious Walking/Medium, 40 strongly cautioned Walking/Orange), exposure details, de-duplication, and card category.

### 3. Identical Thresholds for Motorcycles and Low Clearance Sedans
In the backend logic:
```python
elif vehicle_profile in ["motorcycle", "light"]:
    blocked = red + orange + yellow
    penalized = []
    risk_map = {}
```
Both commuter motorcycles and compact sedans are treated with identical strictness: **both are strictly blocked from Half-Tire (13" / Yellow) and above**. 

While a scooter's air intake is low and vulnerable to water spray, a sedan's low bumper and cabin air intake cause hydro-locking at virtually the same depth (~30cm). Both vehicle categories require immediate avoidance routing.

---

## 6. Verification and File Reference Map

For development, testing, or capstone defense, the passability logic is located in the following files:

1. **Depth UI Selection:** [`frontend/src/features/hazards/FloodReportPanel.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx#L78-L92)
2. **Vehicle Profile Selection:** [`frontend/src/features/routing/RoutePanel.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/routing/RoutePanel.tsx#L172-L177)
3. **Shared flood policy, evaluation, and ranking:** [`backend/app/services/flood_routing_policy.py`](file:///d:/Documents/Github/LANES/backend/app/services/flood_routing_policy.py)
4. **Valhalla and ORS provider adapters:** [`backend/app/services/valhalla_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/valhalla_service.py) and [`backend/app/services/ors_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/ors_service.py)
5. **Routing orchestration:** [`backend/app/services/routing_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/routing_service.py)
