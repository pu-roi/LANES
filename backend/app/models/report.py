import enum
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.core.database import Base


class ReportSource(str, enum.Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    USER_REPORT = "direct_user"
    MANUAL_SEEDER = "manual_seeder"


class ReportSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class HazardPresence(str, enum.Enum):
    YES = "yes"
    NO = "no"
    UNSURE = "unsure"


class FloodReport(Base):
    """
    FloodReport model representing incoming Taglish flood feeds or manual user alerts.
    """
    __tablename__ = "flood_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    raw_text: Mapped[str] = mapped_column(String)
    
    source: Mapped[ReportSource] = mapped_column(Enum(ReportSource, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]))
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    severity: Mapped[ReportSeverity] = mapped_column(Enum(ReportSeverity, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]))
    depth: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]), default=ReportStatus.PENDING)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # [NEW] Fields for Community Feed
    human_readable_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    barangay: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # PostGIS Geometry column for generic geometry (Point or LineString) (SRID 4326 = WGS 84 coordinate system)
    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    avoidance_zones: Mapped[List["FloodAvoidanceZone"]] = relationship(
        "FloodAvoidanceZone",
        back_populates="report",
        cascade="all, delete-orphan"
    )
    locations: Mapped[List["FloodReportLocation"]] = relationship(
        "FloodReportLocation",
        back_populates="report",
        cascade="all, delete-orphan"
    )
    community_post: Mapped[Optional["CommunityPost"]] = relationship(
        "CommunityPost",
        back_populates="report",
        cascade="all, delete-orphan",
        uselist=False
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id]
    )
    survey: Mapped[Optional["FloodReportSurvey"]] = relationship(
        "FloodReportSurvey",
        back_populates="report",
        cascade="all, delete-orphan",
        uselist=False
    )


class FloodReportLocation(Base):
    """
    FloodReportLocation model storing extracted locations for 3NF normalization.
    """
    __tablename__ = "flood_report_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("flood_reports.id", ondelete="CASCADE"), index=True)
    location_name: Mapped[str] = mapped_column(String(100), index=True)

    # Relationships
    report: Mapped["FloodReport"] = relationship("FloodReport", back_populates="locations")


class FloodReportSurvey(Base):
    """
    FloodReportSurvey model storing the survey responses for a flood report.
    """
    __tablename__ = "flood_report_surveys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("flood_reports.id", ondelete="CASCADE"), index=True, unique=True)
    
    passable_vehicles: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    hidden_hazards: Mapped[HazardPresence] = mapped_column(
        Enum(HazardPresence, native_enum=False, length=50, values_callable=lambda x: [e.value for e in x]),
        default=HazardPresence.UNSURE
    )

    report: Mapped["FloodReport"] = relationship("FloodReport", back_populates="survey")


class FloodAvoidanceZone(Base):
    """
    FloodAvoidanceZone model representing generated detour areas around flooded coordinates.
    """
    __tablename__ = "flood_avoidance_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("flood_reports.id", ondelete="CASCADE"), index=True)
    
    # PostGIS Geometry column for polygonal boundaries representing avoidance buffer areas
    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    report: Mapped["FloodReport"] = relationship("FloodReport", back_populates="avoidance_zones")

    @property
    def severity(self) -> str:
        return self.report.severity.value if self.report and hasattr(self.report.severity, 'value') else "medium"

    @property
    def depth(self) -> Optional[str]:
        return self.report.depth if self.report else None

    @property
    def report_geometry(self) -> Any:
        return self.report.geometry if self.report else None

    @property
    def report_text(self) -> Optional[str]:
        return self.report.raw_text if self.report else None

    @property
    def reporter_name(self) -> str:
        if self.report and self.report.user:
            return self.report.user.full_name or self.report.user.username or "Anonymous"
        return "System"

    @property
    def reporter_role(self) -> Optional[str]:
        if self.report and self.report.user and hasattr(self.report.user, 'role') and self.report.user.role:
            return self.report.user.role.name
        return None

    @property
    def passable_vehicles(self) -> Optional[str]:
        if self.report and self.report.survey:
            return self.report.survey.passable_vehicles
        return None

    @property
    def hidden_hazards(self) -> Optional[str]:
        if self.report and self.report.survey and hasattr(self.report.survey.hidden_hazards, 'value'):
            return self.report.survey.hidden_hazards.value
        return None

    @property
    def reporter_trust_score(self) -> Optional[float]:
        if self.report and self.report.user and self.report.user.profile:
            return float(self.report.user.profile.trust_score)
        return 100.0

    @property
    def reporter_reports_submitted(self) -> Optional[int]:
        if self.report and self.report.user and self.report.user.profile:
            return self.report.user.profile.reports_submitted
        return 0

    @property
    def reporter_reports_verified(self) -> Optional[int]:
        if self.report and self.report.user and self.report.user.profile:
            return self.report.user.profile.reports_approved
        return 0
