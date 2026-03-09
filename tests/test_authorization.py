import pytest
from app.models import User, Portfolio, PortfolioAccess
from app.services import authorization_service

@pytest.fixture
def auth_setup(app, db_session):
    with app.app_context():
        # Create Owner
        owner = User(username="owner_user", password="password", firstname="Owner", lastname="User", balance=1000.0)
        db_session.add(owner)
        
        # Create Manager candidate
        manager = User(username="manager_user", password="password", firstname="Manager", lastname="User", balance=100.0)
        db_session.add(manager)
        
        # Create Viewer candidate
        viewer = User(username="viewer_user", password="password", firstname="Viewer", lastname="User", balance=100.0)
        db_session.add(viewer)
        
        # Create Unauthorized user
        other = User(username="other_user", password="password", firstname="Other", lastname="User", balance=100.0)
        db_session.add(other)
        
        db_session.commit()
        
        # Create Portfolio
        portfolio = Portfolio(name="Auth Portfolio", description="Testing auth", user=owner)
        db_session.add(portfolio)
        db_session.commit()
        
        yield {
            "owner": owner,
            "manager": manager,
            "viewer": viewer,
            "other": other,
            "portfolio": portfolio
        }

def test_is_owner(app, auth_setup):
    with app.app_context():
        portfolio_id = auth_setup["portfolio"].id
        assert authorization_service.is_owner(portfolio_id, "owner_user") is True
        assert authorization_service.is_owner(portfolio_id, "manager_user") is False

def test_role_hierarchy(app, db_session, auth_setup):
    with app.app_context():
        portfolio_id = auth_setup["portfolio"].id
        
        # Grant Manager role
        authorization_service.grant_access(portfolio_id, "manager_user", "manager")
        
        # Manager should be able to view and trade
        assert authorization_service.can_view_portfolio(portfolio_id, "manager_user") is True
        assert authorization_service.can_trade_portfolio(portfolio_id, "manager_user") is True
        assert authorization_service.is_owner(portfolio_id, "manager_user") is False
        
        # Grant Viewer role
        authorization_service.grant_access(portfolio_id, "viewer_user", "viewer")
        
        # Viewer should be able to view but NOT trade
        assert authorization_service.can_view_portfolio(portfolio_id, "viewer_user") is True
        assert authorization_service.can_trade_portfolio(portfolio_id, "viewer_user") is False

def test_unauthorized_access(app, auth_setup):
    with app.app_context():
        portfolio_id = auth_setup["portfolio"].id
        assert authorization_service.can_view_portfolio(portfolio_id, "other_user") is False
        assert authorization_service.can_trade_portfolio(portfolio_id, "other_user") is False

def test_revoke_access(app, db_session, auth_setup):
    with app.app_context():
        portfolio_id = auth_setup["portfolio"].id
        authorization_service.grant_access(portfolio_id, "manager_user", "manager")
        assert authorization_service.can_view_portfolio(portfolio_id, "manager_user") is True
        
        authorization_service.revoke_access(portfolio_id, "manager_user")
        assert authorization_service.can_view_portfolio(portfolio_id, "manager_user") is False

def test_grant_access_invalid_user(app, auth_setup):
    with app.app_context():
        portfolio_id = auth_setup["portfolio"].id
        with pytest.raises(authorization_service.AuthorizationException):
            authorization_service.grant_access(portfolio_id, "nonexistent", "viewer")
