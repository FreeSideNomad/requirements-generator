"""
Web interface routes for HTML pages.
Provides tenant selection and basic dashboard functionality.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..shared.tenant_middleware import get_current_tenant, tenant_context
from ..auth.routes import get_current_user_dependency
from ..auth.schemas import UserResponse
from ..tenants.service import TenantService
from ..tenants.schemas import TenantResponse

web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="templates")


@web_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - redirects to login for unauthenticated users."""
    return RedirectResponse(url="/login", status_code=302)


@web_router.get("/tenant-select", response_class=HTMLResponse)
async def tenant_select(request: Request):
    """Tenant selection page."""
    tenant_service = TenantService()
    tenants, _ = await tenant_service.list_tenants(page=1, page_size=50, active_only=True)

    return templates.TemplateResponse("pages/tenant_select.html", {
        "request": request,
        "tenants": tenants,
        "title": "Select Tenant"
    })


@web_router.post("/tenant-select")
async def set_tenant(
    request: Request,
    tenant_id: uuid.UUID = Form(...),
    redirect_to: Optional[str] = Form(default="/dashboard")
):
    """Set tenant context and redirect."""
    tenant_service = TenantService()
    tenant = await tenant_service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # In a real implementation, you'd set this in a session or token
    # For now, we'll redirect with tenant ID as a parameter
    redirect_url = f"{redirect_to}?tenant_id={tenant_id}"
    return RedirectResponse(url=redirect_url, status_code=302)


@web_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: UserResponse = Depends(get_current_user_dependency)
):
    """Main dashboard page."""
    from ..auth.service import AuthService

    # Check if user needs to set up a tenant first
    auth_service = AuthService()
    needs_tenant = await auth_service.user_needs_tenant(current_user.id)

    if needs_tenant:
        return RedirectResponse(url="/tenant-setup", status_code=302)

    tenant_service = TenantService()

    # Get tenant information
    tenant = None
    if tenant_context.has_tenant:
        tenant = await tenant_service.get_tenant(tenant_context.tenant_id)

    return templates.TemplateResponse("pages/dashboard.html", {
        "request": request,
        "user": current_user,
        "tenant": tenant,
        "title": "Dashboard"
    })


@web_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("pages/login.html", {
        "request": request,
        "title": "Login"
    })


@web_router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    token: Optional[str] = None
):
    """Registration page."""
    invitation_data = None

    # If invitation token provided, verify and show invitation details
    if token:
        from ..auth.service import AuthService
        try:
            auth_service = AuthService()
            invitation_data = await auth_service.verify_invitation(token)
        except Exception:
            # Invalid token, continue without invitation data
            pass

    return templates.TemplateResponse("pages/register.html", {
        "request": request,
        "invitation_token": token,
        "invitation_data": invitation_data,
        "title": "Register"
    })


@web_router.get("/tenant-setup", response_class=HTMLResponse)
async def tenant_setup_page(
    request: Request,
    current_user: UserResponse = Depends(get_current_user_dependency)
):
    """Tenant setup page for new users."""
    from ..auth.service import AuthService

    auth_service = AuthService()
    needs_tenant = await auth_service.user_needs_tenant(current_user.id)

    if not needs_tenant:
        return RedirectResponse(url="/dashboard", status_code=302)

    tenant_service = TenantService()
    industry_templates = tenant_service.get_all_industry_templates()

    return templates.TemplateResponse("pages/tenant_setup.html", {
        "request": request,
        "user": current_user,
        "industry_templates": industry_templates,
        "title": "Setup Your Organization"
    })


@web_router.post("/tenant-setup")
async def handle_tenant_setup(
    request: Request,
    current_user: UserResponse = Depends(get_current_user_dependency),
    organization_name: str = Form(...),
    subdomain: str = Form(...),
    industry: str = Form(...),
    subscription_tier: str = Form(default="trial")
):
    """Handle tenant setup form submission."""
    from ..auth.service import AuthService
    from ..tenants.schemas import TenantCreate

    try:
        auth_service = AuthService()
        tenant_service = TenantService()

        # Create tenant
        tenant_data = TenantCreate(
            name=organization_name,
            subdomain=subdomain,
            industry=industry,
            subscription_tier=subscription_tier
        )

        tenant = await tenant_service.create_tenant(tenant_data, admin_user_id=current_user.id)

        # Link user to tenant
        await auth_service.link_user_to_tenant(current_user.id, tenant.id)

        return RedirectResponse(url="/dashboard", status_code=302)

    except Exception as e:
        # Return to setup page with error
        tenant_service = TenantService()
        industry_templates = tenant_service.get_all_industry_templates()

        return templates.TemplateResponse("pages/tenant_setup.html", {
            "request": request,
            "user": current_user,
            "industry_templates": industry_templates,
            "error": str(e),
            "title": "Setup Your Organization"
        })


@web_router.get("/tenant/create", response_class=HTMLResponse)
async def create_tenant_page(request: Request):
    """Tenant creation page."""
    tenant_service = TenantService()
    industry_templates = tenant_service.get_all_industry_templates()

    return templates.TemplateResponse("pages/tenant_create.html", {
        "request": request,
        "industry_templates": industry_templates,
        "title": "Create Tenant"
    })


@web_router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    current_user: UserResponse = Depends(get_current_user_dependency)
):
    """Admin users management page."""
    # Check admin permissions
    if current_user.role not in ["tenant_admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )

    return templates.TemplateResponse("pages/admin/users.html", {
        "request": request,
        "user": current_user,
        "tenant": None,  # Would fetch tenant here
        "title": "User Management"
    })


@web_router.get("/admin/tenant", response_class=HTMLResponse)
async def admin_tenant_settings(
    request: Request,
    current_user: UserResponse = Depends(get_current_user_dependency)
):
    """Admin tenant settings page."""
    # Check admin permissions
    if current_user.role not in ["tenant_admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )

    tenant_service = TenantService()
    tenant = None
    if tenant_context.has_tenant:
        tenant = await tenant_service.get_tenant(tenant_context.tenant_id)

    return templates.TemplateResponse("pages/admin/tenant_settings.html", {
        "request": request,
        "user": current_user,
        "tenant": tenant,
        "title": "Tenant Settings"
    })


@web_router.get("/profile", response_class=HTMLResponse)
async def user_profile(
    request: Request,
    current_user: UserResponse = Depends(get_current_user_dependency)
):
    """User profile page."""
    return templates.TemplateResponse("pages/profile.html", {
        "request": request,
        "user": current_user,
        "tenant": None,  # Would fetch tenant here
        "title": "Profile Settings"
    })