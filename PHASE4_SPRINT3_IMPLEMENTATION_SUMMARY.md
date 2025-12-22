# Phase 4 Sprint 3: The "What-If" Cost Engine (The Simulator)

## Overview

Sprint 4.3 implements a comparative cost engine that allows engineers to toggle design variables and see immediate cost and time impacts. The system creates "what-if" scenarios, generates Bills of Quantities (BOQ), estimates costs with complexity factors, and provides trade-off analysis.

## Key Deliverables

### 1. Parametric Linkage System
Design variables are directly linked to BOQ generation:
- **Concrete Grade** (M20-M50) → Material cost per m³
- **Steel Grade** (Fe415/500/550) → Reinforcement cost per kg
- **Beam Dimensions** → Formwork area and labor hours
- **Design Optimization Level** → Section sizes and material quantities

### 2. Scenario Comparison Logic
Two built-in comparison templates:
- **High-Strength vs Standard Concrete**: M50+Fe550 with smaller sections vs M30+Fe500 with larger sections
- **Fast-Track vs Economical**: Modular formwork with standard dims vs custom formwork with optimized dims

### 3. Total Cost Calculation
Cost estimation integrates:
- **Material costs** from SKG cost database (Sprint 4.1)
- **Labor costs** adjusted by complexity multipliers
- **Equipment costs** based on duration
- **Complexity factors** from Constructability Agent (Sprint 4.2):
  - Formwork complexity: 1.0x (Standard) to 2.0x (Highly Complex)
  - Congestion factor: 1.0x (Low) to 1.5x (Critical)
  - Labor efficiency adjustments

## Implementation Details

### Database Schema (`init_phase4_sprint3.sql`)

**New Tables:**
| Table | Purpose |
|-------|---------|
| `design_scenarios` | Store scenarios with design variables, outputs, and costs |
| `scenario_comparison_groups` | Group scenarios for comparison |
| `boq_items` | Bill of Quantities items linked to scenarios |
| `cost_estimation_history` | Historical cost estimates with versioning |
| `scenario_comparisons` | Comparison results with trade-off analysis |
| `scenario_templates` | Predefined templates for common comparisons |

**Key Functions:**
- `calculate_scenario_total_cost()` - Aggregate costs by category
- `compare_scenarios()` - Compare two scenarios across metrics
- `get_scenario_summary()` - Get scenario overview
- `get_boq_summary()` - BOQ breakdown by category

### Backend Components

**Cost Engines (`backend/app/engines/cost/`):**
- `boq_generator.py` - Generates BOQ from design outputs with parametric linkage
- `cost_estimator.py` - Estimates costs with complexity multipliers
- `duration_estimator.py` - Estimates construction duration based on productivity rates

**Scenario Service (`backend/app/services/scenario/scenario_service.py`):**
- Creates scenarios from templates or custom variables
- Runs design engine for each scenario
- Generates BOQ and estimates costs/duration
- Compares scenarios with trade-off analysis

**API Routes (`backend/app/api/scenario_routes.py`):**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scenarios/templates` | GET | List available templates |
| `/scenarios/from-template` | POST | Create scenarios from template |
| `/scenarios/` | POST | Create single scenario |
| `/scenarios/{id}` | GET | Get scenario details |
| `/scenarios/{id}/boq` | GET | Get scenario BOQ |
| `/scenarios/compare` | POST | Compare two scenarios |
| `/scenarios/quick-compare` | POST | Quick comparison without template |

### Frontend Components

**Scenario Comparison Dashboard (`frontend/src/pages/ScenarioComparisonPage.jsx`):**
- Template selection UI
- Base design parameters form (span, loads, support type)
- Side-by-side scenario comparison cards
- Trade-off analysis visualization
- Detailed metrics table with winner indicators

**API Service (`frontend/src/services/scenarioService.js`):**
- Template operations
- Scenario CRUD operations
- Comparison operations
- Utility functions for formatting

## Trade-off Analysis Logic

The system calculates cost vs. time trade-offs:

1. **Same Direction**: If one scenario is both cheaper AND faster, it's the clear winner
2. **Cost per Day Saved**: When time savings cost extra money:
   - < ₹3,000/day: Good value for acceleration
   - ₹3,000-8,000/day: Consider project urgency
   - > ₹8,000/day: Expensive acceleration
3. **Daily Savings Threshold**: When cost savings add time:
   - > ₹5,000/day saved: Worth the extra time
   - < ₹5,000/day saved: Time premium may not justify savings

## Complexity Integration

The system integrates Sprint 4.2 complexity scores:

```python
# Formwork complexity affects material and labor costs
FORMWORK_COST_MULTIPLIERS = {
    "STANDARD": 1.0,
    "MODERATE": 1.15,    # 15% increase
    "COMPLEX": 1.40,     # 40% increase
    "HIGHLY_COMPLEX": 2.0 # 100% increase
}

# Duration factors
LABOR_MULTIPLIERS = {
    "STANDARD": 1.0,
    "MODERATE": 1.20,
    "COMPLEX": 1.60,
    "HIGHLY_COMPLEX": 2.5
}
```

## Example Comparison Output

```json
{
  "comparison_id": "CMP-ABC123",
  "scenario_a": {
    "name": "High-Strength (M50)",
    "total_cost": 125000,
    "duration_days": 18,
    "concrete_volume": 1.2,
    "steel_weight": 180
  },
  "scenario_b": {
    "name": "Standard (M30)",
    "total_cost": 98000,
    "duration_days": 22,
    "concrete_volume": 1.5,
    "steel_weight": 210
  },
  "trade_off": {
    "cost_difference": -27000,
    "time_difference_days": 4,
    "cost_per_day_saved": 6750,
    "recommendation": "Scenario A is faster by 4 days at ₹6,750/day - good value for urgent projects"
  }
}
```

## File Structure

```
backend/
├── init_phase4_sprint3.sql              # Database schema
├── app/
│   ├── schemas/scenario/
│   │   ├── __init__.py
│   │   └── models.py                    # Pydantic models
│   ├── engines/cost/
│   │   ├── __init__.py
│   │   ├── boq_generator.py             # BOQ generation
│   │   ├── cost_estimator.py            # Cost estimation
│   │   └── duration_estimator.py        # Duration estimation
│   ├── services/scenario/
│   │   ├── __init__.py
│   │   └── scenario_service.py          # Main service
│   └── api/
│       └── scenario_routes.py           # API endpoints

frontend/src/
├── services/
│   └── scenarioService.js               # API client
├── pages/
│   └── ScenarioComparisonPage.jsx       # Dashboard UI
└── components/
    └── Layout.jsx                       # Updated navigation
```

## Usage

### Running a What-If Comparison

1. Navigate to "What-If Costs" in the sidebar
2. Select a comparison template (e.g., "High-Strength vs Standard")
3. Enter base design parameters (span, loads, etc.)
4. Click "Run Comparison"
5. View side-by-side results with trade-off recommendations

### API Example

```python
# Create scenarios from template
response = requests.post(
    "http://localhost:8000/scenarios/from-template",
    json={
        "template_id": "beam-high-strength-vs-standard",
        "base_input": {
            "span_length": 6.0,
            "dead_load_udl": 15.0,
            "live_load_udl": 10.0,
            "beam_width": 0.30
        },
        "created_by": "engineer1"
    }
)

result = response.json()
comparison = result["comparison"]
print(f"Winner: {comparison['overall_winner']}")
print(f"Recommendation: {comparison['trade_off']['recommendation']}")
```

## Testing

```bash
# Run backend
cd backend && source venv/bin/activate
python main.py

# In another terminal, run frontend
cd frontend && npm run dev

# Test API
curl http://localhost:8000/scenarios/templates
```

## Next Steps (Sprint 4.4)

1. Add more scenario templates (foundation, column, slab)
2. Integrate with project management for budget tracking
3. Add historical cost data learning
4. Export comparison reports to PDF
5. Multi-scenario comparison (more than 2 at a time)

## Dependencies

- Sprint 4.1: Cost database from Strategic Knowledge Graph
- Sprint 4.2: Complexity scores from Constructability Agent
- Phase 3: Beam designer engine for scenario computation
