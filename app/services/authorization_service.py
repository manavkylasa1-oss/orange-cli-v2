from app.db import db
from app.models import Portfolio, PortfolioAccess, User

class AuthorizationException(Exception):
    pass

ROLE_VIEWER = 'viewer'
ROLE_MANAGER = 'manager'
ROLE_OWNER = 'owner'

def has_role(portfolio_id: int, username: str, required_role: str) -> bool:
    """
    Checks if a user has at least the required role for a portfolio.
    Roles: owner > manager > viewer
    """
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        return False
    
    # Check if owner
    if portfolio.owner == username:
        return True
    
    if required_role == ROLE_OWNER:
        return False # Only the actual owner satisfies ROLE_OWNER
    
    # Check access grants
    grant = db.session.query(PortfolioAccess).filter_by(
        portfolio_id=portfolio_id, 
        username=username
    ).one_or_none()
    
    if not grant:
        return False
        
    if required_role == ROLE_MANAGER:
        return grant.role == ROLE_MANAGER
        
    if required_role == ROLE_VIEWER:
        return grant.role in [ROLE_VIEWER, ROLE_MANAGER]
        
    return False

def can_view_portfolio(portfolio_id: int, username: str) -> bool:
    return has_role(portfolio_id, username, ROLE_VIEWER)

def can_trade_portfolio(portfolio_id: int, username: str) -> bool:
    return has_role(portfolio_id, username, ROLE_MANAGER)

def is_owner(portfolio_id: int, username: str) -> bool:
    return has_role(portfolio_id, username, ROLE_OWNER)

def grant_access(portfolio_id: int, username: str, role: str):
    """
    Grants or updates access for a user to a portfolio.
    """
    if role not in [ROLE_VIEWER, ROLE_MANAGER]:
        raise AuthorizationException(f"Invalid role: {role}")
        
    # Check if user exists
    user = db.session.query(User).filter_by(username=username).one_or_none()
    if not user:
        raise AuthorizationException(f"User {username} does not exist")
        
    grant = db.session.query(PortfolioAccess).filter_by(
        portfolio_id=portfolio_id, 
        username=username
    ).one_or_none()
    
    if grant:
        grant.role = role
    else:
        db.session.add(PortfolioAccess(portfolio_id=portfolio_id, username=username, role=role))
    
    db.session.flush()

def revoke_access(portfolio_id: int, username: str):
    grant = db.session.query(PortfolioAccess).filter_by(
        portfolio_id=portfolio_id, 
        username=username
    ).one_or_none()
    
    if grant:
        db.session.delete(grant)
        db.session.flush()
