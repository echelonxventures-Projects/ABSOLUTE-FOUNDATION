# 01 — Execution Authorization Register

> PROGRAM **UAKOS PHASE-005** — Constitutional Implementation Execution Governance · baseline `57d91b7` (branch `governance-reconciliation`) · consumes FREEZE A+B+C+D · AUTHORITY = **NONE (DERIVED / GOVERNANCE)** · **READ-ONLY** · generated `2026-07-23T06:26:34Z` by `phase5_gov.py`.
>
> Exactly one Execution Authorization per implementation unit: WHO, WHEN, prerequisites, approval + validation + certification gates, rollback.
>
> Reproduce: `python3 00-MASTER/UAKOS-PHASE-005/phase5_gov.py`.

- Execution authorizations issued: **186** (1:1 with implementation units)
- Authorizations gated by GOVERNANCE-RELEASE (deferred): **20**

| Auth | Unit | Knowledge object | Wave | Authorized executor | Approval gates | Cert gates |
|---|---|---|---|---|---|---|
| EA-0001 | IU-0001 | CEP-003 | 2 | Constitutional Governance Authority | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0002 | IU-0002 | CEP-009 | 2 | Constitutional Governance Authority | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0003 | IU-0003 | CEP-010 | 2 | Constitutional Governance Authority | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0004 | IU-0004 | GOV-007 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0005 | IU-0005 | GOV-008 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0006 | IU-0006 | GOV-009 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0007 | IU-0007 | GOV-010 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0008 | IU-0008 | Ω∞-001 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0009 | IU-0009 | Ω∞-002 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0010 | IU-0010 | Ω∞-003 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0011 | IU-0011 | Ω∞-004 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0012 | IU-0012 | Ω∞-005 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0013 | IU-0013 | Ω∞-006 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0014 | IU-0014 | Ω∞-007 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0015 | IU-0015 | Ω∞-008 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0016 | IU-0016 | Ω∞-009 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0017 | IU-0017 | Ω∞-010 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0018 | IU-0018 | Ω∞-011 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0019 | IU-0019 | Ω∞-012 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0020 | IU-0020 | Ω∞-013 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0021 | IU-0021 | Ω∞-014 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0022 | IU-0022 | Ω∞-015 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0023 | IU-0023 | Ω∞-016 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0024 | IU-0024 | Ω∞-017 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0025 | IU-0025 | Ω∞-018 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0026 | IU-0026 | Ω∞-019 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0027 | IU-0027 | Ω∞-020 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0028 | IU-0028 | UCOS-COMP-001000 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0029 | IU-0029 | UCOS-COMP-001010 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0030 | IU-0030 | UCOS-COMP-009010 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0031 | IU-0031 | UCOS-GOV-000 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0032 | IU-0032 | UCOS-GOV-001 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0033 | IU-0033 | UCOS-GOV-003 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0034 | IU-0034 | UCOS-GOV-005 | 2 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0035 | IU-0035 | CEP-002 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0036 | IU-0036 | GOV-002 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0037 | IU-0037 | GOV-003 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0038 | IU-0038 | GOV-004 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0039 | IU-0039 | GOV-005 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0040 | IU-0040 | GOV-006 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0041 | IU-0041 | Ω∞-000 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0042 | IU-0042 | DMR-10 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0043 | IU-0043 | DMR-12 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0044 | IU-0044 | ICAP-02 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0045 | IU-0045 | ICAP-05 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0046 | IU-0046 | ICMP-05 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0047 | IU-0047 | ICNW-05 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0048 | IU-0048 | ISTO-05 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0049 | IU-0049 | UCOS-COMP-000000 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0050 | IU-0050 | UCOS-COMP-000001 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0051 | IU-0051 | UCOS-GOV-002 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0052 | IU-0052 | UCOS-GOV-004 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0053 | IU-0053 | UCOS-GOV-006 | 3 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0054 | IU-0054 | EPIC-DOC-002 | 4 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0055 | IU-0055 | EPIC-DOC-003 | 4 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0056 | IU-0056 | EPIC-PLAT-003 | 4 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0057 | IU-0057 | EPIC-RTE-002 | 4 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0058 | IU-0058 | EPIC-RTE-003 | 4 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0059 | IU-0059 | EPIC-UKDA-002 | 4 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0060 | IU-0060 | EPIC-UKDA-004 | 4 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0061 | IU-0061 | EPIC-VAL-003 | 4 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0062 | IU-0062 | APPLICATION-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0063 | IU-0063 | APPLICATION-002 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0064 | IU-0064 | APPLICATION-015 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0065 | IU-0065 | APPLICATION-017 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0066 | IU-0066 | APPLICATION-019 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0067 | IU-0067 | APPLICATION-020 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0068 | IU-0068 | ARCH-AI-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0069 | IU-0069 | ARCH-API-001 | 5 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0070 | IU-0070 | ARCH-BCDR-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0071 | IU-0071 | ARCH-CERT-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0072 | IU-0072 | ARCH-EVENT-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0073 | IU-0073 | ARCH-GAP-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0074 | IU-0074 | ARCH-INFRA-001 | 5 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0075 | IU-0075 | ARCH-INTEGRATION-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0076 | IU-0076 | ARCH-MASTER-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0077 | IU-0077 | ARCH-OBS-001 | 5 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0078 | IU-0078 | ARCH-OPS-001 | 5 | Constitutional Governance Authority | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0079 | IU-0079 | ARCH-QUALITY-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0080 | IU-0080 | ARCH-RUNTIME-001 | 5 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0081 | IU-0081 | ARCH-TEST-001 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0082 | IU-0082 | ARCH-WORKFLOW-001 | 5 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0083 | IU-0083 | ARCH-XXX-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0084 | IU-0084 | DATA-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0085 | IU-0085 | DATA-002 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0086 | IU-0086 | DATA-027 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0087 | IU-0087 | EPIC-XXX-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0088 | IU-0088 | INFRASTRUCTURE-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0089 | IU-0089 | INFRASTRUCTURE-002 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0090 | IU-0090 | INFRASTRUCTURE-004 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0091 | IU-0091 | PLATFORM-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0092 | IU-0092 | PLATFORM-002 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0093 | IU-0093 | PLATFORM-003 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0094 | IU-0094 | PLATFORM-004 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0095 | IU-0095 | PLATFORM-005 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0096 | IU-0096 | PLATFORM-007 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0097 | IU-0097 | PLATFORM-013 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0098 | IU-0098 | PLATFORM-014 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0099 | IU-0099 | PLATFORM-015 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0100 | IU-0100 | PLATFORM-016 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0101 | IU-0101 | PLATFORM-017 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0102 | IU-0102 | PLATFORM-018 | 5 | Certified Implementation Engine (EC-1) | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0103 | IU-0103 | RUNTIME-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0104 | IU-0104 | RUNTIME-001 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0105 | IU-0105 | RUNTIME-002 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0106 | IU-0106 | RUNTIME-003 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0107 | IU-0107 | RUNTIME-004 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0108 | IU-0108 | RUNTIME-005 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0109 | IU-0109 | RUNTIME-011 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0110 | IU-0110 | RUNTIME-014 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0111 | IU-0111 | RUNTIME-020 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0112 | IU-0112 | SERVICE-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0113 | IU-0113 | SERVICE-017 | 5 | Certified Implementation Engine (EC-1) | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0114 | IU-0114 | UCOS-EXEC-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0115 | IU-0115 | UCOS-RAT-000 | 5 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0116 | IU-0116 | UCOS-RAT-001 | 5 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0117 | IU-0117 | APPLICATION-016 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0118 | IU-0118 | APPLICATION-018 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0119 | IU-0119 | ARCH-GOV-001 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0120 | IU-0120 | ARCH-SECURITY-001 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0121 | IU-0121 | DATA-003 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0122 | IU-0122 | DATA-004 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0123 | IU-0123 | DATA-015 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0124 | IU-0124 | DATA-018 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0125 | IU-0125 | EPIC-VAL-002 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0126 | IU-0126 | INFRASTRUCTURE-015 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0127 | IU-0127 | INFRASTRUCTURE-017 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0128 | IU-0128 | INFRASTRUCTURE-018 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0129 | IU-0129 | PLATFORM-001 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0130 | IU-0130 | PLATFORM-008 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0131 | IU-0131 | PLATFORM-011 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0132 | IU-0132 | RUNTIME-012 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0133 | IU-0133 | RUNTIME-013 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0134 | IU-0134 | SERVICE-002 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0135 | IU-0135 | SERVICE-016 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0136 | IU-0136 | SERVICE-018 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0137 | IU-0137 | UCOS-EXEC-001 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0138 | IU-0138 | UCOS-EXEC-002 | 6 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0139 | IU-0139 | UCKO-ANTI-0001 | 7 | Knowledge Authority | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0140 | IU-0140 | UCKO-CONV-0001 | 7 | Knowledge Authority | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0141 | IU-0141 | UCKO-DEC-0001 | 7 | Knowledge Authority | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0142 | IU-0142 | UCKO-PAT-0001 | 7 | Knowledge Authority | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0143 | IU-0143 | UCKO-PRIN-0004 | 7 | Knowledge Authority | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0144 | IU-0144 | UCKO-STD-0001 | 7 | Knowledge Authority | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0145 | IU-0145 | UCKO-T-0001 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0146 | IU-0146 | UCKO-T-0002 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0147 | IU-0147 | UCKO-T-0003 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0148 | IU-0148 | UCKO-T-0004 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0149 | IU-0149 | UCKO-T-0005 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0150 | IU-0150 | UCKO-T-0006 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0151 | IU-0151 | UCKO-T-0007 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0152 | IU-0152 | UCKO-T-0008 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0153 | IU-0153 | UCKO-T-0009 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0154 | IU-0154 | UCKO-T-0010 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0155 | IU-0155 | UCKO-T-0011 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0156 | IU-0156 | UCKO-T-0012 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0157 | IU-0157 | UKDA-DEC-0001 | 7 | Knowledge Authority | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0158 | IU-0158 | UKDA-DEC-0002 | 7 | Certified Implementation Engine (EC-1) | SPEC-AUTHOR-APPROVAL+TRACEABILITY- | G1+G5 |
| EA-0159 | IU-0159 | EC-3-AP-1 | 8 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0160 | IU-0160 | MCP-000 | 8 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0161 | IU-0161 | MCP-004 | 8 | Knowledge Authority | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0162 | IU-0162 | MCP-006 | 8 | Knowledge Authority | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0163 | IU-0163 | MEP-00 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0164 | IU-0164 | MEP-06 | 8 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0165 | IU-0165 | MEP-08 | 8 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0166 | IU-0166 | MEP-09 | 8 | Constitutional Governance Authority | GOVERNANCE-RELEASE+DESIGN-APPROVAL | G1+G2+G5+G6 |
| EA-0167 | IU-0167 | Phase-000 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0168 | IU-0168 | Phase-001 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0169 | IU-0169 | Phase-002 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0170 | IU-0170 | Phase-003 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0171 | IU-0171 | Phase-020 | 8 | Constitutional Governance Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0172 | IU-0172 | Phase-021 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0173 | IU-0173 | Phase-024 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0174 | IU-0174 | Phase-025 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0175 | IU-0175 | Phase-040 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0176 | IU-0176 | UCKO-XXX-000 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0177 | IU-0177 | UCOS-RECON-0000 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0178 | IU-0178 | UCOS-RECON-0001 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0179 | IU-0179 | UCOS-RECON-001 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0180 | IU-0180 | UCOS-RECON-C1 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0181 | IU-0181 | UKDA-DEC-000 | 8 | Knowledge Authority | DESIGN-APPROVAL+IMPL-APPROVAL+VALI | G1+G2+G5+G6 |
| EA-0182 | IU-0182 | UCKO-PRIN-0001 | 9 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0183 | IU-0183 | UCKO-PRIN-0002 | 9 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0184 | IU-0184 | UCKO-PRIN-0003 | 9 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0185 | IU-0185 | UCKO-PRIN-0005 | 9 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
| EA-0186 | IU-0186 | UCKO-RULE-0001 | 9 | Constitutional Completeness Engine (CCE) + Certification Authority | EVIDENCE-APPROVAL+CERTIFICATION-AP | G5+G6+G8 |
