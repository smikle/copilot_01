"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app, follow_redirects=False)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities with correct structure"""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # We have 9 activities defined

        # Check that each activity has the required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_includes_participants(self, client):
        """Test that activities include participant lists"""
        response = client.get("/activities")
        data = response.json()

        # Check specific activities that should have participants
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]

        programming_class = data["Programming Class"]
        assert "emma@mergington.edu" in programming_class["participants"]
        assert "sophia@mergington.edu" in programming_class["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful_for_empty_activity(self, client):
        """Test successful signup for activity with no participants"""
        response = client.post("/activities/Basketball Team/signup?email=test@example.com")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "test@example.com" in data["message"]
        assert "Basketball Team" in data["message"]

        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "test@example.com" in activities["Basketball Team"]["participants"]

    def test_signup_successful_for_existing_participants(self, client):
        """Test successful signup for activity that already has participants"""
        # First signup
        client.post("/activities/Art Club/signup?email=first@example.com")

        # Second signup
        response = client.post("/activities/Art Club/signup?email=second@example.com")
        assert response.status_code == 200

        # Verify both participants are there
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities["Art Club"]["participants"]
        assert "first@example.com" in participants
        assert "second@example.com" in participants

    def test_signup_duplicate_email_returns_400(self, client):
        """Test that signing up with same email twice returns 400"""
        # First signup
        client.post("/activities/Drama Club/signup?email=duplicate@example.com")

        # Second signup with same email
        response = client.post("/activities/Drama Club/signup?email=duplicate@example.com")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post("/activities/NonExistent Activity/signup?email=test@example.com")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_missing_email_parameter(self, client):
        """Test signup without email parameter"""
        response = client.post("/activities/Science Club/signup")
        # FastAPI should return 422 for missing required query parameter
        assert response.status_code == 422

    def test_signup_empty_email_string(self, client):
        """Test signup with empty email string"""
        response = client.post("/activities/Debate Club/signup?email=")
        assert response.status_code == 200  # Currently no validation

        # Verify empty email was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "" in activities["Debate Club"]["participants"]

    def test_signup_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        special_email = "test_tag@example.com"
        response = client.post("/activities/Soccer Club/signup?email=" + special_email)
        assert response.status_code == 200

        # Verify special email was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert special_email in activities["Soccer Club"]["participants"]

    def test_signup_case_sensitive_activity_names(self, client):
        """Test that activity names are case sensitive"""
        # Correct case
        response = client.post("/activities/Chess Club/signup?email=case@example.com")
        assert response.status_code == 200

        # Wrong case
        response = client.post("/activities/chess club/signup?email=wrongcase@example.com")
        assert response.status_code == 404


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_remove_participant_successful(self, client):
        """Test successful removal of participant"""
        # First add a participant
        client.post("/activities/Gym Class/signup?email=remove@example.com")

        # Then remove them
        response = client.delete("/activities/Gym Class/signup?email=remove@example.com")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "remove@example.com" in data["message"]
        assert "Gym Class" in data["message"]

        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "remove@example.com" not in activities["Gym Class"]["participants"]

    def test_remove_nonexistent_activity_returns_404(self, client):
        """Test removing from non-existent activity returns 404"""
        response = client.delete("/activities/NonExistent Activity/signup?email=test@example.com")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_remove_nonexistent_participant_returns_404(self, client):
        """Test removing non-existent participant returns 404"""
        response = client.delete("/activities/Chess Club/signup?email=nonexistent@example.com")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Participant not found" in data["detail"]

    def test_remove_missing_email_parameter(self, client):
        """Test remove without email parameter"""
        response = client.delete("/activities/Programming Class/signup")
        # FastAPI should return 422 for missing required query parameter
        assert response.status_code == 422


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that GET / redirects to static index.html"""
        response = client.get("/")
        assert response.status_code == 307  # Temporary redirect

        # Check redirect location
        assert response.headers["location"] == "/static/index.html"


class TestDataIntegrity:
    """Tests for data persistence and integrity"""

    def test_activities_persist_across_requests(self, client):
        """Test that activity data persists across multiple requests"""
        # Add participant
        client.post("/activities/Art Club/signup?email=persist@example.com")

        # Make another request
        response = client.get("/activities")
        activities = response.json()

        # Verify participant is still there
        assert "persist@example.com" in activities["Art Club"]["participants"]

    def test_multiple_activities_signups_work_independently(self, client):
        """Test that signups to different activities work independently"""
        # Signup to two different activities
        client.post("/activities/Drama Club/signup?email=multi@example.com")
        client.post("/activities/Science Club/signup?email=multi@example.com")

        # Verify in both activities
        response = client.get("/activities")
        activities = response.json()

        assert "multi@example.com" in activities["Drama Club"]["participants"]
        assert "multi@example.com" in activities["Science Club"]["participants"]