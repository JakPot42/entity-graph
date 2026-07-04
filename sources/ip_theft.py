"""
sources/ip_theft.py -- adapter for the IP Theft Pattern Database (DOJ economic
espionage / trade secret cases).

Transcribed from ip_theft/seed_data.py's SEED_CASES -- real DOJ press
releases and public court records. The victim company for each case is named
directly in that case's `summary` text there (there is no separate
`victim_company` field in the source project), so this adapter names each
one explicitly rather than attempting NLP extraction. See README.md's
ingestion design note for why this is a static transcription rather than a
live import.
"""
from __future__ import annotations

PROJECT_KEY = "ip_theft"
PROJECT_LABEL = "IP Theft Pattern Database -- DOJ Economic Espionage Cases"

# (victim_company, case_name, outcome, source_date, url)
_VICTIMS = [
    ("Boeing", "United States v. Dongfan 'Greg' Chung", "convicted", "2010-02-08",
     "https://www.justice.gov/opa/pr/former-boeing-engineer-convicted-economic-espionage-selling-space-shuttle-secrets-china"),
    ("Northrop Grumman", "United States v. Noshir Gowadia", "convicted", "2010-08-09",
     "https://www.justice.gov/opa/pr/engineer-convicted-communicating-classified-information-assist-people-s-republic-china"),
    ("L-3 Communications", "United States v. Chi Mak", "convicted", "2008-03-24",
     "https://www.justice.gov/opa/pr/defense-contractor-engineer-sentenced-24-years-prison-conspiring-export-us-defense-technology"),
    ("GE Aviation", "United States v. Yanjun Xu", "convicted", "2021-11-05",
     "https://www.justice.gov/opa/pr/chinese-intelligence-officer-convicted-economic-espionage-and-theft-trade-secrets"),
    ("Avago Technologies", "United States v. Hao Zhang and Wei Pang", "fugitive", "2015-05-19",
     "https://www.justice.gov/opa/pr/two-former-employees-us-semiconductor-companies-indicted-theft-trade-secrets"),
    ("Skyworks Solutions", "United States v. Hao Zhang and Wei Pang", "fugitive", "2015-05-19",
     "https://www.justice.gov/opa/pr/two-former-employees-us-semiconductor-companies-indicted-theft-trade-secrets"),
    ("Micron Technology", "United States v. United Microelectronics Corp. and Fujian Jinhua", "plea", "2020-10-28",
     "https://www.justice.gov/opa/pr/taiwan-based-company-pleads-guilty-trade-secret-theft-conspiracy"),
    ("DuPont", "United States v. Walter Liew and Robert Maegerle", "convicted", "2014-07-10",
     "https://www.justice.gov/opa/pr/california-man-sentenced-15-years-prison-conspiring-conduct-economic-espionage"),
    ("Coca-Cola", "United States v. Xiaorong You", "convicted", "2021-05-12",
     "https://www.justice.gov/opa/pr/former-coca-cola-and-east-tennessee-state-university-researcher-convicted-economic-espionage"),
    ("Eastman Chemical", "United States v. Xiaorong You", "convicted", "2021-05-12",
     "https://www.justice.gov/opa/pr/former-coca-cola-and-east-tennessee-state-university-researcher-convicted-economic-espionage"),
    ("American Superconductor", "United States v. Sinovel Wind Group Co. Ltd.", "convicted", "2018-01-24",
     "https://www.justice.gov/opa/pr/sinovel-wind-group-convicted-trade-secret-theft"),
    ("GE Power", "United States v. Xiaoqing Zheng", "convicted", "2022-03-08",
     "https://www.justice.gov/opa/pr/former-ge-engineer-convicted-economic-espionage-and-theft-ge-trade-secrets"),
    ("GlaxoSmithKline", "United States v. Yu Xue", "convicted", "2014-05-15",
     "https://www.justice.gov/opa/pr/former-glaxosmithkline-scientist-sentenced-theft-trade-secrets"),
    ("Pioneer Hi-Bred", "United States v. Mo Hailong", "convicted", "2016-02-03",
     "https://www.justice.gov/opa/pr/iowa-man-sentenced-theft-trade-secrets-involving-inbred-corn-seeds"),
    ("Monsanto", "United States v. Mo Hailong", "convicted", "2016-02-03",
     "https://www.justice.gov/opa/pr/iowa-man-sentenced-theft-trade-secrets-involving-inbred-corn-seeds"),
    ("Dow AgroSciences", "United States v. Zhengdong Cheng and Jiang Zhao", "convicted", "2015-03-05",
     "https://www.justice.gov/opa/pr/dow-agrosciences-researcher-convicted-stealing-trade-secrets"),
    ("T-Mobile", "United States v. Huawei Technologies Co. Ltd. (T-Mobile 'Tappy')", "charged", "2020-02-13",
     "https://www.justice.gov/opa/pr/chinese-telecommunications-conglomerate-huawei-and-subsidiaries-charged-racketeering"),
    ("Motorola Solutions", "United States v. Hanjuan Jin", "convicted", "2012-02-27",
     "https://www.justice.gov/opa/pr/former-motorola-solutions-engineer-convicted-theft-trade-secrets"),
]


def get_entities() -> list[dict]:
    return [
        {
            "name": victim,
            "entity_type": "company",
            "source_project": PROJECT_KEY,
            "context": f"Trade secret theft victim -- {outcome} (DOJ press release {source_date})",
            "reference": case_name,
            "url": url,
        }
        for victim, case_name, outcome, source_date, url in _VICTIMS
    ]


def get_relationships() -> list[dict]:
    return []
