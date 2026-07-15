# Analytics Fixtures (TEST DATA ONLY)

These fixtures are **illustrative test data**. They prove validators are domain-neutral across structurally different projects without changing core skill code.

| Fixture | Structural shape | Intentionally absent |
|---|---|---|
| `domain_a_transactional` | transaction/event + entity + catalog + status | healthcare-only entities |
| `domain_b_encounter` | encounter/event + provider/location + status | product/order/SKU requirements |
| `domain_c_asset_events` | asset/sensor-like events + asset + status | customer/payment requirements |
| `domain_d_case_activity` | case/activity lifecycle + person/org + status | subscription/SKU requirements |

Rebuild and validate:

```bash
python scripts/build_analytics_fixtures.py
python -m unittest tests.test_analytics_gates -v
```
