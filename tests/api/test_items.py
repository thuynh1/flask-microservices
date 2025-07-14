import json
from http import HTTPStatus

class TestGetItemsEndpoint:
    """Test cases for GET /api/v1/items endpoint."""

    # todo - add the fixture type to client
    def test_get_items_empty_database(self, client):
        """Test getting items when database is empty."""
        response = client.get("/api/v1/items")

        assert response.status_code == HTTPStatus.OK

        data = json.loads(response.data)
        assert data['items'] == []
        assert data['pagination']['total_count'] == 0
        assert data['pagination']['page_count'] == 1
        assert data['pagination']['page'] == 1
        assert data['pagination']['size'] == 10
        assert data['pagination']['has_next'] is False
        assert data['pagination']['has_prev'] is False
        assert data['base_response']['status_message'] == ""
        assert data['base_response']['status_code'] == 0
