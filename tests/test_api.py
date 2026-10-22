"""
tests/test_api.py - Verification Test Suite for EcoGridAI FastAPI Backend
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from api.app import app
from api.serializers import sanitize_for_json

client = TestClient(app)


def test_sanitize_for_json():
    data = {
        "int": np.int64(42),
        "float": np.float64(3.1415),
        "nan": float("nan"),
        "inf": float("inf"),
        "array": np.array([1.0, 2.0, 3.0]),
        "nested": {"val": np.float32(10.5)},
    }
    sanitized = sanitize_for_json(data)
    assert sanitized["int"] == 42
    assert sanitized["float"] == pytest.approx(3.1415)
    assert sanitized["nan"] == 0.0
    assert sanitized["inf"] == 0.0
    assert sanitized["array"] == [1.0, 2.0, 3.0]
    assert sanitized["nested"]["val"] == pytest.approx(10.5)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "ABC" in data["models"]
    assert "PSO" in data["models"]
    assert data["datasets"]["Data1.csv"] is True


def test_network_endpoint():
    res = client.get("/api/network")
    assert res.status_code == 200
    data = res.json()
    assert data["total_buses"] == 33
    assert len(data["buses"]) == 33
    assert len(data["branches"]) == 32
    assert data["root_bus"] == 1
    # Check bus 13 has PV and bus 6 has Wind
    bus13 = next(b for b in data["buses"] if b["id"] == 13)
    assert "solar" in bus13["resources"]
    assert bus13["loss_factor"] > 1.0
    bus6 = next(b for b in data["buses"] if b["id"] == 6)
    assert "wind" in bus6["resources"]


def test_datasets_endpoint():
    res = client.get("/api/datasets")
    assert res.status_code == 200
    datasets = res.json()
    ids = [d["id"] for d in datasets]
    assert "Data1.csv" in ids
    data1 = next(d for d in datasets if d["id"] == "Data1.csv")
    assert data1["hours"] == 24
    assert data1["peak_load_kw"] > 1000.0


def test_validate_dataset_endpoint():
    valid_csv = "Total_Load_kW\n" + "\n".join([str(2000 + i * 10) for i in range(24)])
    res = client.post("/api/datasets/validate", data={"raw_csv": valid_csv})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["summary"]["hours"] == 24
    assert data["summary"]["peak_kw"] > 2000.0

    # Negative test case
    invalid_csv = "Unknown_Column\n" + "\n".join([str(10) for i in range(5)])
    res_bad = client.post("/api/datasets/validate", data={"raw_csv": invalid_csv})
    assert res_bad.status_code == 200
    assert res_bad.json()["valid"] is False
    assert len(res_bad.json()["errors"]) > 0


def test_scenarios_endpoint():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    scs = res.json()
    assert len(scs) == 10
    names = [s["name"] for s in scs]
    assert "Normal Operation" in names
    assert "Grid Outage" in names
    assert "Battery Failure" in names


def test_optimize_sync_endpoint():
    payload = {
        "dataset": "Data1.csv",
        "scenario_index": 0,
        "config": {
            "solarKw": 900,
            "windKw": 650,
            "batteryKw": 500,
            "batteryKwh": 1800,
            "gridLimitKw": 3200,
        },
        "use_entropy_weights": True,
        "max_iter": 15,
        "async_job": False,
    }
    res = client.post("/api/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"]["name"] == "Normal Operation"
    assert "abc" in data
    assert "pso" in data
    assert len(data["abc"]["dispatch"]) == 24
    assert len(data["pso"]["dispatch"]) == 24
    assert len(data["abc"]["convergence"]) == 15
    assert data["abc"]["cost"] > 0
    assert data["pso"]["cost"] > 0
    assert "losses" in data
    assert "feasibility" in data
    assert "recommendations" in data


def test_optimize_async_job_endpoint():
    payload = {
        "dataset": "Data1.csv",
        "scenario_index": 0,
        "config": {
            "solarKw": 900,
            "windKw": 650,
            "batteryKw": 500,
            "batteryKwh": 1800,
            "gridLimitKw": 3200,
        },
        "max_iter": 15,
        "async_job": True,
    }
    res = client.post("/api/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Poll job result
    res_poll = client.get(f"/api/results/{job_id}")
    assert res_poll.status_code == 200
    poll_data = res_poll.json()
    assert poll_data["status"] in ["running", "complete"]


def test_recommendations_endpoint():
    payload = {
        "scenario_name": "Peak Summer",
        "scenario_index": 1,
        "unmet_kwh": 450.0,
        "peak_gap_kw": 250.0,
        "load_satisfaction": 94.2,
        "grid_available": True,
    }
    res = client.post("/api/recommendations", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "gap_analysis" in data
    assert len(data["recommendations"]) > 0
    assert any("PV" in r["category"] or "Solar" in r["category"] for r in data["recommendations"])
