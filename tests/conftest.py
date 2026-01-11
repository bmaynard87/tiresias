"""Pytest fixtures and configuration."""

import pytest


@pytest.fixture
def sample_design_doc() -> str:
    """Sample design document for testing."""
    return """
# Feature Design: User Dashboard

## Goals
Build a user dashboard to show account information.

## Scope
In scope: profile display, settings page
Out of scope: admin features

## Architecture
We will use React for the frontend and Express for the backend API.

## Success Metrics
- User engagement increases by 20%
- Page load time < 500ms

## Testing
Will write unit tests and integration tests.

## Alternatives Considered
We considered using Vue.js but chose React for team familiarity.
"""


@pytest.fixture
def sample_doc_missing_errors() -> str:
    """Sample document missing error handling."""
    return """
# Payment Service Design

## Goals
Build a payment processing service.

## Architecture
We will use a REST API with PostgreSQL database.

## Testing
We will write unit tests.
"""
