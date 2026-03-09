from app.errors import APIError
from app.models import PortfolioAccess

ROLE_VIEWER = 'viewer'
ROLE_MANAGER = 'manager'


def grant_access(portfolio_id: int, user_id: str, role: str):
    if role not in {ROLE_VIEWER, ROLE_MANAGER}:
        raise APIError('forbidden', 'Invalid role', 400)
    existing = PortfolioAccess.query.filter_by(portfolio_id=portfolio_id, user_id=user_id).one_or_none()
    if existing:
        existing.role = role
        return existing
    grant = PortfolioAccess(portfolio_id=portfolio_id, user_id=user_id, role=role)
    from app.db import db

    db.session.add(grant)
    return grant


def revoke_access(portfolio_id: int, user_id: str):
    grant = PortfolioAccess.query.filter_by(portfolio_id=portfolio_id, user_id=user_id).one_or_none()
    if not grant:
        raise APIError('not_found', 'Access grant not found', 404)
    from app.db import db

    db.session.delete(grant)


def has_access(portfolio_id: int, user_id: str, required: str) -> bool:
    grant = PortfolioAccess.query.filter_by(portfolio_id=portfolio_id, user_id=user_id).one_or_none()
    if not grant:
        return False
    if required == ROLE_VIEWER:
        return grant.role in {ROLE_VIEWER, ROLE_MANAGER}
    return grant.role == ROLE_MANAGER
