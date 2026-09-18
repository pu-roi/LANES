# Schemas index
from app.schemas.user import UserBase, UserCreate, UserResponse, UsersPaginatedResponse, UserStatusUpdateRequest, UserRoleUpdateRequest
from app.schemas.report import (
    FloodReportBase, FloodReportCreate, FloodReportResponse,
    FloodAvoidanceZoneBase, FloodAvoidanceZoneCreate, FloodAvoidanceZoneResponse,
    FloodAvoidanceZoneCreateOfficial, FloodAvoidanceZoneUpdate,
    FloodReportsPaginatedResponse, AdminDashboardStats,
    FloodAvoidanceZonesPaginatedResponse, AvoidanceZoneDeactivateBulkRequest,
    AvoidanceZoneUpdateRequest, ApproveReportRequest, NearbyZoneResponse,
    MergePendingReportsRequest, MergePendingReportsResponse,
    MergeConflict, MergeCandidateItem, MergeCandidatesListResponse,
    MergedZoneFinalData, MergeReportsRequest, MergeReportsResponse
)
from app.schemas.route import RouteRequest, RouteResponse, LineStringGeometry, RouteOption, MultiRouteResponse, FloodExposure, BlockedRouteBaseline
from app.schemas.common import PointGeometry, PolygonGeometry
from app.schemas.auth import (
    Token, TokenPayload, GoogleAuthRequest, GoogleAuthResponse,
    PasswordResetRequest, PasswordResetVerifyRequest, PasswordResetVerifyResponse, PasswordResetConfirm
)
from app.schemas.audit import AuditLogCreate, AuditLogResponse, AuditLogsPaginatedResponse
from app.schemas.post import (
    CommunityPostBase, CommunityPostCreate, CommunityPostUpdate,
    CommunityPostReportCreate, CommunityPostModerationResolution,
    CommunityPostEditHistoryResponse, CommunityPostResponse,
    CommunityPostPaginatedResponse, CommentBase, CommentCreate,
    CommentResponse, ArchivedCommunityPostResponse,
    ArchivedCommunityPostsPaginatedResponse
)
from app.schemas.saved_place import SavedPlaceBase, SavedPlaceCreate, SavedPlaceUpdate, SavedPlaceResponse
from app.schemas.role import RoleBase, RoleCreate, RoleUpdate, RoleResponse
from app.schemas.data import BackupFile, RestoreRequest, CleanupRequest, ExportResponse
from app.schemas.profile import ProfileBase, ProfileCreate, ProfileResponse, ProfileUpdate
from app.schemas.address import AddressBase, AddressCreate, AddressResponse, AddressUpdate
from app.schemas.otp import OTPVerificationBase, OTPVerificationCreate, OTPVerificationResponse
from app.schemas.contact import ContactMessageCreate, ContactMessageResponse
