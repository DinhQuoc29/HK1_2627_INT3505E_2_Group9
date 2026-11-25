"""Endpoint Sellers (/api/v1): nộp hồ sơ người bán (buyer) và duyệt hồ sơ (admin)."""
import uuid
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response

from accounts import emails
from accounts.authentication import CurrentAuth, get_settings
from accounts.permissions import require_role
from config import Settings
from db import session_scope
from sellers import service
from sellers.schema import AdminApplicationOut, AdminApplicationPage, ApplicationOut, ApplyRequest, RejectRequest

router = APIRouter(prefix="/api/v1")


@router.post("/seller-applications", status_code=201, response_model=ApplicationOut)
def submit_application(
    body: ApplyRequest, response: Response, tasks: BackgroundTasks, request: Request,
    auth: CurrentAuth = Depends(require_role("buyer", "seller", "admin")), st: Settings = Depends(get_settings),
):
    """Buyer đã xác minh email nộp hồ sơ mở shop; admin duyệt thì mới thành seller."""
    with session_scope() as s:
        out = service.apply(s, auth.user.id, body.name, body.province_code)
    tasks.add_task(
        request.app.state.mailer.send,
        emails.application_submitted_email(st, auth.user.email, auth.user.full_name, out.shop_name),
    )
    response.headers["Cache-Control"] = "no-store"
    return out


@router.get("/seller-applications/me", response_model=ApplicationOut)
def my_application(response: Response, auth: CurrentAuth = Depends(require_role("buyer", "seller", "admin"))):
    """Hồ sơ gần nhất của tôi (404 nếu chưa nộp)."""
    with session_scope() as s:
        out = service.my_latest(s, auth.user.id)
    response.headers["Cache-Control"] = "no-store"
    return out


@router.get("/admin/seller-applications", response_model=AdminApplicationPage)
def admin_list_applications(
    response: Response,
    status: Literal["pending", "approved", "rejected"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None, max_length=200),
    _: CurrentAuth = Depends(require_role("admin")),
):
    response.headers["Cache-Control"] = "no-store"
    with session_scope() as s:
        return service.admin_list(s, status=status, limit=limit, cursor=cursor)


@router.post("/admin/seller-applications/{application_id}/approval", response_model=AdminApplicationOut)
def approve_application(application_id: uuid.UUID, tasks: BackgroundTasks, request: Request,
                        auth: CurrentAuth = Depends(require_role("admin")), st: Settings = Depends(get_settings)):
    """Duyệt: tạo shop và nâng người nộp lên seller trong một giao dịch."""
    with session_scope() as s:
        out, user, shop = service.approve(s, auth.user, application_id)
    tasks.add_task(request.app.state.mailer.send, emails.application_approved_email(st, user.email, user.full_name, shop.name))
    return out


@router.post("/admin/seller-applications/{application_id}/rejection", response_model=AdminApplicationOut)
def reject_application(application_id: uuid.UUID, body: RejectRequest, tasks: BackgroundTasks, request: Request,
                       auth: CurrentAuth = Depends(require_role("admin")), st: Settings = Depends(get_settings)):
    with session_scope() as s:
        out, user = service.reject(s, auth.user, application_id, body.reason)
    tasks.add_task(request.app.state.mailer.send,
                   emails.application_rejected_email(st, user.email, user.full_name, out.shop_name, body.reason))
    return out
