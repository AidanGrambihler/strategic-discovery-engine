# Data Registry & Technical Schema

This directory contains the raw data files retrieved from the [Seattle Open Data Portal](https://data.seattle.gov/) on **January 22, 2026**, supplemented with municipal geospatial boundaries.

## 🏗️ Anchor Data: Public Life (SDOT)
*Agency: Seattle Department of Transportation (SDOT)*

| Local Filename | Official Dataset Name | Data Last Updated | Metadata Last Updated | Key Function |
| :--- | :--- | :--- | :--- | :--- |
| `study.csv` | [Public Life Data - Study](https://data.seattle.gov/Community-and-Culture/Public-Life-Data-Study/7qru-sdcp/) | Feb 6, 2023 | Jan 28, 2025 | Metadata on specific study projects. |
| `locations.csv` | [Public Life Data - Locations](https://data.seattle.gov/Community-and-Culture/Public-Life-Data-Locations/fg6z-cn3y/) | Feb 6, 2023 | Jan 28, 2025 | Attributes for site comparisons (e.g. street blocks). |
| `geography.csv` | [Public Life Data - Geography](https://data.seattle.gov/Community-and-Culture/Public-Life-Data-Geography/v4q3-5hvp/) | Feb 6, 2023 | Jan 29, 2025 | GIS polygons/boundaries for sites. |
| `moving.csv` | [Public Life Data - People Moving](https://data.seattle.gov/Community-and-Culture/Public-Life-Data-People-Moving/7rx6-5pgd/) | Feb 15, 2023 | Jan 28, 2025 | Foot traffic and demographic counts. |
| `staying.csv` | [Public Life Data - People Staying](https://data.seattle.gov/Community-and-Culture/Public-Life-Data-People-Staying/5mzj-4rtf/) | Mar 5, 2024 | Jan 28, 2025 | **Primary Dependent Variable (DSR) Source.** |

> **Note on `staying.csv`:** This project prioritizes "staying" data (20-minute intervals) over "moving" data because it captures intentional use of space, including temperature, group size, and specific activities like **talking_to_others** vs. **using_electronics**.

## 🌐 Supplemental Data: Digital Equity (IT)
*Agency: Seattle Information Technology - Digital Equity Team*

| Local Filename | Official Dataset Name | Data Last Updated | Metadata Last Updated | Key Function |
| :--- | :--- | :--- | :--- | :--- |
| `tech_survey_2018.csv` | [Technology Access and Adoption 2018](https://data.seattle.gov/Community-and-Culture/Technology-Access-and-Adoption-Survey-2018/cz6d-tu92/) | Nov 15, 2018 | Jan 28, 2025 | Baseline (Pre-Pandemic) metrics. |
| `tech_survey_2023.csv` | [Technology Access and Adoption 2023](https://data.seattle.gov/Community-and-Culture/Technology-Access-and-Adoption-Survey-2023/jddv-fz6y/) | Oct 4, 2023 | Jan 29, 2025 | Modern (Post-Pandemic) metrics. |

---

## 🛠️ Field Mappings & Standardization

### 1. Longitudinal Survey Alignment
To compare 2018 and 2023 surveys, variable schemas were mapped as follows:
* **Internet Access:** `q1` (2018) mapped to `Q1` (2023). Defined as having a home connection (Fiber, DSL, Cable, or Cellular).
* **Reliability:** `q6` (2018) mapped to `Q6` (2023). Scale: 1 (Adequate) to 5 (Not Adequate).
* **Societal Impact:** `q22_2` (2018) mapped to `q23` (2023). Scale: 1 (Positive) to 5 (Harmful).

### 2. Income Normalization (Inflation-Adjusted)
A unified 1–7 index was created to handle shifting income buckets. While numerically similar, the 2023 buckets represent a ~21.2% decrease in purchasing power relative to 2018 (based on CPI-U). 

| Unified Index | 2018 Nominal Range | 2018 in "2023 Dollars" | 2023 Survey Range | Alignment Note |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Below $25k | Below $30.2k | Less than $27k | **Tightened** (2023 is poorer) |
| **2** | $25k - $50k | $30.2k - $60.5k | $27k - $46k | **Shifted Down** |
| **3** | $50k - $75k | $60.5k - $90.7k | $46k - $74k | **Overlap** |
| **4** | $75k - $100k | $90.7k - $121k | $74k - $100k | **Shifted Down** |
| **5** | $100k - $150k| $121k - $181k | $100k - $150k| **Stable** |
| **6** | $150k - $200k| $181k - $242k | $150k - $200k| **Stable** |
| **7** | $200k+ | $242k+ | $200k+ | **Stable** |

---

## ⚖️ Methodological Assumptions & Rigor

### 📍 The Locality Assumption
A standard urban planning assumption is applied: users observed in a neighborhood plaza are likely residents of the ZIP code in which the plaza is located. Thus, residential survey data (connectivity/income) is treated as the primary environmental pressure for those users.

### 🔢 The "Small N" Rule & Bias
Per Seattle IT instructions, **"comparisons among subgroups shouldn't be made when n < 50."** * Any ZIP code with <50 survey respondents was excluded from regression models.
* Future research is required to verify if survey respondents are demographically representative of their ZIP codes (Census/ACS validation) to account for potential response bias.

### ⚖️ Unweighted Analysis
This project deliberately utilizes **unweighted raw means** at the ZIP-code level.
* **Reasoning:** SDOT observation data is unweighted "headcount" data. Weighting only the survey side would create a mathematical mismatch. Furthermore, we are interested in the raw behavioral substitution signal between neighborhoods rather than city-wide population totals.

### 🗓️ Temporal Lumping (Era Proxies)
To maximize statistical power and ensure robust alignment with the Technology Access surveys, observations are aggregated into two era-based proxies:

* **Pre-Pandemic Proxy ('2018'):** Combined observations from 2018 and 2019. 
* **Post-Pandemic Proxy ('2023'):** Combined observations from 2022 and 2023.

**Methodological Justification:** This "lumping" assumes that urban behavior and digital reliance within these two-year windows were internally consistent enough to represent their respective eras. By including 2019 and 2022 data, we significantly increase the N-size per ZIP code, which is critical for meeting the "Small N" requirement ($N \ge 50$) and improving the confidence of the final regression models.