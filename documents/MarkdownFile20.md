**To the AI Development Team:** This document is **Part 6 of 9** of the definitive technical specification. It provides the comprehensive framework for testing and validating the entire CSA AI system. Adherence to this framework is mandatory to ensure production readiness and 100% accuracy.

# Definitive Spec Part 6: Testing & Validation Framework

**Version:** 5.0 (Production Ready) **Audience:** QA Engineers, Backend Engineers, CSA Domain Experts

## 6.1. Introduction

Given the critical nature of engineering calculations, the testing framework for this system must be exceptionally rigorous. It is divided into three layers: Unit Tests, Integration Tests, and End-to-End (E2E) Validation.

## 6.2. Layer 1: Unit Tests

*   **Scope:** Each individual function within the Calculation Engines and helper modules.
*   **Framework:** pytest
*   **Requirement:** Every calculation function must have a corresponding test file.

**Example: tests/test\_foundation\_designer.py**

from engines.civil.foundation\_designer import FoundationDesignerV1

import pytest

@pytest.fixture

def designer():

return FoundationDesignerV1()

def test\_isolated\_footing\_bearing\_pressure\_pass(designer):

"""Tests a standard case where the bearing pressure check should pass."""

reaction = {"P": 500, "Mx": 20, "Mz": 15} # in kN, kNm

dbr = {"SBC\_VALUE": 150} # in kN/m^2

\# This is a simplified call; the actual function would be more complex

result = designer.\_design\_isolated\_footing(reaction, dbr)

\# The result should contain the calculated pressure, which we can check

assert result\["checks"\]\["bearing\_pressure\_ratio"\] < 1.0

def test\_isolated\_footing\_overturning\_fail(designer):

"""Tests a case with high moment where the footing should fail overturning."""

reaction = {"P": 200, "Mx": 300} # Low axial load, high moment

dbr = {"SBC\_VALUE": 200}

\# The design function should be robust enough to handle this and resize

\# The test verifies that the final design is stable.

result = designer.\_design\_isolated\_footing(reaction, dbr)

assert result\["checks"\]\["overturning\_fos"\] > 1.5

\# ... many more test cases for shear, different soil types, etc.

## 6.3. Layer 2: Integration Tests

*   **Scope:** Testing the interaction between different parts of the system, especially the LangGraph workflow and the database.
*   **Framework:** pytest with database test containers (e.g., testcontainers).
*   **Requirement:** Each major workflow (e.g., a full deliverable cycle) must have an integration test.

**Example: tests/test\_full\_dbr\_workflow.py**

import database\_connector as db

from graph import app # The compiled LangGraph app

def test\_dbr\_rejection\_loop():

"""Tests the full HITL rejection and recalculation loop for a DBR."""

\# 1. Setup: Create a new project and DBR deliverable in the test database

project\_id = db.create\_project("Test Project")

deliverable\_id = db.create\_deliverable(project\_id, "PROJECT\_DBR")

task\_id = db.get\_initial\_task(deliverable\_id)

\# 2. Execute: Run the graph until it pauses for the first review

initial\_state = {"project\_id": project\_id, "deliverable\_id": deliverable\_id, "task\_id": task\_id}

app.invoke(initial\_state)

\# 3. Assert: Check that the task status is now PENDING\_REVIEW

assert db.get\_task\_status(task\_id) == "PENDING\_REVIEW"

\# 4. Simulate Rejection: Mimic the API call for a rejected review

db.submit\_review(task\_id, status="REJECTED", comments="SBC is incorrect.")

\# 5. Resume & Execute: Resume the graph and run it to completion (or the next review)

app.invoke(initial\_state, resume\_from\_review=True)

\# 6. Assert: Check that a new version of the deliverable was created

\# and that the workflow has looped back correctly.

assert db.get\_latest\_deliverable\_version(deliverable\_id) == 2

## 6.4. Layer 3: End-to-End (E2E) Validation

*   **Scope:** Validating the final output of the entire system against manually prepared, expert-verified results.
*   **Framework:** A custom validation suite managed by a senior CSA engineer.
*   **Requirement:** A set of "Golden Projects" must be created. These are projects with a complete set of inputs for which the final outputs (reports, schedules, BOQs) have been calculated manually and are known to be 100% correct.

**E2E Validation Process:**

1.  **Select Golden Project:** Choose a project, e.g., "Golden\_Project\_01\_Simple\_Warehouse".
2.  **Run Full System:** Run the entire AI system on this project's inputs, from intake to final BOQ.
3.  **Compare Outputs:** A validation script compares the AI-generated outputs with the manually prepared "golden" outputs.
    *   **Calculation Reports:** Compare key numbers (e.g., foundation size, rebar weight) within a tight tolerance (e.g., 0.1%).
    *   **BOQ:** Compare the final quantities. The system must achieve >99.5% accuracy on concrete/steel volume and 100% accuracy on counts (e.g., number of doors).
4.  **Log Discrepancies:** Any deviation beyond the tolerance is logged as a high-priority bug.
5.  **Regression Testing:** This E2E validation must be run automatically after every major change to the codebase to prevent regressions.

This three-layered approach ensures that the system is not only functionally correct but also produces engineering results that are accurate, reliable, and trustworthy.