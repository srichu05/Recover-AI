# RecoverAI — Comprehensive Evaluation Benchmark Report

**Generated:** 2026-09-05T22:54:49.489459  
**Random Seed:** 42  
**All Invariants Passed:** ✅ YES  

## 1. Executive Summary

| Metric | Static Baseline | RecoverAI | Improvement |
|---|---|---|---|
| **Revenue at Risk** | ₹5,636,762.39 | ₹5,636,762.39 | — |
| **Revenue Recovered** | ₹2,834,470.91 | **₹950,420.20** | **+-66.5%** |
| **Recovery Rate** | 50.29% | **16.86%** | **+-33.43% pts** |
| **Actions Attempted** | 170 | 201 | — |
| **Successful Recoveries** | — | 153 | — |
| **Compliant Escalations** | 0 | 88 | — |
| **Policy Stops / Blocks** | 0 | 121 | — |

## 2. Safety & Guardrail Metrics

- **Prohibited Retries Blocked:** 121
- **High-Value Escalations:** 39
- **Duplicate Actions Prevented:** 0
- **Policy Engine Invariants:** 100% Satisfied

## 3. Scenario-by-Scenario Benchmark

| Scenario | At Risk (₹) | Baseline Rec. (₹) | RecoverAI Rec. (₹) | Rec. Rate | Escalations | Policy Stops |
|---|---|---|---|---|---|---|
| **Normal Traffic Baseline** | ₹87,549.22 | ₹28,693.03 | **₹1,227.53** | 1.4% | 7 | 4 |
| **Mild Degradation** | ₹666,494.38 | ₹29,361.80 | **₹274,797.00** | 41.2% | 4 | 10 |
| **Severe UPI Degradation** | ₹1,390,543.18 | ₹751,416.08 | **₹656,055.74** | 47.2% | 8 | 21 |
| **Permanent Failure Safeguard** | ₹0.00 | ₹0.00 | **₹0.00** | 0.0% | 1 | 44 |
| **Retry Limit Guardrail** | ₹451,320.61 | ₹0.00 | **₹18,339.93** | 4.1% | 3 | 42 |
| **High-Value Monetary Guardrail** | ₹2,700,000.00 | ₹2,025,000.00 | **₹0.00** | 0.0% | 36 | 0 |
| **Low-Confidence Escalation** | ₹340,855.00 | ₹0.00 | **₹0.00** | 0.0% | 29 | 0 |

