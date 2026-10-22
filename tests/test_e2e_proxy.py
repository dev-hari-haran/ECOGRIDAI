"""
tests/test_e2e_proxy.py - End-to-end verification through the live Vite proxy
"""

import json
import urllib.request

VITE_URL = "http://127.0.0.1:5173"


def get_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())


def post_json(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())


def main():
    print(">>> 1. Testing /api/health through Vite proxy...")
    s, d = get_json(f"{VITE_URL}/api/health")
    assert s == 200
    print(f"    Health Status: {d['status']}, Models: {d['models']}, System: {d['system']}")

    print(">>> 2. Testing /api/network...")
    s, net = get_json(f"{VITE_URL}/api/network")
    assert s == 200
    assert net["total_buses"] == 33
    assert net["total_branches"] == 32
    print(f"    Total Buses: {net['total_buses']}, Branches: {net['total_branches']}, Base Load: {net['total_base_load_kw']} kW")
    print(f"    Bus 13 (PV): {net['buses'][12]['loss_pct']}% loss, Bus 30 (PV): {net['buses'][29]['loss_pct']}% loss")

    print(">>> 3. Testing /api/scenarios...")
    s, scs = get_json(f"{VITE_URL}/api/scenarios")
    assert s == 200
    assert len(scs) == 10
    print(f"    Scenarios Count: {len(scs)}, Scenario 2: {scs[1]['name']}")

    print(">>> 4. Testing /api/datasets...")
    s, dsets = get_json(f"{VITE_URL}/api/datasets")
    assert s == 200
    print(f"    Datasets Count: {len(dsets)}, Default Dataset: {dsets[0]['id']}")

    print(">>> 5. Testing /api/datasets/validate...")
    val_payload = {"raw_csv": "Total_Load_kW\n" + "\n".join(str(2500 + i * 10) for i in range(24))}
    s, val = post_json(f"{VITE_URL}/api/datasets/validate", val_payload)
    assert s == 200
    assert val["valid"] is True
    print(f"    Validation: valid={val['valid']}, peak={val['summary']['peak_kw']} kW")

    print(">>> 6. Testing /api/optimize (Scenario 2: Peak Summer, 40 iterations)...")
    opt_payload = {
        "dataset": "Data1.csv",
        "scenario_index": 1,
        "config": {
            "solarKw": 900,
            "windKw": 650,
            "batteryKw": 500,
            "batteryKwh": 1800,
            "gridLimitKw": 3200,
        },
        "max_iter": 40,
    }
    s, opt = post_json(f"{VITE_URL}/api/optimize", opt_payload)
    assert s == 200
    print(f"    Optimization: Scenario={opt['scenario']['name']}, Overall Winner={opt['overallWinner']}")
    print(f"    ABC Daily Cost: INR {opt['abc']['cost']:,.2f}, PSO Daily Cost: INR {opt['pso']['cost']:,.2f}")
    print(f"    ABC Unmet: {opt['abc']['unmetKwh']:.1f} kWh, PSO Unmet: {opt['pso']['unmetKwh']:.1f} kWh")
    print(f"    Cable Transmission Loss: {opt['losses']['abc_cable_transmission_loss_kwh']:.2f} kWh")
    print(f"    Convergence Iterations: ABC={opt['abc']['convergenceIterations']}, PSO={opt['pso']['convergenceIterations']}")
    print(f"    Recommendations Count: {len(opt['recommendations'])}")
    for r in opt["recommendations"]:
        print(f"     * [{r['priority']}] {r['category']}: {r['action']} ({r['additional_capacity']}, INR {r['capital_cost']:,.0f})")

    print("\n[SUCCESS] ALL END-TO-END HTTP PROXY ENDPOINTS AND REAL OPTIMIZATIONS VERIFIED!")


if __name__ == "__main__":
    main()
