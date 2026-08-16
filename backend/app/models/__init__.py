# Domain models are imported here to allow convenient "from app.models import X"
from app.models.role import Role
from app.models.user import User
from app.models.profile import Profile
from app.models.address import Address
from app.models.otp import OTPVerification
from app.models.report import FloodReport, FloodAvoidanceZone, FloodReportLocation, FloodReportSurvey, ReportSource, ReportSeverity, ReportStatus
from app.models.audit import AuditLog
from app.models.setting import SystemSetting
from app.models.interaction import PostInteraction, CommentInteraction
from app.models.comment import Comment
from app.models.post import CommunityPost
from app.models.notification import Notification
from app.models.saved_place import SavedPlace

# Route domain currently has no models (mostly algorithmic), adding comment per user request
# from app.models.route import ...
