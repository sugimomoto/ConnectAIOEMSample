from backend.models.api_log import ApiLog
from backend.models import db


class ApiLogService:
    def list_logs(self, user_id: int, limit: int = 50, offset: int = 0) -> dict:
        query = ApiLog.query.filter_by(user_id=user_id).order_by(ApiLog.timestamp.desc())
        total = query.count()
        logs = query.limit(limit).offset(offset).all()
        return {
            "logs": [self._to_dict(log) for log in logs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def clear_logs(self, user_id: int) -> None:
        ApiLog.query.filter_by(user_id=user_id).delete()
        db.session.commit()

    def _to_dict(self, log: ApiLog) -> dict:
        return {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "method": log.method,
            "endpoint": log.endpoint,
            "status_code": log.status_code,
            "elapsed_ms": log.elapsed_ms,
            "request_body": log.request_body,
            "response_body": log.response_body,
        }
