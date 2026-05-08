"""
Comprehensive test suite for the Mergington High School Activities API

Tests cover all 4 endpoints with both happy path and error cases:
- GET / (redirect)
- GET /activities (list all activities)
- POST /activities/{activity_name}/signup (register student)
- DELETE /activities/{activity_name}/remove (unregister student)
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture providing a FastAPI TestClient for all tests"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture to reset activities to initial state before each test.
    This ensures tests don't interfere with each other due to in-memory state.
    """
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Soccer Team": {
            "description": "Competitive soccer training and matches",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": ["james@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Basketball practice and friendly games",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu", "tyler@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and mixed media techniques",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["isabella@mergington.edu"]
        },
        "Theater Club": {
            "description": "Acting, stage performance, and play production",
            "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["grace@mergington.edu", "lucas@mergington.edu"]
        },
        "Math Club": {
            "description": "Advanced mathematics and problem-solving competitions",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 14,
            "participants": ["noah@mergington.edu"]
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking skills",
            "schedule": "Thursdays and Saturdays, 2:00 PM - 3:30 PM",
            "max_participants": 12,
            "participants": ["ava@mergington.edu", "ethan@mergington.edu"]
        }
    }
    
    # Clear current activities
    activities.clear()
    
    # Restore original state
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test (reset again)
    activities.clear()
    activities.update(original_activities)


# ============================================================================
# Root Endpoint Tests
# ============================================================================

class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirect_to_static_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


# ============================================================================
# Get Activities Endpoint Tests
# ============================================================================

class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test that GET /activities returns all activities successfully"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_returns_correct_count(self, client, reset_activities):
        """Test that GET /activities returns all 9 activities"""
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)
    
    def test_get_activities_participant_counts(self, client, reset_activities):
        """Test that participant counts are accurate"""
        response = client.get("/activities")
        data = response.json()
        
        # Verify some known participant counts
        assert len(data["Chess Club"]["participants"]) == 2
        assert len(data["Programming Class"]["participants"]) == 2
        assert len(data["Gym Class"]["participants"]) == 2
        assert len(data["Soccer Team"]["participants"]) == 1


# ============================================================================
# Signup Endpoint Tests
# ============================================================================

class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_registration(self, client, reset_activities):
        """Test that duplicate signup returns 400 error"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Duplicate signup
        response2 = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds participant to activity list"""
        new_email = "addtest@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Programming Class"]["participants"])
        
        # Sign up
        client.post(
            "/activities/Programming Class/signup?email=" + new_email
        )
        
        # Verify participant was added
        response = client.get("/activities")
        final_count = len(response.json()["Programming Class"]["participants"])
        assert final_count == initial_count + 1
        assert new_email in response.json()["Programming Class"]["participants"]
    
    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that participant count increments after signup"""
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Math Club"]["participants"])
        
        # Sign up a new student
        client.post(
            "/activities/Math Club/signup?email=mathstudent@mergington.edu"
        )
        
        # Verify count increased
        response = client.get("/activities")
        new_count = len(response.json()["Math Club"]["participants"])
        assert new_count == initial_count + 1


# ============================================================================
# Remove Participant Endpoint Tests
# ============================================================================

class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/remove endpoint"""
    
    def test_remove_participant_success(self, client, reset_activities):
        """Test successful removal of a participant from activity"""
        response = client.delete(
            "/activities/Chess Club/remove?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
    
    def test_remove_activity_not_found(self, client, reset_activities):
        """Test removal from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/remove?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_remove_student_not_registered(self, client, reset_activities):
        """Test removal of non-registered student returns 400"""
        response = client.delete(
            "/activities/Chess Club/remove?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_remove_decrements_participant_count(self, client, reset_activities):
        """Test that participant count decrements after removal"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Programming Class"]["participants"])
        
        # Remove a participant
        client.delete(
            "/activities/Programming Class/remove?email=emma@mergington.edu"
        )
        
        # Verify count decreased
        response = client.get("/activities")
        new_count = len(response.json()["Programming Class"]["participants"])
        assert new_count == initial_count - 1
    
    def test_remove_participant_really_removed(self, client, reset_activities):
        """Test that participant is actually removed from the list"""
        removed_email = "daniel@mergington.edu"
        
        # Verify participant is initially present
        response = client.get("/activities")
        assert removed_email in response.json()["Chess Club"]["participants"]
        
        # Remove participant
        client.delete(
            f"/activities/Chess Club/remove?email={removed_email}"
        )
        
        # Verify participant is no longer in list
        response = client.get("/activities")
        assert removed_email not in response.json()["Chess Club"]["participants"]


# ============================================================================
# Integration Tests (Multiple Operations)
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_then_remove_workflow(self, client, reset_activities):
        """Test signing up and then removing a participant"""
        email = "workflow@mergington.edu"
        activity = "Debate Team"
        
        # Get initial count
        response = client.get("/activities")
        initial = len(response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify added
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial + 1
        
        # Remove
        response = client.delete(
            f"/activities/{activity}/remove?email={email}"
        )
        assert response.status_code == 200
        
        # Verify back to initial
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial
        assert email not in response.json()[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client, reset_activities):
        """Test signing up same student for multiple activities"""
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Chess Club", "Art Studio", "Math Club"]
        
        # Sign up for multiple activities
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        response = client.get("/activities")
        data = response.json()
        for activity in activities_to_join:
            assert email in data[activity]["participants"]
