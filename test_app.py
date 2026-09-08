import unittest
from unittest.mock import patch

import app as app_module
from app import app, index


class IndexFunctionTests(unittest.TestCase):
    """Unit tests for the index view function."""

    def test_index_renders_index_template(self):
        """index() should render the dashboard template."""
        expected_response = "rendered dashboard"

        with patch.object(
            app_module,
            "render_template",
            return_value=expected_response,
        ) as render_template_mock:
            response = index()

        render_template_mock.assert_called_once_with("index.html")
        self.assertEqual(response, expected_response)

    def test_index_returns_rendered_template_result(self):
        """index() should return the value produced by render_template."""
        expected_response = object()

        with patch.object(
            app_module,
            "render_template",
            return_value=expected_response,
        ):
            response = index()

        self.assertIs(response, expected_response)


class IndexRouteTests(unittest.TestCase):
    """Tests for the root route that invokes index()."""

    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_root_route_returns_http_200(self):
        """GET / should return a successful response."""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

    def test_root_route_returns_html(self):
        """GET / should return an HTML response."""
        response = self.client.get("/")

        self.assertTrue(response.content_type.startswith("text/html"))

    def test_root_route_contains_dashboard_title(self):
        """GET / should contain the page title."""
        response = self.client.get("/")

        self.assertIn(b"Weather Dashboard", response.data)

    def test_root_route_contains_search_form(self):
        """GET / should contain the city search form."""
        response = self.client.get("/")

        self.assertIn(b'id="weather-form"', response.data)
        self.assertIn(b'id="city-input"', response.data)
        self.assertIn(b"Get Weather", response.data)

    def test_root_route_contains_weather_results_section(self):
        """GET / should include the hidden results section."""
        response = self.client.get("/")

        self.assertIn(b'id="weather-results"', response.data)
        self.assertIn(b'id="forecast-list"', response.data)


if __name__ == "__main__":
    unittest.main()
