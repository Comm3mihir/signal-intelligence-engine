# SIGNAL OSINT Data Sources & Entity Taxonomies

## 1. Intelligence Source Taxonomies
SIGNAL ingests external intelligence across four primary categories:
1. **Government Publications & Regulatory Announcements**: Export control lists, sanctions registries, customs notifications (e.g. BIS Entity List, MOFCOM export policy, EU Sanctions Map).
2. **Trade Data & Customs Manifests**: Port activity logs, shipping lane congestion metrics, critical mineral import volumes.
3. **Reputable News & OSINT Publishers**: Financial media, defense industry analysis, semiconductor supply chain trackers (e.g. Reuters, Bloomberg, Nikkei Asia, TrendForce).
4. **Corporate Disclosures & 10-K Filings**: Supplier financial health metrics, geographic risk declarations.

## 2. Entity Schemas
- **Organisation**: Enterprise name, industry, headquarters, key revenue segments.
- **Supplier**: Supplier name, country of operation, tier level (Tier 1, Tier 2), financial stability index.
- **Dependency**: Component/service name, dependency type (Single source, Dual source, Non-substitutable), lead time in weeks.
- **Business Process**: Process name, operational criticality (Mission critical, Core, Support), annual revenue at risk.
- **External Signal**: Title, signal type (Geopolitical, Policy/Regulatory, Tariff, Supply Chain Disruption), country, published date, raw content.
- **Evidence Snippet**: Key text excerpt, source URL, confidence rating.
