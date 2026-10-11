"""Bounded Cloud Run job dispatch/reconciliation with workload credentials."""
from datetime import datetime
import re
import google.auth
from app.core.news_scheduler_auth import BoundedGoogleRequest
import httpx


class NewsJobGateway:
    def __init__(self, job_name: str, client: httpx.Client) -> None:
        if not re.fullmatch(r"projects/[a-z0-9-]+/locations/[a-z0-9-]+/jobs/[a-z0-9-]+", job_name):
            raise ValueError("news_job_not_configured")
        self.job_name = job_name
        self.client = client
        self.credentials = None

    def _call(self, method: str, path: str, **kwargs: object) -> dict:
        if not path.startswith(self.job_name+"/") and path != self.job_name+":run":
            # Operation names are returned by the API; allow only this project's region.
            prefix = self.job_name.split("/jobs/")[0] + "/operations/"
            if not path.startswith(prefix) or not re.fullmatch(r"[a-zA-Z0-9/_-]+", path):
                raise ValueError("invalid_news_operation")
        if self.credentials is None:
            self.credentials, _project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not self.credentials.valid:
            self.credentials.refresh(BoundedGoogleRequest())
        response = self.client.request(method, "https://run.googleapis.com/v2/"+path,
            headers={"Authorization": "Bearer "+self.credentials.token}, **kwargs)
        response.raise_for_status()
        return response.json()

    def start(self, token: str) -> str:
        result = self._call("POST", self.job_name+":run", json={"overrides": {"containerOverrides": [
            {"env": [{"name": "LANES_NEWS_DISPATCH_TOKEN", "value": token}]}]}})
        operation = result.get("name")
        if not operation:
            raise ValueError("news_dispatch_response_invalid")
        return operation

    def reconcile(self, token: str, operation: str | None, reserved_at: datetime) -> str:
        """No resend until an operation or complete execution listing establishes state."""
        if operation:
            result = self._call("GET", operation)
            if not result.get("done"):
                return "running"
            if result.get("error"):
                return "failed"
            execution = result.get("response", {})
            if execution.get("name", "").startswith(self.job_name+"/executions/"):
                execution = self._call("GET", execution["name"])
                if not execution.get("completionTime"):
                    return "running"
                return "failed" if execution.get("failedCount", 0) or execution.get("cancelledCount", 0) else "finished"
            return "unknown"
        page_token = None
        for _page in range(10):
            result = self._call("GET", self.job_name+"/executions", params={"pageSize": 100, "showDeleted": True, **({"pageToken": page_token} if page_token else {})})
            for execution in result.get("executions", []):
                env = [entry for container in execution.get("template", {}).get("containers", []) for entry in container.get("env", [])]
                if any(entry.get("name") == "LANES_NEWS_DISPATCH_TOKEN" and entry.get("value") == token for entry in env):
                    return ("failed" if execution.get("failedCount", 0) or execution.get("cancelledCount", 0) else "finished") if execution.get("completionTime") else "running"
            page_token = result.get("nextPageToken")
            if not page_token:
                return "absent"
        # An incomplete listing cannot establish absence.
        return "unknown"
