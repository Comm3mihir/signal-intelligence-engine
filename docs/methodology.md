# SIGNAL Transparent Risk Scoring Methodology

## 1. Overview
Rather than relying purely on LLM subjective judgement, SIGNAL evaluates geopolitical, regulatory, and supply-chain risks using a transparent, mathematical, and version-controlled scoring framework.

## 2. Risk Score Formula

$$\text{Risk Score} = \text{Likelihood} \times \text{Impact} \times \text{Exposure} \times \text{Dependency Weight} \times \text{Evidence Confidence}$$

Where each factor is normalized on a standard 1 to 5 scale (with Evidence Confidence between 0.2 and 1.0):

- **Likelihood ($L$, 1 to 5)**: Probability of event occurrence or enforcement within the given time horizon.
- **Impact ($I$, 1 to 5)**: Potential financial, operational, or strategic disruption to the enterprise.
- **Exposure ($E$, 1 to 5)**: Extent to which internal business processes depend on the affected region/technology.
- **Dependency Weight ($D$, 1 to 5)**: Criticality and single-source concentration of the affected supplier or component.
- **Evidence Confidence ($C$, 0.2 to 1.0)**: Reliability and verification of supporting OSINT sources.

### Raw Score & Normalized Score (0-100)
$$\text{Raw Score} = L \times I \times E \times D \times C$$
Max Raw Score = $5 \times 5 \times 5 \times 5 \times 1.0 = 625$.
$$\text{Normalized Risk Score} = \left(\frac{\text{Raw Score}}{625}\right) \times 100$$

## 3. Risk Categories
- **Critical Risk (80 - 100)**: Immediate strategic action required. High dependency on single source in high-volatility region.
- **High Risk (60 - 79)**: Significant operational exposure. Active mitigation planning required.
- **Medium Risk (35 - 59)**: Moderate exposure. Monitor signal developments and prepare backup options.
- **Low Risk (0 - 34)**: Minor exposure or high supplier redundancy.

## 4. Evidence Traceability Chain
Every risk score and finding must link back to an unbroken evidence chain:
`Finding -> Evidence Snippet -> Source Title & Type -> Publication Date -> Source URL / Document ID`
