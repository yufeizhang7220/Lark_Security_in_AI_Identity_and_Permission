from typing import Dict, Any, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel
from logger import AuditLogger
from anomaly_detector import AnomalyDetector
from storage import AuditStorage

router = APIRouter()

logger = AuditLogger()
detector = AnomalyDetector()


class AuditRequest(BaseModel):
    agent_id: str
    start_time: int
    end_time: int
    operation: str
    detail: Dict[str, Any]


class AuditResponse(BaseModel):
    valid: bool
    fail_reason: str


@router.post("/logs", response_model=AuditResponse)
def audit_logs(request: AuditRequest):
    is_valid, fail_reason = detector.check_audit_legality(
        agent_id=request.agent_id,
        start_time=request.start_time,
        end_time=request.end_time,
        operation=request.operation,
        detail=request.detail
    )

    return {
        "valid": is_valid,
        "fail_reason": fail_reason if not is_valid else ""
    }


@router.post("/record")
def record_log(request: dict):
    agent_id = request.get("agent_id", "")
    ip = request.get("ip", "")
    operation = request.get("operation", "")
    status = request.get("status", "success")
    detail = request.get("detail", {})

    log_id = logger.log(agent_id, ip, operation, status, detail)

    return {
        "code": 200,
        "message": "日志记录成功",
        "data": {"log_id": log_id}
    }


@router.post("/record/registration")
def record_registration(request: dict):
    agent_id = request.get("agent_id", "")
    ip = request.get("ip", "")
    subtype = request.get("subtype", "")
    scope = request.get("scope", {})
    agent_secret_masked = request.get("agent_secret", "")
    status = request.get("status", "success")
    fail_reason = request.get("fail_reason", "")

    log_id = logger.log_registration(agent_id, ip, subtype, scope, agent_secret_masked, status, fail_reason)

    return {
        "code": 200,
        "message": "注册日志记录成功",
        "data": {"log_id": log_id}
    }


@router.post("/record/authorization")
def record_authorization(request: dict):
    agent_id = request.get("agent_id", "")
    ip = request.get("ip", "")
    token_id = request.get("token_id", "")
    applied_scope = request.get("applied_scope", {})
    granted_scope = request.get("granted_scope", {})
    expire_at = request.get("expire_at", 0)
    status = request.get("status", "success")
    fail_reason = request.get("fail_reason", "")

    log_id = logger.log_authorization(agent_id, ip, token_id, applied_scope, granted_scope, expire_at, status, fail_reason)

    return {
        "code": 200,
        "message": "授权日志记录成功",
        "data": {"log_id": log_id}
    }


@router.post("/record/verification")
def record_verification(request: dict):
    agent_id = request.get("agent_id", "")
    ip = request.get("ip", "")
    token_id = request.get("token_id", "")
    required_scope = request.get("required_scope", {})
    valid = request.get("valid", True)
    fail_reason = request.get("fail_reason", "")

    log_id = logger.log_verification(agent_id, ip, token_id, required_scope, valid, fail_reason)

    return {
        "code": 200,
        "message": "验证日志记录成功",
        "data": {"log_id": log_id}
    }


@router.get("/export")
def export_logs(start_time: int, end_time: int):
    logs = logger.export_logs(start_time, end_time)

    return {
        "code": 200,
        "message": "success",
        "data": logs
    }


@router.get("/blacklist")
def get_blacklist():
    blacklist = AuditStorage.load_blacklist()

    return {
        "code": 200,
        "message": "success",
        "data": blacklist
    }


@router.post("/blacklist/add")
def add_to_blacklist(agent_id: Optional[str] = None, ip: Optional[str] = None, user_id: Optional[str] = None):
    if not agent_id and not ip and not user_id:
        return {
            "code": 400,
            "message": "至少需要提供agent_id、ip或user_id中的一个"
        }

    AuditStorage.add_to_blacklist(agent_id=agent_id, ip=ip, user_id=user_id)

    return {
        "code": 200,
        "message": "已加入黑名单"
    }


@router.post("/blacklist/remove")
def remove_from_blacklist(agent_id: Optional[str] = None, ip: Optional[str] = None, user_id: Optional[str] = None):
    blacklist = AuditStorage.load_blacklist()

    if agent_id and agent_id in blacklist["agents"]:
        blacklist["agents"].remove(agent_id)
    if ip and ip in blacklist["ips"]:
        blacklist["ips"].remove(ip)
    if user_id and user_id in blacklist["users"]:
        blacklist["users"].remove(user_id)

    AuditStorage.save_blacklist(blacklist)

    return {
        "code": 200,
        "message": "已从黑名单移除"
    }


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Audit-Trail-API"
    }