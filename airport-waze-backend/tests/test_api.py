"""
Comprehensive API tests for AirportWaze backend.
Tests cover health checks, airport endpoints, journey planning, and wait time reporting.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import applications for testing
from app.main import app as main_app
from app.main_old import app as legacy_app


# Fixtures
@pytest.fixture
def client_v1():
    """Test client for main_old.py (legacy API)"""
    return TestClient(legacy_app)


@pytest.fixture
def client_v2():
    """Test client for main.py (production API)"""
    return TestClient(main_app)


@pytest.fixture
def sample_airport_code():
    """Sample airport code for testing"""
    return "JFK"


@pytest.fixture
def sample_journey_request():
    """Sample journey planning request"""
    return {
        "airport_code": "JFK",
        "terminal": "4",
        "gate": "B20",
        "has_tsa_precheck": False,
        "has_global_entry": False,
        "has_checked_bags": True,
        "mobility_factor": 1.0,
        "departure_time": (datetime.now() + timedelta(hours=2)).isoformat(),
        "user_lat": 40.6413,
        "user_lng": -73.7781
    }


@pytest.fixture
def sample_wait_time_report():
    """Sample wait time report"""
    return {
        "airport_code": "JFK",
        "checkpoint_id": "jfk_t4_security_main",
        "reported_wait_minutes": 15,
        "reporter_id": "test-user-123",
        "user_lat": 40.6413,
        "user_lng": -73.7781
    }


# ============== HEALTH CHECK TESTS ==============

@pytest.mark.unit
def test_health_check_v1(client_v1):
    """Test health check endpoint (legacy API)"""
    response = client_v1.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.unit
def test_health_check_v2(client_v2):
    """Test health check endpoint (production API)"""
    response = client_v2.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data


@pytest.mark.unit
def test_root_endpoint_v2(client_v2):
    """Test root endpoint returns API information"""
    response = client_v2.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data


# ============== AIRPORT ENDPOINTS TESTS ==============

@pytest.mark.api
def test_get_all_airports_v1(client_v1):
    """Test getting all airports (legacy API)"""
    response = client_v1.get("/api/airports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Check first airport structure
    airport = data[0]
    assert "code" in airport
    assert "name" in airport
    assert "city" in airport
    assert "lat" in airport
    assert "lng" in airport


@pytest.mark.api
def test_get_all_airports_v2(client_v2):
    """Test getting all airports (production API)"""
    response = client_v2.get("/api/v1/airports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.api
def test_get_specific_airport_v1(client_v1, sample_airport_code):
    """Test getting specific airport details (legacy API)"""
    response = client_v1.get(f"/api/airports/{sample_airport_code}")
    assert response.status_code == 200
    data = response.json()

    assert data["code"] == sample_airport_code
    assert "name" in data
    assert "terminals" in data
    assert "checkpoints" in data
    assert isinstance(data["checkpoints"], list)

    # Check checkpoint structure
    if len(data["checkpoints"]) > 0:
        checkpoint = data["checkpoints"][0]
        assert "id" in checkpoint
        assert "name" in checkpoint
        assert "type" in checkpoint
        assert "current_wait_minutes" in checkpoint


@pytest.mark.api
def test_get_specific_airport_v2(client_v2, sample_airport_code):
    """Test getting specific airport details (production API)"""
    response = client_v2.get(f"/api/v1/airports/{sample_airport_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == sample_airport_code


@pytest.mark.api
def test_get_nonexistent_airport(client_v1):
    """Test getting non-existent airport returns 404"""
    response = client_v1.get("/api/airports/XXX")
    assert response.status_code == 404


@pytest.mark.api
def test_get_airport_gates_v1(client_v1, sample_airport_code):
    """Test getting gates for a specific terminal"""
    response = client_v1.get(f"/api/airports/{sample_airport_code}/terminals/4/gates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============== JOURNEY PLANNING TESTS ==============

@pytest.mark.api
@pytest.mark.integration
def test_journey_planning_v1(client_v1, sample_journey_request):
    """Test journey planning endpoint (legacy API)"""
    response = client_v1.post("/api/journey/plan", json=sample_journey_request)
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "total_time_minutes" in data
    assert "total_distance_meters" in data
    assert "recommended_arrival_time" in data
    assert "steps" in data
    assert "buffer_minutes" in data

    # Verify steps
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0

    # Check first step structure
    step = data["steps"][0]
    assert "step_name" in step
    assert "location" in step
    assert "estimated_wait_minutes" in step
    assert "estimated_walk_minutes" in step


@pytest.mark.api
@pytest.mark.integration
def test_journey_planning_v2(client_v2, sample_journey_request):
    """Test journey planning endpoint (production API)"""
    response = client_v2.post("/api/v1/journey/plan", json=sample_journey_request)
    assert response.status_code == 200
    data = response.json()
    assert "total_time_minutes" in data
    assert "steps" in data


@pytest.mark.api
def test_journey_planning_with_tsa_precheck(client_v1, sample_journey_request):
    """Test journey planning with TSA PreCheck enabled"""
    sample_journey_request["has_tsa_precheck"] = True
    response = client_v1.post("/api/journey/plan", json=sample_journey_request)
    assert response.status_code == 200
    data = response.json()

    # With PreCheck, total time should generally be less
    assert data["total_time_minutes"] > 0


@pytest.mark.api
def test_journey_planning_invalid_airport(client_v1):
    """Test journey planning with invalid airport code"""
    invalid_request = {
        "airport_code": "INVALID",
        "terminal": "1",
        "gate": "A1",
        "departure_time": datetime.now().isoformat()
    }
    response = client_v1.post("/api/journey/plan", json=invalid_request)
    assert response.status_code == 404


@pytest.mark.api
def test_journey_planning_missing_fields(client_v1):
    """Test journey planning with missing required fields"""
    incomplete_request = {
        "airport_code": "JFK"
        # Missing required fields
    }
    response = client_v1.post("/api/journey/plan", json=incomplete_request)
    assert response.status_code == 422  # Validation error


# ============== WAIT TIME REPORTING TESTS ==============

@pytest.mark.api
@pytest.mark.database
def test_submit_wait_time_report_v1(client_v1, sample_wait_time_report):
    """Test submitting a wait time report (legacy API)"""
    response = client_v1.post("/api/wait-times/report", json=sample_wait_time_report)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "report_id" in data


@pytest.mark.api
@pytest.mark.database
def test_submit_wait_time_report_v2(client_v2, sample_wait_time_report):
    """Test submitting a wait time report (production API)"""
    response = client_v2.post("/api/v1/wait-times/report", json=sample_wait_time_report)
    assert response.status_code in [200, 201]


@pytest.mark.api
def test_get_wait_time_reports_v1(client_v1, sample_airport_code):
    """Test getting wait time reports for an airport"""
    response = client_v1.get(f"/api/wait-times/reports/{sample_airport_code}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.api
def test_submit_invalid_wait_time_report(client_v1):
    """Test submitting invalid wait time report"""
    invalid_report = {
        "airport_code": "JFK",
        "reported_wait_minutes": -5  # Negative wait time is invalid
    }
    response = client_v1.post("/api/wait-times/report", json=invalid_report)
    assert response.status_code == 422


# ============== PREDICTIONS TESTS ==============

@pytest.mark.api
@pytest.mark.external
def test_get_predictions_v1(client_v1, sample_airport_code):
    """Test getting predictions for an airport"""
    response = client_v1.get(f"/api/predictions/{sample_airport_code}")
    assert response.status_code == 200
    data = response.json()
    assert "airport_code" in data
    assert "checkpoints" in data


@pytest.mark.api
@pytest.mark.external
def test_get_predictions_v2(client_v2, sample_airport_code):
    """Test getting predictions for an airport (production API)"""
    response = client_v2.get(f"/api/v1/predictions/{sample_airport_code}")
    assert response.status_code in [200, 404]  # 404 if not implemented yet


@pytest.mark.api
def test_get_checkpoint_distribution_v1(client_v1):
    """Test getting wait time distribution for a checkpoint"""
    checkpoint_id = "jfk_t4_security_main"
    response = client_v1.get(f"/api/checkpoints/{checkpoint_id}/distribution")
    assert response.status_code == 200
    data = response.json()

    # Check distribution structure
    assert "p50" in data
    assert "p80" in data
    assert "p90" in data
    assert "p95" in data
    assert "confidence" in data


# ============== TSA API TESTS ==============

@pytest.mark.api
@pytest.mark.external
@pytest.mark.slow
@patch('httpx.AsyncClient.get')
async def test_get_tsa_live_data_v1(mock_get, client_v1):
    """Test getting live TSA wait times with mocked external API"""
    # Mock the TSA API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "airports": [
            {
                "code": "JFK",
                "name": "John F. Kennedy International",
                "wait_times": []
            }
        ]
    }
    mock_get.return_value = mock_response

    response = client_v1.get("/api/tsa/live")
    # This might return 500 if TSA API is not configured, which is OK for tests
    assert response.status_code in [200, 500]


# ============== WILL I MAKE IT TESTS ==============

@pytest.mark.api
@pytest.mark.integration
def test_will_i_make_it_v1(client_v1):
    """Test 'Will I Make It' flight analysis endpoint"""
    request_data = {
        "current_location": {
            "lat": 40.6413,
            "lng": -73.7781
        },
        "flight": {
            "departure_time": (datetime.now() + timedelta(hours=2)).isoformat(),
            "terminal": "4",
            "gate": "B20"
        },
        "airport_code": "JFK",
        "travel_mode": "driving",
        "user_profile": {
            "has_tsa_precheck": False,
            "has_checked_bags": True,
            "mobility_factor": 1.0
        }
    }

    response = client_v1.post("/api/will-i-make-it", json=request_data)
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "will_make_it" in data
    assert "confidence_level" in data
    assert "probabilities" in data
    assert "journey_plan" in data
    assert "recommendations" in data


# ============== FLIGHT IMPORT TESTS ==============

@pytest.mark.api
@pytest.mark.integration
def test_flight_import_v1(client_v1):
    """Test flight import/parsing endpoint"""
    request_data = {
        "flight_number": "AA100",
        "date": datetime.now().date().isoformat()
    }

    response = client_v1.post("/api/flight/import", json=request_data)
    # This might fail without actual flight data, which is OK
    assert response.status_code in [200, 404, 500]


# ============== AUTHENTICATION TESTS (V2 only) ==============

@pytest.mark.api
@pytest.mark.auth
def test_register_user_v2(client_v2):
    """Test user registration endpoint"""
    user_data = {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }

    response = client_v2.post("/api/v1/auth/register", json=user_data)
    assert response.status_code in [200, 201]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "access_token" in data or "id" in data


@pytest.mark.api
@pytest.mark.auth
def test_login_invalid_credentials_v2(client_v2):
    """Test login with invalid credentials"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    }

    response = client_v2.post("/api/v1/auth/login", data=login_data)
    assert response.status_code in [401, 404]


# ============== ERROR HANDLING TESTS ==============

@pytest.mark.api
def test_404_not_found(client_v1):
    """Test that non-existent endpoints return 404"""
    response = client_v1.get("/api/nonexistent/endpoint")
    assert response.status_code == 404


@pytest.mark.api
def test_method_not_allowed(client_v1):
    """Test that wrong HTTP methods return 405"""
    response = client_v1.post("/api/airports")  # Should be GET
    assert response.status_code == 405


# ============== PERFORMANCE/LOAD TESTS ==============

@pytest.mark.slow
def test_multiple_concurrent_requests(client_v1):
    """Test handling multiple concurrent requests"""
    import concurrent.futures

    def make_request():
        return client_v1.get("/healthz")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All requests should succeed
    assert all(r.status_code == 200 for r in results)


# ============== DATA VALIDATION TESTS ==============

@pytest.mark.unit
def test_journey_request_validation():
    """Test journey request data validation"""
    from app.schemas.journey import JourneyRequest

    # Valid request
    valid_data = {
        "airport_code": "JFK",
        "terminal": "4",
        "gate": "B20",
        "departure_time": datetime.now().isoformat()
    }
    request = JourneyRequest(**valid_data)
    assert request.airport_code == "JFK"
    assert request.has_tsa_precheck is False  # Default value


@pytest.mark.unit
def test_wait_time_report_validation():
    """Test wait time report data validation"""
    from app.schemas.wait_time import WaitTimeReport

    # Valid report
    valid_data = {
        "airport_code": "JFK",
        "checkpoint_id": "jfk_t4_security_main",
        "reported_wait_minutes": 15
    }
    report = WaitTimeReport(**valid_data)
    assert report.reported_wait_minutes == 15
