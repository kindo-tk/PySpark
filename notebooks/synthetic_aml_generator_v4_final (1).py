"""
=============================================================================
SYNTHETIC AML DATA GENERATOR v4  —  RETAIL BANKING (US BANK)
=============================================================================
PURPOSE
  Generate synthetic Customer, Account, and Transaction data for a large
  US retail bank.  Data covers a 6-month lookback window, split as:
    Training  : first 4 months  (months 1-4)
    Testing   : last  2 months  (months 5-6)

SCALING
  Change only CFG["n_normal"] to scale everything proportionally.
    n_normal = 100_000  →  ~8 M transactions  (test/dev)
    n_normal = 500_000  →  ~40 M transactions
    n_normal = 5_000_000→  ~400 M transactions/6-months (production emulation)
  All typology customer counts and noise customer counts are computed as
  fractions of n_normal — no other values need to change.

OUTPUT
  Returns (customers_df, accounts_df, transactions_df) — no CSV writes.
  To save locally:
    customers_df.to_csv("customers.csv", index=False)
    accounts_df.to_csv("accounts.csv", index=False)
    transactions_df.to_csv("transactions.csv", index=False)

═══════════════════════════════════════════════════════════════════════════
AML TYPOLOGIES — DETAILED REFERENCE
═══════════════════════════════════════════════════════════════════════════

PATTERN 1 — China Currency-Restriction Structuring (SAFE 50k USD Cap)
  Source: FinCEN Advisory FIN-2018-A001 / China SAFE regulations
  Description:
    China's State Administration of Foreign Exchange (SAFE) caps annual
    outward remittances at USD 50,000 per individual.  Customers evade this
    by sending multiple wires just below the threshold within a 6-month window.
  Behavioural signals embedded:
    - 4-10 international wires per customer in window, each $45,000-$49,900
    - All wires to CN counterparties (family accounts or informal brokers)
    - CN nationality, US-resident, high stated income
    - Tight amount clustering (low std-dev) around $47-49k
    - Wire fees paid on every transfer
    - Aggregated CN wire total far exceeds normal customer's entire wire activity
  Detection features (post groupby):
    cn_wire_count, cn_wire_total_amt, cn_wire_amount_stddev,
    pct_txns_to_CN, max_single_wire_amt, intl_wire_ratio

PATTERN 2 — CMLN / Cartel Money Mule Network (Chinese Money Laundering Networks)
  Source: FinCEN Advisory FIN-2022-A001 (CMLN + Mexico TCOs)
  Description:
    Chinese Money Laundering Networks (CMLNs) launder drug proceeds for
    CJNG, Sinaloa Cartel, Gulf Cartel and other TCOs.  Chinese-national
    students or low-income individuals act as money mules: receive large
    inbound ACH/wire transfers (labelled "tuition" or "living expenses")
    then immediately spend on gift cards, prepaid cards, cellphones, and
    airline tickets back to China.  Shell companies are external counterparties.
  Behavioural signals embedded:
    - Student / retiree / housewife occupation with income $8k-$22k/year
    - Inbound ACH credits ($2k-$18k each, 3-8 per window) from external
      Chinese-owned US companies (counterparty_name = shell company)
    - Transaction remarks: "Tuition fee from sponsor", "Living expense support"
    - Rapid outbound spend on gift cards, prepaid cards, cellphones, airline
    - Monthly spend ratio vs declared income: 3x-7x (extreme outlier)
    - Multiple card products on a low-income student account
    - P2P transfers to unknown third parties after receiving funds
  Detection features (post groupby):
    spend_to_income_ratio, gift_card_amt, prepaid_amt, inbound_ach_count,
    inbound_ach_amt, mule_mcc_concentration, txn_velocity_post_inbound

PATTERN 3 — Rapid Movement of Funds / Layering
  Source: FATF Guidance on Money Laundering / FinCEN SAR data trends
  Description:
    Classic three-stage laundering layering step.  Large sums received
    (placement) and moved out within 24-72 hours across multiple accounts
    or counterparties (layering).  Net balance change near zero but gross
    flow is very high.  Funds may hop through 2-3 intermediary accounts.
  Behavioural signals embedded:
    - Large inbound credit ($20k-$200k) followed by multiple debits within
      48 hours consuming 80-100% of the inbound amount
    - 3-8 outbound wires/ACH within 2 days of each inbound
    - Diverse counterparty countries per cluster (US, CN, HK, AE)
    - High gross flow vs low net balance change
    - Funds-in-transit: balance spikes then rapidly returns to near-zero
    - Intermediary banks used for cross-border hops
  Detection features (post groupby):
    max_single_day_inflow, churn_ratio (outflow/inflow within 48h),
    unique_counterparty_countries, gross_flow_vs_net_balance,
    rapid_succession_txn_count

PATTERN 4 — Domestic Cash Structuring (Smurfing)
  Source: 31 U.S.C. § 5324 / FinCEN Currency Transaction Report rules
  Description:
    Multiple cash deposits below the $10,000 Currency Transaction Report
    (CTR) threshold, made at different branches or ATMs, to avoid regulatory
    reporting.  May involve multiple individuals (smurfs) depositing on
    behalf of one beneficiary.  Purely domestic USD cash — distinct from
    Pattern 1 (international wire structuring).
  Behavioural signals embedded:
    - 5-12 cash deposits per customer per month, each $7,000-$9,800
    - Deposits at multiple branch codes (geographic spread)
    - All deposits within a 30-day rolling window (dense clustering)
    - No corresponding payroll or regular income credits
    - Deposits followed by single large consolidating outward transfer
    - Transaction remarks: "Cash deposit - personal savings",
      "Business cash proceeds", "Cash deposit - contractor payment"
  Detection features (post groupby):
    cash_deposit_count, cash_deposit_total, avg_cash_deposit_amt,
    branch_diversity_count, cash_to_wire_ratio, sub_ctr_flag_count

PATTERN 5 — Russian Oligarch / Sanctions Evasion
  Source: FinCEN Alert FIN-2022-Alert001 (Russian Elites and Oligarchs)
  Description:
    Prior to and after OFAC designations (Feb-Mar 2022 analog), Russian
    oligarchs and their family members accelerated purchases of luxury goods
    and real estate, transferred assets to family members, and routed funds
    through Swiss and UAE-based intermediaries.
  Behavioural signals embedded:
    - RU/BY/KZ nationality; HNI customer category; high declared income
    - Inbound credit card payments from Swiss bank accounts (UBSWCHZH,
      CRESCHZZ) that spike sharply in months 5-6 of window (pre-sanction analog)
    - Large wire transfers ($500k-$2.5M) to UAE-based real estate companies
      with remarks: "Purchase and sale of residential premises in UAE",
      "Real estate acquisition deposit - Dubai"
    - Luxury goods MCC spend: 5944 (Jewelry), 5999 (Luxury retail), art dealers
    - Asset transfer to family member account (intrabank or close counterparty)
    - Transaction remarks reference art, jewelry, real estate, offshore entities
    - Counterparty countries: CH (Switzerland), AE (UAE), CY (Cyprus), MT (Malta)
  Detection features (post groupby):
    intl_wire_to_ae_amt, luxury_mcc_spend, swiss_inbound_count,
    pre_period_credit_spike, hni_flag + ru_nationality + uae_wire_combo

PATTERN 6 — Illegal Alien / MSB Cross-Border Remittance
  Source: FinCEN Alert FIN-2014-A005 (Undocumented Worker Remittances)
  Description:
    Undocumented workers (Mexican, Central American, Southeast Asian
    nationalities) deposit irregular cash from informal employment then
    immediately transfer via Money Services Businesses (MSBs) such as
    Western Union, MoneyGram, Remitly to home countries.  Transactions are
    fragmented below reporting thresholds.  No payroll deposits; income
    inconsistent with declared occupation.
  Behavioural signals embedded:
    - Nationality pool: MX, GT, SV, HN, VN, PH, BD (undocumented worker pool)
    - Cash deposits $200-$2,000 (fragmented, below CTR)
    - Immediate same-day or next-day MSB transfer to home country
    - MSB counterparties: Western Union, MoneyGram, Remitly, Xoom, Ria
    - No salary/payroll credits; cash-in/wire-out pattern
    - Destination countries: MX, GT, SV, HN, VN, PH, BD
    - Transaction remarks: "Remittance to family", "Money transfer - family support"
    - is_non_resident = True for most of this group
  Detection features (post groupby):
    cash_deposit_count, msb_transfer_count, cash_to_msb_ratio,
    unique_msb_counterparties, intl_remittance_total, payroll_absent_flag

PATTERN 7 — Drug Reference in Transaction Remarks
  Source: FinCEN Advisory on Darknet/P2P Drug Payments / SAR data
  Description:
    Customers use P2P payment platforms (Venmo, Zelle, CashApp) or cash
    for drug purchases, with transaction remarks/notes containing drug
    slang, chemical names, or weight measurements.  FinCEN SAR data shows
    this pattern predominantly in P2P digital payments.
    Alongside the text signal, the behavioural pattern (small frequent P2P
    transfers + irregular hours + high cash) supports model detection even
    without NLP features.
  Behavioural signals embedded:
    - Small P2P transfers ($20-$500) with drug-related remarks
    - Remarks contain: fentanyl slang ("fent", "fenty", "china white",
      "blues", "M30s"), chemical names ("Acetylfentanyl", "Carfentanil"),
      weight references ("1g", "2 grams", "half oz"), other drug slang
    - High cash deposit frequency (drug sale proceeds)
    - Transactions predominantly at night (11pm-5am)
    - Many unique counterparties (buyers/suppliers)
    - Channel: Mobile App / P2P predominantly
  Detection features (post groupby):
    drug_keyword_flag_count (requires text extraction from remarks),
    p2p_transfer_count, cash_deposit_count, night_txn_ratio,
    unique_counterparty_count, avg_p2p_amount

NOISE PATTERNS IN NORMAL POPULATION (aml_pattern_label = "Normal")
  These are realistic AML-like behaviours that are innocent.  They ensure
  models must learn DEGREE + COMBINATION, not simple presence/absence.
  NOISE_SUB_CTR_WITHDRAWAL  : sub-$10k ATM series (contractor payments)
  NOISE_LEGIT_INTL_WIRE     : 1-2 large wires (tuition, overseas property)
  NOISE_FREELANCER_ACH      : gig/freelance inbound ACH (Upwork, Fiverr)
  NOISE_BULK_GIFTCARD       : holiday/corporate gift card purchases
  NOISE_ROUND_AMT_DOMESTIC  : round-number rent/loan transfers
  NOISE_HRC_TRAVEL_BURST    : travel POS in high-risk country
  NOISE_VELOCITY_SPIKE      : 3-day shopping/renovation spending spike
  NOISE_LARGE_INBOUND_REDIST: inheritance/settlement redistribution
  NOISE_ODD_HOURS           : night-shift / overseas-timezone spend
  NOISE_CN_AIRLINE_LEGIT    : legitimate Air China flights (diaspora)
  NOISE_DORMANCY_REACT      : dormant account reactivation (illness/travel)

═══════════════════════════════════════════════════════════════════════════
SCHEMA OVERVIEW
═══════════════════════════════════════════════════════════════════════════
customers   (20 columns): demographics, KYC, risk, income, PEP, SAR
accounts    (16 columns): product, currency, status, branch, tenure
transactions(42 columns): amounts, currencies, geolocation, IP, BIC,
                           intermediary, MCC enrichment, remarks, flags

COLUMNS ALIGNED TO FEATURE SPECIFICATION (Book1.xlsx - Raw Features tab)
  All 88 features from the specification are covered across the 3 tables.
═══════════════════════════════════════════════════════════════════════════
"""

# ─────────────────────────────────────────────────────────────────────────────
# 0.  IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import os, gc, warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

OUTPUT_DIR = r"D:\study material\Solytics_Partners\US_Bank_anomaly_detection\codes\data"

TXN_PATH   = os.path.join(OUTPUT_DIR, "transactions.csv")
CUST_PATH  = os.path.join(OUTPUT_DIR, "customers.csv")
ACCT_PATH  = os.path.join(OUTPUT_DIR, "accounts.csv")

SEED = 42
rng  = np.random.default_rng(SEED)

# ── 6-month lookback window ───────────────────────────────────────────────────
END_DATE   = datetime(2026, 3, 31)
START_DATE = datetime(2025, 10, 1)                   # exactly 6 months
TRAIN_CUT  = datetime(2026, 1, 31)                   # first 4 months (training)
# Testing window: TRAIN_CUT → END_DATE (last 2 months)

START_TS = START_DATE.timestamp()
END_TS   = END_DATE.timestamp()
TRAIN_TS = TRAIN_CUT.timestamp()

# ─────────────────────────────────────────────────────────────────────────────
# 1.  CONFIGURATION  (change n_normal to scale everything)
# ─────────────────────────────────────────────────────────────────────────────
CFG = dict(
    # ── Base population ───────────────────────────────────────────────────────
    n_normal = 100_000,     # ← ONLY VALUE TO CHANGE FOR SCALING 75_000 was default

    # ── Typology fractions of n_normal ───────────────────────────────────────
    # Total anomalous at n_normal=100k: 2000/102000 = 1.96%  (< 2% cap)
    pct_p1 = 0.004,   # Pattern 1: China structuring           400 @ 100k
    pct_p2 = 0.004,   # Pattern 2: CMLN/Cartel mule            400 @ 100k
    pct_p3 = 0.003,   # Pattern 3: Rapid movement of funds     300 @ 100k
    pct_p4 = 0.002,   # Pattern 4: Domestic smurfing           200 @ 100k
    pct_p5 = 0.002,   # Pattern 5: Russian oligarch            200 @ 100k
    pct_p6 = 0.003,   # Pattern 6: Illegal alien MSB           300 @ 100k
    pct_p7 = 0.002,   # Pattern 7: Drug reference              200 @ 100k

    # ── Transactions per customer (6-month window) ────────────────────────────
    # US benchmark: ~13 txns/month × 6 months ≈ 78 per customer
    txn_normal_lo = 55,   txn_normal_hi = 105,
    txn_p1_lo     = 15,   txn_p1_hi     = 30,    # cover + structuring wires
    txn_p2_lo     = 50,   txn_p2_hi     = 120,   # high card + P2P spend
    txn_p3_lo     = 20,   txn_p3_hi     = 45,    # rapid movement clusters
    txn_p4_lo     = 25,   txn_p4_hi     = 60,    # cash deposits + consolidate
    txn_p5_lo     = 20,   txn_p5_hi     = 50,    # luxury + wire
    txn_p6_lo     = 25,   txn_p6_hi     = 55,    # cash + MSB
    txn_p7_lo     = 35,   txn_p7_hi     = 85,    # P2P + cash

    # ── Pattern 1 ─────────────────────────────────────────────────────────────
    p1_struct_lo  = 45_000.0,
    p1_struct_hi  = 49_900.0,
    p1_wires_lo   = 4,
    p1_wires_hi   = 10,

    # ── Pattern 2 ─────────────────────────────────────────────────────────────
    p2_income_lo        = 8_000,   p2_income_hi        = 22_000,
    p2_monthly_spend_lo = 3_000,   p2_monthly_spend_hi = 12_000,
    p2_inbound_amt_lo   = 2_000.0, p2_inbound_amt_hi   = 18_000.0,
    p2_inbound_cnt_lo   = 3,       p2_inbound_cnt_hi   = 8,

    # ── Pattern 3 ─────────────────────────────────────────────────────────────
    p3_inbound_lo  = 20_000.0,  p3_inbound_hi  = 200_000.0,
    p3_cluster_cnt = 3,          # rapid movement clusters per customer

    # ── Pattern 4 ─────────────────────────────────────────────────────────────
    p4_deposit_lo  = 7_000.0,  p4_deposit_hi  = 9_800.0,
    p4_deposit_cnt_lo = 5,     p4_deposit_cnt_hi = 12,

    # ── Pattern 5 ─────────────────────────────────────────────────────────────
    p5_wire_lo  = 500_000.0,  p5_wire_hi  = 2_500_000.0,
    p5_income_lo = 500_000,   p5_income_hi = 5_000_000,

    # ── Pattern 6 ─────────────────────────────────────────────────────────────
    p6_cash_lo     = 200.0,   p6_cash_hi     = 2_000.0,
    p6_msb_lo      = 150.0,   p6_msb_hi      = 1_800.0,

    # ── Pattern 7 ─────────────────────────────────────────────────────────────
    p7_p2p_lo = 20.0,  p7_p2p_hi = 500.0,

    # ── Normal-population noise fractions ────────────────────────────────────
    noise_sub_ctr_pct        = 0.030,
    noise_legit_intl_pct     = 0.020,
    noise_freelancer_pct     = 0.040,
    noise_giftcard_pct       = 0.020,
    noise_round_amt_pct      = 0.030,
    noise_hrc_travel_pct     = 0.020,
    noise_velocity_pct       = 0.020,
    noise_large_inbound_pct  = 0.010,
    noise_odd_hours_pct      = 0.020,
    noise_cn_airline_pct     = 0.030,
    noise_dormancy_pct       = 0.015,

    # ── Memory / processing ───────────────────────────────────────────────────
    chunk_customers = 5_000,
)

# ─────────────────────────────────────────────────────────────────────────────
# 2.  FX + COUNTRY MAPPINGS
# ─────────────────────────────────────────────────────────────────────────────
FX = {"USD":1.00,"CNY":7.25,"EUR":0.92,"GBP":0.79,"HKD":7.82,
      "RUB":90.0,"AED":3.67,"CHF":0.88,"MXN":17.2,"CAD":1.36}

COUNTRY_CURRENCY = {
    "US":"USD","CN":"CNY","HK":"HKD","GB":"GBP","UK":"GBP",
    "DE":"EUR","FR":"EUR","IT":"EUR","ES":"EUR","NL":"EUR",
    "RU":"RUB","AE":"AED","CH":"CHF","MX":"MXN","CA":"CAD",
}

HIGH_RISK_COUNTRIES = {"CN","HK","RU","IR","KP","SY","VE","CU","MM",
                        "BY","AE","PK","UA","NG","ET","YE"}

OWN_BANK_BIC = "SYNTHUS33"   # synthetic bank's own SWIFT code

COUNTRY_BIC = {
    "US":["CHASUS33","BOFAUS3N","WFBIUS6S","CITIUS33","PNCCUS33"],
    "CN":["ICBKCNBJ","BKCHIN22","PCBCCNBJ","ABOCCNBJ"],
    "HK":["HSBCHKHH","SCBLHKHH","BKCHHKHH"],
    "RU":["SABRRUMM","VTBRRUMM","SBERRUM2","ALFARUMM"],
    "AE":["NBADAEAA","ADCBAEAA","EBILAEAD"],
    "CH":["UBSWCHZH","CRESCHZZ","ZKBKCHZZ"],
    "DE":["DEUTDEDB","DRESDEFF","COBADEFF"],
    "GB":["BARCGB22","HBUKGB4B","NWBKGB2L"],
    "MX":["BCMRMXMM","BNMXMXMM","HSSCMXMM"],
    "CA":["ROYCCAT2","TDOMCATT","BOFMCAM2"],
    "IN":["ICICIINBB","HDFCINBB","SBILINBB"],
    "GT":["BARCGTGX","BNCGGTGG"],"SV":["BACCSVSS"],
    "HN":["HNDMHNTT"],"VN":["BIDVVNVX","VBAAVNVX"],
    "PH":["BNORPHMM","MBTCPHMM"],"BD":["SONABDDH","PUBABDDH"],
    "CY":["BCYPCY2N","ABLACY2N"],"MT":["MMEBMTMT"],
}

INTERMEDIARY_POOL = {
    "CN":[("JP Morgan Chase","CHASUS33","US"),("Deutsche Bank","DEUTDEDB","DE"),("Citibank","CITIUS33","US")],
    "HK":[("HSBC","HSBCHKHH","HK"),("Citibank","CITIUS33","US")],
    "RU":[("Deutsche Bank","DEUTDEDB","DE"),("Commerzbank","COBADEFF","DE")],
    "AE":[("JP Morgan Chase","CHASUS33","US"),("HSBC","HBUKGB4B","GB")],
    "CH":[("Citibank","CITIUS33","US"),("Deutsche Bank","DEUTDEDB","DE")],
    "MX":[("Citibank","CITIUS33","US"),("Wells Fargo","WFBIUS6S","US")],
    "DEFAULT":[("Citibank","CITIUS33","US"),("JP Morgan Chase","CHASUS33","US")],
}

# ─────────────────────────────────────────────────────────────────────────────
# 3.  REFERENCE DATA
# ─────────────────────────────────────────────────────────────────────────────

CHINESE_SURNAMES = ["Wang","Li","Zhang","Liu","Chen","Yang","Zhao","Huang",
                    "Zhou","Wu","Xu","Sun","Ma","Zhu","Hu","Guo","He","Lin",
                    "Gao","Luo","Zheng","Liang","Xie","Tang","Han","Feng",
                    "Dong","Cheng","Cao","Yuan"]
CHINESE_GIVEN    = ["Wei","Fang","Min","Lei","Jing","Tao","Hao","Xin","Yue",
                    "Peng","Qiang","Rui","Ying","Long","Kun","Shan","Bo",
                    "Jian","Na","Hua","Xiao","Zhi","Hui","Yu","Cheng","Jun"]
RUSSIAN_SURNAMES = ["Ivanov","Petrov","Sidorov","Kozlov","Novikov","Morozov",
                    "Volkov","Alekseev","Lebedev","Semenov","Popov","Egorov",
                    "Orlov","Nikitin","Fedorov","Sokolov","Mikhailov","Zhukov"]
RUSSIAN_GIVEN_M  = ["Aleksandr","Dmitri","Ivan","Mikhail","Sergei","Nikolai",
                    "Andrei","Vladimir","Boris","Pavel","Roman","Viktor"]
RUSSIAN_GIVEN_F  = ["Natasha","Elena","Olga","Irina","Anna","Svetlana",
                    "Maria","Tatiana","Yulia","Ekaterina","Oksana"]
US_FIRST_M = ["James","John","Robert","Michael","William","David","Richard",
               "Joseph","Thomas","Charles","Christopher","Daniel","Matthew",
               "Anthony","Mark","Donald","Steven","Paul","Andrew","Joshua"]
US_FIRST_F = ["Mary","Patricia","Jennifer","Linda","Barbara","Susan",
               "Jessica","Sarah","Karen","Lisa","Nancy","Betty","Margaret",
               "Sandra","Ashley","Dorothy","Kimberly","Emily","Donna","Michelle"]
US_LAST    = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller",
               "Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez",
               "Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin"]

LATAM_FIRST_M = ["Carlos","Jose","Juan","Miguel","Luis","Jorge","Roberto",
                  "Rafael","Antonio","Eduardo","Fernando","Ricardo","Diego"]
LATAM_FIRST_F = ["Maria","Rosa","Carmen","Ana","Patricia","Guadalupe",
                  "Elizabeth","Esperanza","Sandra","Diana","Claudia","Laura"]
LATAM_LAST    = ["Garcia","Rodriguez","Martinez","Lopez","Hernandez","Perez",
                  "Gonzalez","Torres","Ramirez","Flores","Cruz","Morales",
                  "Reyes","Jimenez","Vargas","Mendoza","Gutierrez","Castro"]

SEA_FIRST_M = ["Minh","Duc","Thanh","Hieu","Nguyen","Jose","Juan","Mark",
                "Rahim","Karim","Hasan","Reza","Thang","Bao","Huy"]
SEA_FIRST_F = ["Linh","Lan","Thu","Mai","Rosa","Maria","Nadia","Fatima",
                "Rina","Sari","Dewi","Nita","Hoa","Thuy","Phuong"]
SEA_LAST    = ["Nguyen","Tran","Le","Pham","Hoang","Santos","Reyes","Cruz",
                "Rahman","Islam","Khan","Ali","Bui","Do","Dang","Dinh"]

NATIONALITIES_NORMAL = (
    ["US"]*55+["MX"]*5+["IN"]*5+["PH"]*4+["CA"]*4+["UK"]*4+
    ["KR"]*3+["BR"]*3+["DE"]*3+["FR"]*3+["JP"]*3+["VN"]*2+
    ["CO"]*2+["NG"]*2+["GH"]*2
)
ILLEGAL_ALIEN_NATIONALITIES = (
    ["MX"]*35+["GT"]*15+["SV"]*12+["HN"]*10+["VN"]*10+["PH"]*10+["BD"]*8
)

OCCUPATIONS_NORMAL = [
    "Software Engineer","Accountant","Registered Nurse","Project Manager",
    "Sales Representative","Administrative Assistant","Financial Analyst",
    "Physician","Attorney","Electrician","Plumber","Truck Driver","Chef",
    "Teacher","Marketing Manager","Operations Manager","Data Analyst",
    "Pharmacist","Civil Engineer","Insurance Agent","Real Estate Agent",
]
OCCUPATIONS_MULE   = ["International Student","Graduate Student","Undergraduate Student"]
OCCUPATIONS_OLIGARCH = ["Business Owner","Private Investor","Company Director",
                         "Entrepreneur","Executive Chairman","Managing Director"]
OCCUPATIONS_ILLEGAL = ["Construction Worker","Agricultural Worker",
                        "Domestic Worker","Restaurant Worker","Landscaper",
                        "Factory Worker","Housekeeper","Delivery Worker"]

INDUSTRIES_NORMAL = ["Technology","Healthcare","Finance","Education","Retail",
                      "Manufacturing","Construction","Hospitality","Transportation",
                      "Professional Services","Government","Non-Profit"]

EMPLOYMENT_STATUS = ["Employed","Self-Employed","Retired","Student",
                      "Homemaker","Part-Time","Unemployed","Other"]
EDUCATION_LEVELS  = ["High School Diploma","Associate Degree","Bachelor's Degree",
                      "Master's Degree","Doctoral Degree","Professional Degree",
                      "Some College","Trade/Vocational Certificate"]
SOURCE_OF_FUNDS   = ["Salary","Business Income","Investment Returns",
                      "Inheritance","Rental Income","Pension","Other"]

US_STATES = ["CA","NY","TX","FL","IL","PA","OH","GA","NC","MI","NJ","VA",
              "WA","AZ","MA","TN","IN","MO","MD","WI","CO","MN","SC","AL",
              "LA","KY","OR","OK","CT","UT","NV","AR","MS","KS","NM","NE"]
BRANCH_CITIES = {
    "CA":"Los Angeles","NY":"New York","TX":"Houston","FL":"Miami",
    "IL":"Chicago","PA":"Philadelphia","OH":"Columbus","GA":"Atlanta",
    "NC":"Charlotte","MI":"Detroit","NJ":"Newark","VA":"Richmond",
    "WA":"Seattle","AZ":"Phoenix","MA":"Boston","TN":"Nashville",
    "MO":"St. Louis","MD":"Baltimore","WI":"Milwaukee","CO":"Denver",
    "MN":"Minneapolis","SC":"Columbia","AL":"Birmingham","LA":"New Orleans",
    "KY":"Louisville","OR":"Portland","OK":"Oklahoma City","CT":"Hartford",
    "UT":"Salt Lake City","NV":"Las Vegas",
}

# Geolocation: US and international city coordinates
US_CITY_GEO = {
    "Los Angeles":  (34.0522,-118.2437), "New York":    (40.7128,-74.0060),
    "Houston":      (29.7604,-95.3698),  "Miami":       (25.7617,-80.1918),
    "Chicago":      (41.8781,-87.6298),  "Philadelphia":(39.9526,-75.1652),
    "Columbus":     (39.9612,-82.9988),  "Atlanta":     (33.7490,-84.3880),
    "Charlotte":    (35.2271,-80.8431),  "Detroit":     (42.3314,-83.0458),
    "Newark":       (40.7357,-74.1724),  "Richmond":    (37.5407,-77.4360),
    "Seattle":      (47.6062,-122.3321), "Phoenix":     (33.4484,-112.0740),
    "Boston":       (42.3601,-71.0589),  "Nashville":   (36.1627,-86.7816),
    "St. Louis":    (38.6270,-90.1994),  "Baltimore":   (39.2904,-76.6122),
    "Milwaukee":    (43.0389,-87.9065),  "Denver":      (39.7392,-104.9903),
    "Minneapolis":  (44.9778,-93.2650),  "New Orleans": (29.9511,-90.0715),
    "Louisville":   (38.2527,-85.7585),  "Portland":    (45.5051,-122.6750),
    "Las Vegas":    (36.1699,-115.1398), "Salt Lake City":(40.7608,-111.8910),
}
INTL_CITY_GEO = {
    "CN":[("Shanghai",31.2304,121.4737),("Beijing",39.9042,116.4074),("Shenzhen",22.5431,114.0579)],
    "HK":[("Hong Kong",22.3193,114.1694)],
    "RU":[("Moscow",55.7558,37.6173),("St. Petersburg",59.9343,30.3351)],
    "AE":[("Dubai",25.2048,55.2708),("Abu Dhabi",24.4539,54.3773)],
    "CH":[("Zurich",47.3769,8.5417),("Geneva",46.2044,6.1432)],
    "MX":[("Mexico City",19.4326,-99.1332),("Tijuana",32.5027,-117.0062)],
    "GT":[("Guatemala City",14.6349,-90.5069)],"SV":[("San Salvador",13.6929,-89.2182)],
    "HN":[("Tegucigalpa",14.0818,-87.2068)],"VN":[("Ho Chi Minh City",10.8231,106.6297)],
    "PH":[("Manila",14.5995,120.9842)],"BD":[("Dhaka",23.8103,90.4125)],
    "DE":[("Frankfurt",50.1109,8.6821),("Berlin",52.5200,13.4050)],
    "GB":[("London",51.5074,-0.1278)],
    "CA":[("Toronto",43.6532,-79.3832),("Vancouver",49.2827,-123.1207)],
}

# IP first-octet ranges by country (approximate)
COUNTRY_IP_FIRST = {
    "US":[72,98,174,184,206,208],"CN":[114,116,119,120,121,122,163,220],
    "RU":[95,178,185,46,5],"AE":[185,213,194,109],
    "CH":[83,178,195,213],"MX":[187,189,200,201],
    "GT":[190,200,201],"SV":[190,200],"HN":[190,200],
    "VN":[14,27,42,58,103,113,116,117,118,171,183],
    "PH":[49,58,121,122,180,202,203,210],
    "BD":[103,114,119,202,203,210],
}

ACCOUNT_OPEN_CHANNELS = ["Branch","Online","Mobile App","Referral","Telephone"]
ACCOUNT_PURPOSES      = ["Daily Use","Salary","Savings","Investment","Business"]
PRODUCT_CODE_MAP = {
    "Checking"    : "CURP01", "Savings": "SAV001",
    "Credit Card" : "CRDC01", "Prepaid": "PRPD01",
    "Money Market": "MMKT01",
}

# MCC catalogue: category → (mcc_code, description, risk_cat, [merchants], [channels])
MCC_CATALOGUE = {
    "Grocery"         :("5411","Grocery Stores, Supermarkets","Low",
                         ["Walmart","Kroger","Whole Foods","Trader Joes","Costco","Safeway","Publix"],
                         ["POS","Mobile App"]),
    "Restaurant"      :("5812","Eating Places and Restaurants","Low",
                         ["McDonalds","Chipotle","Starbucks","Subway","Chick-fil-A","Olive Garden"],
                         ["POS","Mobile App"]),
    "Gas Station"     :("5541","Service Stations","Low",
                         ["Shell","BP","Chevron","ExxonMobil","Circle K","Sunoco"],
                         ["POS"]),
    "Utilities"       :("4900","Utilities - Electric, Gas, Water","Low",
                         ["PGE","ConEd","National Grid","Duke Energy","AT&T","Verizon","Comcast"],
                         ["Online Banking","ACH"]),
    "Healthcare"      :("8011","Health Practitioners","Low",
                         ["CVS Pharmacy","Walgreens","Kaiser Permanente","Quest Diagnostics"],
                         ["POS","Online Banking"]),
    "Travel - Air"    :("4511","Airlines, Air Carriers","Low",
                         ["United Airlines","Delta","American Airlines","Southwest","JetBlue"],
                         ["Online Banking","Mobile App"]),
    "Travel - Hotel"  :("7011","Hotels, Motels, Resorts","Low",
                         ["Marriott","Hilton","Hyatt","IHG","Airbnb","Best Western"],
                         ["Online Banking","Mobile App"]),
    "Travel - Car"    :("7512","Automobile Rental Agency","Low",
                         ["Hertz","Enterprise","Avis","Budget","National","Alamo"],
                         ["Online Banking","POS"]),
    "Retail - General":("5999","Miscellaneous Retail","Medium",
                         ["Amazon","Target","Best Buy","Macys","TJ Maxx","Ross","Kohls"],
                         ["Online Banking","POS","Mobile App"]),
    "Retail - Clothing":("5600","Apparel and Accessory Stores","Low",
                         ["HM","Zara","Gap","Nike","Foot Locker","Old Navy","UNIQLO"],
                         ["POS","Online Banking"]),
    "Online Services" :("7372","Computer Programming, Data Processing","Low",
                         ["Netflix","Spotify","Adobe","Microsoft","Amazon Prime","Apple"],
                         ["Online Banking","Mobile App"]),
    "Education"       :("8220","Colleges, Universities","Low",
                         ["University Bursar","Coursera","Udemy","College Board"],
                         ["Online Banking","ACH"]),
    "ATM Withdrawal"  :("6011","Automated Cash Disbursements","High",
                         ["Chase ATM","BofA ATM","Wells Fargo ATM","Citibank ATM"],
                         ["ATM"]),
    "P2P Transfer"    :("6012","Financial Institutions - Merchandise","Medium",
                         ["Zelle","Venmo","PayPal","Cash App","Apple Pay"],
                         ["Mobile App","Online Banking"]),
    "Wire Transfer"   :("4829","Wire Transfer, Money Order","High",
                         ["Wire Transfer"],
                         ["Wire","Branch"]),
    "Intl Wire"       :("4829","Wire Transfer - International","High",
                         ["International Wire Transfer"],
                         ["Wire","Branch"]),
    "Inbound ACH"     :("6012","ACH Credit - Inbound","Medium",
                         ["ACH Credit"],
                         ["ACH"]),
    "Charity"         :("8398","Charitable and Social Service Organizations","Low",
                         ["Red Cross","Salvation Army","UNICEF","GoFundMe"],
                         ["Online Banking","Mobile App"]),
    "Cash Deposit"    :("6010","Financial Institutions - Cash","High",
                         ["Branch Cash Deposit","ATM Cash Deposit"],
                         ["Branch","ATM"]),
    "MSB Transfer"    :("4829","Money Services Business Transfer","High",
                         ["Western Union","MoneyGram","Remitly","Xoom","Ria Money Transfer"],
                         ["Branch","Online Banking","Agent"]),
    "Luxury - Jewelry":("5944","Jewelry Stores, Watches, Clocks","High",
                         ["Tiffany Co","Cartier","Bulgari","Harry Winston","Chopard","Van Cleef"],
                         ["POS","Online Banking"]),
    "Luxury - Art"    :("5999","Art Dealers and Galleries","High",
                         ["Sothebys","Christies","Phillips Auction","Gagosian Gallery","Pace Gallery"],
                         ["Wire","Branch"]),
    "Luxury - Goods"  :("5999","Luxury Retail","High",
                         ["Louis Vuitton","Gucci","Hermes","Chanel","Prada","Burberry","Rolex"],
                         ["POS","Online Banking"]),
    "Real Estate"     :("6531","Real Estate Dealers","High",
                         ["UAE Real Estate LLC","Dubai Properties","Abu Dhabi Investment"],
                         ["Wire","Branch"]),
    "Gift Cards"      :("5947","Card Shops, Gift, Novelty Shops","High",
                         ["CVS Gift Card","Safeway Gift Card","Walmart Gift Card","Target Gift Card","Amazon Gift Card"],
                         ["POS"]),
    "Prepaid Cards"   :("6051","Non-Financial Institutions - Foreign Currency","High",
                         ["Greendot","NetSpend","Bluebird Prepaid","Visa Prepaid","Mastercard Prepaid"],
                         ["POS","Online Banking"]),
    "Electronics"     :("5732","Electronics Stores","Medium",
                         ["Apple Store","Best Buy","Micro Center","Newegg","Samsung Store"],
                         ["POS","Online Banking"]),
    "Cellphones"      :("4812","Telephone and Telegraph Equipment","Medium",
                         ["AT&T Store","T-Mobile","Verizon","Apple Store","Cricket Wireless"],
                         ["POS","Online Banking"]),
    "CN Airline"      :("4511","Airlines - International","Medium",
                         ["Air China","China Eastern Airlines","Cathay Pacific","Hainan Airlines"],
                         ["Online Banking","Mobile App"]),
}

MULE_CATS    = ["Gift Cards","Prepaid Cards","Electronics","Cellphones","CN Airline","Luxury - Goods"]
MULE_WEIGHTS = [0.22, 0.18, 0.20, 0.23, 0.12, 0.05]

SHELL_NAMES = [
    "Pacific Wang Trading LLC","Golden Chen Group Inc","SinoUS Li Corp",
    "Dragon Zhang Holdings LLC","Huang Global Imports Inc",
    "Liu Technology Solutions LLC","Zhou Consulting Group Inc",
    "Wu Global Enterprises LLC","Sun Pacific Trading Partners LLC",
    "Zheng International Corp","Han Import Export LLC","Feng Commerce LLC",
    "Cheng Pacific Holdings LLC","Guo Overseas Trading LLC",
    "Luo Sino-American LLC","Tang Pacific Consulting LLC",
]
MSB_OPERATORS = ["Western Union","MoneyGram","Remitly","Xoom","Ria Money Transfer",
                  "Intermex Wire Transfer","Vigo Remittance","Transfast"]
UAE_REAL_ESTATE = [
    "Dubai Premier Properties LLC","Abu Dhabi Realty Investments",
    "Emirates Real Estate Corp","Gulf Coast Properties UAE",
    "Al Noor Real Estate LLC","Burj Capital Properties",
    "Desert Rose Investment Properties","Falcon Real Estate Group UAE",
]
SWISS_ORIGIN_NAMES = [
    "Zurich Private Holdings AG","Geneva Wealth Management SA",
    "Swiss Capital Partners AG","Alpine Investment Group SA",
    "Helvetia Asset Management","Lucerne Family Office SA",
]
FREELANCER_PAYERS = [
    "Upwork Inc","Fiverr International","Toptal LLC","Freelancer.com",
    "Deel Inc","Gusto Payroll","Stripe Payouts","Square Payroll",
    "Shopify Payments","DoorDash Payments","Uber Eats Payouts",
    "Lyft Driver Payouts","Instacart Shopper Pay","TaskRabbit",
]

# Drug slang and chemical names for P7 remarks
DRUG_REMARKS = [
    "payment for 1g fent","fenty x2 units","china white delivery",
    "blue M30 supply 10 pack","acetylfentanyl 2 grams","carfentanil sample",
    "payment - 1 gram fentanyl","percs payment","fenty supply",
    "white powder 5g delivery","blues 30 count","1g fent payment",
    "oxycontin supply 20 units","pressing M30 payment","supplier payment fent",
    "half oz white","fentanyl analogue 3g","synthetic opioid payment",
    "payment for pharma supply","drug supply payment 2g","fenty delivery fee",
    "chemical supply payment","medicinal compound 5g","batch payment blues",
    "street pharmacy supply","controlled substance fee","pill press supply",
    "powder supply 1oz","supply chain payment fent","wholesale pharma batch",
]

# Normal transaction remarks by category
NORMAL_REMARKS = {
    "Grocery"         :["Weekly grocery shopping","Supermarket - household supplies",
                         "Food and grocery purchase","Daily household essentials","Monthly pantry restock"],
    "Restaurant"      :["Dining out - restaurant","Family dinner","Business lunch",
                         "Weekend brunch","Quick lunch meal"],
    "Gas Station"     :["Vehicle fuel fill-up","Gas station - weekly fuel","Car fuel purchase"],
    "Utilities"       :["Monthly electricity bill","Water utility payment",
                         "Internet and cable bill","Mobile phone bill payment"],
    "Healthcare"      :["Pharmacy prescription pickup","Medical co-pay",
                         "Healthcare expenses","Annual physical co-payment"],
    "Travel - Air"    :["Flight booking - vacation","Business travel flight",
                         "Airline ticket purchase","Weekend getaway flight"],
    "Travel - Hotel"  :["Hotel accommodation - business trip","Vacation hotel stay",
                         "Conference hotel booking"],
    "Travel - Car"    :["Car rental - business trip","Rental car - road trip"],
    "Retail - General":["Online shopping purchase","Retail purchase - household",
                         "Amazon order payment","General retail purchase"],
    "Retail - Clothing":["Clothing purchase","Apparel shopping","Wardrobe update"],
    "Online Services" :["Monthly subscription","Streaming service payment",
                         "Software subscription renewal"],
    "Education"       :["University tuition payment","Online course enrollment",
                         "Educational materials purchase"],
    "ATM Withdrawal"  :["ATM cash withdrawal - personal use","Cash for weekend expenses",
                         "ATM withdrawal - petty cash"],
    "P2P Transfer"    :["Payment to friend - split bill","Loan repayment - personal",
                         "Shared expense reimbursement","Birthday gift transfer"],
    "Wire Transfer"   :["Personal funds transfer","Payment for services rendered",
                         "Investment account transfer","Business payment"],
    "Intl Wire"       :["International remittance to family","Overseas property payment",
                         "Family support abroad","International business payment"],
    "Inbound ACH"     :["Salary deposit","Payroll credit","Business income deposit",
                         "Freelance payment received","Direct deposit - employer"],
    "Cash Deposit"    :["Cash deposit - personal savings","Cash from sales",
                         "Cash deposit - received funds"],
    "Charity"         :["Charitable donation","Community fund contribution","Nonprofit support"],
    "Default"         :["General transaction","Payment processed","Transfer executed"],
}

CHANNEL_TXN_TYPE = {
    "POS":"Card","ATM":"ATM","Wire":"Wire","Branch":"Cash",
    "ACH":"Digital Transfer","Online Banking":"Digital Transfer",
    "Mobile App":"Digital Transfer","Agent":"Digital Transfer","SWIFT":"Wire",
}
CHANNEL_SUB_TYPE = {
    "POS"           :"POS Purchase",
    "ATM"           :"ATM Withdrawal",
    "Wire"          :"Domestic Wire",
    "Branch"        :"Cash Deposit",
    "ACH"           :"ACH Debit",
    "Online Banking":"Online Transfer",
    "Mobile App"    :"Mobile Payment",
    "Agent"         :"Agent Transfer",
    "SWIFT"         :"International Wire",
}
CHANNEL_FEE = {
    "Wire":25.0,"ATM":3.5,"Branch":5.0,
    "ACH":0.0,"POS":0.0,"Online Banking":0.0,
    "Mobile App":0.0,"Agent":4.99,"SWIFT":35.0,
}

# ─────────────────────────────────────────────────────────────────────────────
# 4.  HELPER UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def make_ids(prefix: str, n: int) -> np.ndarray:
    nums = rng.integers(1_000_000_000, 9_999_999_999, size=n)
    return np.array([f"{prefix}{x}" for x in nums], dtype=object)

def rand_timestamps(n: int, start=None, end=None):
    s = (start or START_DATE).timestamp()
    e = (end   or END_DATE  ).timestamp()
    return pd.to_datetime(rng.uniform(s, e, size=n), unit="s").round("s")

def rand_choice(pool, n: int, weights=None) -> np.ndarray:
    p = np.array(weights)/np.sum(weights) if weights else None
    idx = rng.choice(len(pool), size=n, p=p)
    return np.array(pool)[idx]

def rand_uniform(lo: float, hi: float, n: int) -> np.ndarray:
    return rng.uniform(lo, hi, size=n).round(2)

def rand_int(lo: int, hi: int, n: int) -> np.ndarray:
    return rng.integers(lo, hi+1, size=n)

def ext_ref(n: int, prefix="EXT") -> np.ndarray:
    nums = rng.integers(100_000_000, 999_999_999, size=n)
    return np.array([f"{prefix}{x}" for x in nums], dtype=object)

def bene_ccy(cpty_countries: np.ndarray) -> np.ndarray:
    valid = set(FX.keys())
    return np.array([
        COUNTRY_CURRENCY.get(c,"USD") if COUNTRY_CURRENCY.get(c,"USD") in valid else "USD"
        for c in cpty_countries
    ])

def gen_ips(n: int, country="US") -> np.ndarray:
    firsts = COUNTRY_IP_FIRST.get(country, [192,193,194,195])
    fo = rng.choice(firsts, size=n)
    return np.array([
        f"{fo[i]}.{rng.integers(0,255)}.{rng.integers(0,255)}.{rng.integers(1,254)}"
        for i in range(n)
    ], dtype=object)

def gen_geo(n: int, country="US", state=None) -> tuple:
    """Returns (lats, lngs, cities) arrays."""
    if country == "US":
        city_name = BRANCH_CITIES.get(state,"New York") if state else "New York"
        lat_base, lng_base = US_CITY_GEO.get(city_name, (40.7128,-74.0060))
        lats = (lat_base + rng.uniform(-0.15, 0.15, n)).round(6)
        lngs = (lng_base + rng.uniform(-0.15, 0.15, n)).round(6)
        return lats, lngs, np.full(n, city_name)
    else:
        pool = INTL_CITY_GEO.get(country, [("Unknown",0.0,0.0)])
        picks = [pool[rng.integers(0, len(pool))] for _ in range(n)]
        lats  = np.array([p[1]+rng.uniform(-0.1,0.1) for p in picks]).round(6)
        lngs  = np.array([p[2]+rng.uniform(-0.1,0.1) for p in picks]).round(6)
        cits  = np.array([p[0] for p in picks], dtype=object)
        return lats, lngs, cits

def remarks_for(categories: np.ndarray, custom: np.ndarray = None) -> np.ndarray:
    if custom is not None:
        return custom
    return np.array([
        str(rng.choice(NORMAL_REMARKS.get(c, NORMAL_REMARKS["Default"])))
        for c in categories
    ], dtype=object)

def _fast_acct(customer_ids: np.ndarray, acct_pool: dict) -> np.ndarray:
    unique = list(dict.fromkeys(customer_ids))
    selected = {cid: str(rng.choice(acct_pool.get(cid,["UNKNOWN"]))) for cid in unique}
    return pd.Series(customer_ids).map(selected).values

def _build_acct_pool(accounts: pd.DataFrame) -> dict:
    transactable = accounts[accounts["account_status"].isin(["Active","Dormant"])]
    return transactable.groupby("linked_customer_id")["account_id"].apply(list).to_dict()

# ─────────────────────────────────────────────────────────────────────────────
# 5.  TRANSACTION FRAME BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _make_txn_frame(
    customer_ids    : np.ndarray,
    account_ids     : np.ndarray,
    amounts_usd     : np.ndarray,
    txn_dates       : pd.DatetimeIndex,
    categories      : np.ndarray,
    channels        : np.ndarray,
    txn_types       : np.ndarray,
    cpty_names      : np.ndarray,
    cpty_countries  : np.ndarray,
    is_intrabank    : np.ndarray,
    all_internal_accts: np.ndarray,
    orig_currency   : np.ndarray,
    pattern_labels  : np.ndarray,
    aml_flags       : np.ndarray,
    transaction_remarks: np.ndarray,
    cust_states     : np.ndarray = None,
) -> pd.DataFrame:

    N = len(customer_ids)

    # ── MCC info from categories ─────────────────────────────────────────────
    mcc_codes    = np.array([MCC_CATALOGUE.get(c,MCC_CATALOGUE["Retail - General"])[0] for c in categories])
    mcc_descs    = np.array([MCC_CATALOGUE.get(c,MCC_CATALOGUE["Retail - General"])[1] for c in categories])
    mcc_risk     = np.array([MCC_CATALOGUE.get(c,MCC_CATALOGUE["Retail - General"])[2] for c in categories])
    merchant_names = np.array([
        str(rng.choice(MCC_CATALOGUE.get(c,MCC_CATALOGUE["Retail - General"])[3]))
        for c in categories
    ])
    merchant_ids = make_ids("MID", N)

    # ── Transaction type / sub-type / fee ────────────────────────────────────
    txn_type_col = np.array([CHANNEL_TXN_TYPE.get(ch,"Digital Transfer") for ch in channels])
    sub_type_col = np.array([
        "International Wire" if (categories[i] == "Intl Wire" or cpty_countries[i] != "US")
        and channels[i] in ("Wire","SWIFT")
        else ("ACH Credit" if txn_types[i] == "Credit" and channels[i] == "ACH"
              else CHANNEL_SUB_TYPE.get(channels[i],"Online Transfer"))
        for i in range(N)
    ])
    fee_base = np.array([CHANNEL_FEE.get(ch, 0.0) for ch in channels])
    fee_noise = rng.uniform(0, 5, N)
    fee_amounts = np.where(fee_base > 0, (fee_base + fee_noise).round(2), 0.0)

    # ── Currencies + amounts ──────────────────────────────────────────────────
    bene_curr   = bene_ccy(cpty_countries)
    orig_fx     = np.array([FX.get(c, 1.0) for c in orig_currency])
    bene_fx_arr = np.array([FX.get(c, 1.0) for c in bene_curr])
    orig_curr_amount = (amounts_usd * orig_fx).round(2)
    bene_curr_amount = (amounts_usd * bene_fx_arr).round(2)
    exch_rate = np.where(
        orig_currency != bene_curr,
        (bene_fx_arr / orig_fx).round(6),
        np.nan
    )

    # ── Dates ─────────────────────────────────────────────────────────────────
    post_offset  = pd.to_timedelta(rng.integers(0, 3, N), unit="D")
    posting_date = txn_dates + post_offset
    value_date   = txn_dates + pd.to_timedelta(rng.integers(0, 2, N), unit="D")

    # ── Counterparty accounts ─────────────────────────────────────────────────
    ext_refs    = ext_ref(N, "EXT")
    cnbk_refs   = ext_ref(N, "CNBK")
    ru_refs     = ext_ref(N, "RUBK")
    ae_refs     = ext_ref(N, "AEBK")
    intra_refs  = all_internal_accts[rng.integers(0, len(all_internal_accts), N)]
    cpty_accounts = np.where(
        is_intrabank, intra_refs,
        np.where(cpty_countries=="CN", cnbk_refs,
        np.where(cpty_countries=="RU", ru_refs,
        np.where(cpty_countries=="AE", ae_refs, ext_refs)))
    )
    is_debit     = txn_types == "Debit"
    orig_account = np.where(is_debit, account_ids, cpty_accounts)
    bene_account = np.where(is_debit, cpty_accounts, account_ids)

    # ── BIC codes ────────────────────────────────────────────────────────────
    def pick_bic(country):
        pool = COUNTRY_BIC.get(country, COUNTRY_BIC["US"])
        return str(rng.choice(pool))
    own_bic_arr   = np.full(N, OWN_BANK_BIC)
    cpty_bic_arr  = np.array([pick_bic(c) for c in cpty_countries])
    orig_bank_bic = np.where(is_debit, own_bic_arr, cpty_bic_arr)
    bene_bank_bic = np.where(is_debit, cpty_bic_arr, own_bic_arr)
    # Counterparty bank name
    cpty_bank_names = np.array([
        rng.choice(["Chase Bank","Bank of America","Wells Fargo","Citibank",
                    "JPMorgan","TD Bank","US Bank","PNC Bank"])
        if c == "US" else f"Bank of {c}"
        for c in cpty_countries
    ], dtype=object)

    # ── Geolocation ───────────────────────────────────────────────────────────
    needs_geo   = np.isin(channels, ["POS","ATM","Branch"])
    has_ip      = np.isin(channels, ["Online Banking","Mobile App","Agent",
                                      "Wire","ACH","SWIFT"])
    branch_atm  = np.isin(channels, ["Branch","ATM"])
    txn_lats    = np.full(N, np.nan)
    txn_lngs    = np.full(N, np.nan)
    txn_cities  = np.full(N, "", dtype=object)
    txn_ctries  = np.full(N, "", dtype=object)
    ip_addrs    = np.full(N, "", dtype=object)
    ip_channels = np.full(N, "", dtype=object)
    ip_ctries   = np.full(N, "", dtype=object)

    # Batch geo for POS/ATM/Branch
    if needs_geo.any():
        idx = np.where(needs_geo)[0]
        for i in idx:
            cty = cpty_countries[i] if cpty_countries[i] != "US" else "US"
            st  = cust_states[i] if (cust_states is not None and cty == "US") else None
            lts, lgs, cits = gen_geo(1, cty, st)
            txn_lats[i]   = lts[0]; txn_lngs[i] = lgs[0]
            txn_cities[i] = cits[0]; txn_ctries[i] = cty

    # Branch/ATM: assign private 10.x IPs (bank's internal terminal network)
    if branch_atm.any():
        bidx = np.where(branch_atm)[0]
        for i in bidx:
            ip_addrs[i]    = f"10.{rng.integers(0,256)}.{rng.integers(0,256)}.{rng.integers(1,255)}"
            ip_channels[i] = "Branch Terminal" if channels[i] == "Branch" else "ATM Terminal"
            ip_ctries[i]   = "US"

    # Online/Mobile/Wire channels: assign public IPs matching customer's country
    if has_ip.any():
        idx = np.where(has_ip)[0]
        for i in idx:
            # Customer's country drives IP, not counterparty (sender's device)
            cty = cust_states[i][:2] if cust_states is not None else "US"
            cty = "US"   # all our retail customers are US-resident
            ip_addrs[i]    = gen_ips(1, cty)[0]
            ip_channels[i] = ("Web" if channels[i] == "Online Banking"
                              else "Mobile" if channels[i] == "Mobile App"
                              else "Agent Portal" if channels[i] == "Agent"
                              else "Secure Web")
            ip_ctries[i]   = cty
            txn_ctries[i]  = cty

    # ── Originator / Beneficiary address type & party type (Book1) ──────────
    # address_type: Residential (individuals) | Business (corporates/shell)
    # party_type:   Internal-Individual | External-Individual | External-Corporate | External-Bank
    def _addr_type(names):
        is_biz = np.array([
            any(w in str(n) for w in ["LLC","Inc","Corp","Ltd","Group","SA","AG",
                                       "Holdings","Trading","Consulting","Co.","Bank",
                                       "Real Estate","Trust","Partners","Management"])
            for n in names
        ])
        return np.where(is_biz, "Business", "Residential")

    orig_addr_type = np.where(is_debit, "Residential", _addr_type(cpty_names))
    bene_addr_type = np.where(is_debit, _addr_type(cpty_names), "Residential")

    def _party_type(is_intra, is_deb, cpty_ns):
        result = np.full(len(is_intra), "", dtype=object)
        for i in range(len(is_intra)):
            if is_intra[i]:
                result[i] = "Internal-Individual"
            else:
                n = str(cpty_ns[i])
                is_biz = any(w in n for w in ["LLC","Inc","Corp","Ltd","Group","SA","AG",
                                               "Bank","Holdings","Trading","Management"])
                result[i] = "External-Corporate" if is_biz else "External-Individual"
        return result

    cpty_party_type = _party_type(is_intrabank, is_debit, cpty_names)
    orig_party_type = np.where(is_debit, "Internal-Individual", cpty_party_type)
    bene_party_type = np.where(is_debit, cpty_party_type, "Internal-Individual")

    # ── Intermediary banks split into _1 / _2 / _3 (Book1: up to 10) ────────
    interm_nm1 = np.full(N, "", dtype=object); interm_bic1 = np.full(N, "", dtype=object); interm_cty1 = np.full(N, "", dtype=object)
    interm_nm2 = np.full(N, "", dtype=object); interm_bic2 = np.full(N, "", dtype=object); interm_cty2 = np.full(N, "", dtype=object)
    interm_nm3 = np.full(N, "", dtype=object); interm_bic3 = np.full(N, "", dtype=object); interm_cty3 = np.full(N, "", dtype=object)

    is_intl_wire = (cpty_countries != "US") & (np.isin(channels, ["Wire","SWIFT"]))
    has_1 = is_intl_wire & (rng.random(N) < 0.70)
    has_2 = has_1 & (rng.random(N) < 0.50)
    has_3 = (has_2 & (rng.random(N) < 0.35)) | (pattern_labels == "P5_RussianOligarch")

    for i in range(N):
        if not has_1[i]: continue
        pool = INTERMEDIARY_POOL.get(str(cpty_countries[i]), INTERMEDIARY_POOL["DEFAULT"])
        nm, bic, cy = pool[rng.integers(0, len(pool))]
        interm_nm1[i]=nm; interm_bic1[i]=bic; interm_cty1[i]=cy
        if has_2[i]:
            nm2, bic2, cy2 = INTERMEDIARY_POOL["DEFAULT"][rng.integers(0,len(INTERMEDIARY_POOL["DEFAULT"]))]
            interm_nm2[i]=nm2; interm_bic2[i]=bic2; interm_cty2[i]=cy2
        if has_3[i]:
            nm3, bic3, cy3 = INTERMEDIARY_POOL["DEFAULT"][rng.integers(0,len(INTERMEDIARY_POOL["DEFAULT"]))]
            interm_nm3[i]=nm3; interm_bic3[i]=bic3; interm_cty3[i]=cy3
    is_international  = cpty_countries != "US"
    is_high_risk_cty  = np.array([c in HIGH_RISK_COUNTRIES for c in cpty_countries])
    is_round_amount   = (amounts_usd % 1000 == 0) | (amounts_usd % 500 == 0)
    reversal_indicator = np.where(rng.random(N) < 0.005, "Yes", "No")
    txn_status         = np.where(
        rng.random(N) < 0.005, rng.choice(["Failed","Pending","Reversed"], N),
        "Success"
    )
    hour = txn_dates.hour
    time_of_day = np.where(hour < 6, "Night",
                  np.where(hour < 12, "Morning",
                  np.where(hour < 17, "Afternoon", "Evening")))
    is_training = txn_dates < pd.Timestamp(TRAIN_CUT)

    # ── Orig/bene location (from cpty_countries) ─────────────────────────────
    ob_countries = cpty_countries.copy()
    ob_states    = np.full(N, "", dtype=object)
    ob_cities    = np.full(N, "", dtype=object)
    for i in range(N):
        if cpty_countries[i] == "US" and cust_states is not None:
            ob_states[i] = cust_states[i]
            ob_cities[i] = BRANCH_CITIES.get(str(cust_states[i]), "")

    df = pd.DataFrame({
        # ── Identifiers ──────────────────────────────────────────────────────
        "transaction_id"          : make_ids("TXN", N),
        "customer_id"             : customer_ids,
        "account_id"              : account_ids,
        # ── Dates ────────────────────────────────────────────────────────────
        "transaction_datetime"    : txn_dates,
        "posting_date"            : posting_date,
        "value_date"              : value_date,
        "is_training_window"      : is_training,
        # ── Transaction classification ────────────────────────────────────────
        "debit_credit_indicator"  : pd.Categorical(txn_types, categories=["Debit","Credit"]),
        "transaction_type"        : pd.Categorical(txn_type_col),
        "transaction_sub_type"    : pd.Categorical(sub_type_col),
        "transaction_category"    : pd.Categorical(categories),
        "transaction_channel"     : pd.Categorical(channels),
        # ── Amounts + currencies ─────────────────────────────────────────────
        "transaction_amount_usd"  : amounts_usd.round(2),
        "orig_currency"           : pd.Categorical(orig_currency),
        "bene_currency"           : pd.Categorical(bene_curr),
        "orig_curr_amount"        : orig_curr_amount,
        "bene_curr_amount"        : bene_curr_amount,
        "exchange_rate_applied"   : exch_rate,
        "fee_amount"              : fee_amounts,
        # ── Orig / Bene account + bank ────────────────────────────────────────
        "orig_account"            : orig_account,
        "bene_account"            : bene_account,
        "originator_bank_bic"     : orig_bank_bic,
        "beneficiary_bank_bic"    : bene_bank_bic,
        # ── Orig/Bene party type + address type (Book1) ───────────────────────
        "originator_address_type" : pd.Categorical(orig_addr_type, categories=["Residential","Business"]),
        "originator_party_type"   : pd.Categorical(orig_party_type),
        "beneficiary_address_type": pd.Categorical(bene_addr_type, categories=["Residential","Business"]),
        "beneficiary_party_type"  : pd.Categorical(bene_party_type),
        # ── Orig/Bene geography ───────────────────────────────────────────────
        "orig_bene_country"       : pd.Categorical(ob_countries),
        "orig_bene_state"         : ob_states,
        "orig_bene_city"          : ob_cities,
        # ── Counterparty ──────────────────────────────────────────────────────
        "counterparty_name"       : cpty_names,
        "counterparty_account"    : cpty_accounts,
        "counterparty_bank_name"  : cpty_bank_names,
        "counterparty_country"    : pd.Categorical(cpty_countries),
        "is_intrabank"            : is_intrabank,
        # ── MCC ───────────────────────────────────────────────────────────────
        "merchant_name"           : merchant_names,
        "merchant_id"             : merchant_ids,
        "mcc_code"                : pd.Categorical(mcc_codes),
        "mcc_description"         : pd.Categorical(mcc_descs),
        "mcc_risk_category"       : pd.Categorical(mcc_risk, categories=["Low","Medium","High"], ordered=True),
        # ── Geolocation ───────────────────────────────────────────────────────
        "transaction_latitude"    : txn_lats,
        "transaction_longitude"   : txn_lngs,
        "transaction_city"        : txn_cities,
        "transaction_country"     : pd.Categorical(txn_ctries),
        # ── IP ────────────────────────────────────────────────────────────────
        "transaction_ip_address"  : ip_addrs,
        "ip_capture_channel"      : ip_channels,
        "ip_country_derived"      : pd.Categorical(ip_ctries),
        # ── Intermediary banks 1-3 (Book1: up to 10; retail max is 3) ─────────
        "intermediary_bank_name_1"   : interm_nm1,
        "intermediary_bank_bic_1"    : interm_bic1,
        "intermediary_bank_country_1": pd.Categorical(interm_cty1),
        "intermediary_bank_name_2"   : interm_nm2,
        "intermediary_bank_bic_2"    : interm_bic2,
        "intermediary_bank_country_2": pd.Categorical(interm_cty2),
        "intermediary_bank_name_3"   : interm_nm3,
        "intermediary_bank_bic_3"    : interm_bic3,
        "intermediary_bank_country_3": pd.Categorical(interm_cty3),
        # ── Status + flags ────────────────────────────────────────────────────
        "transaction_status"      : pd.Categorical(txn_status),
        "reversal_indicator"      : pd.Categorical(reversal_indicator),
        "is_international"        : is_international,
        "is_high_risk_country"    : is_high_risk_cty,
        "is_round_amount"         : is_round_amount,
        "time_of_day"             : pd.Categorical(time_of_day, categories=["Morning","Afternoon","Evening","Night"]),
        # ── Remarks ───────────────────────────────────────────────────────────
        "transaction_remarks"     : transaction_remarks,
        # ── AML labels ────────────────────────────────────────────────────────
        "aml_pattern_label"       : pd.Categorical(pattern_labels),
        "aml_flag"                : pd.Categorical(aml_flags),
    })
    return df

# ─────────────────────────────────────────────────────────────────────────────
# 6.  CUSTOMER GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_customers() -> pd.DataFrame:
    n     = CFG["n_normal"]
    n_p1  = max(1, int(n * CFG["pct_p1"]))
    n_p2  = max(1, int(n * CFG["pct_p2"]))
    n_p3  = max(1, int(n * CFG["pct_p3"]))
    n_p4  = max(1, int(n * CFG["pct_p4"]))
    n_p5  = max(1, int(n * CFG["pct_p5"]))
    n_p6  = max(1, int(n * CFG["pct_p6"]))
    n_p7  = max(1, int(n * CFG["pct_p7"]))
    N = n + n_p1 + n_p2 + n_p3 + n_p4 + n_p5 + n_p6 + n_p7

    patterns = np.array(
        ["Normal"]*n + ["P1_ChinaStructuring"]*n_p1 +
        ["P2_MoneyMule_CMLN"]*n_p2 + ["P3_RapidMovement"]*n_p3 +
        ["P4_Smurfing"]*n_p4 + ["P5_RussianOligarch"]*n_p5 +
        ["P6_IllegalAlienMSB"]*n_p6 + ["P7_DrugReference"]*n_p7
    )

    is_cn  = np.isin(patterns, ["P1_ChinaStructuring","P2_MoneyMule_CMLN"])
    is_ru  = patterns == "P5_RussianOligarch"
    is_la  = patterns == "P6_IllegalAlienMSB"  # Latin American / SEA

    # ── Names ─────────────────────────────────────────────────────────────────
    f_names = np.empty(N, dtype=object); l_names = np.empty(N, dtype=object)
    for i in range(N):
        if is_cn[i]:
            f_names[i] = str(rng.choice(CHINESE_GIVEN))
            l_names[i] = str(rng.choice(CHINESE_SURNAMES))
        elif is_ru[i]:
            g = rng.random()
            if g < 0.55:
                f_names[i] = str(rng.choice(RUSSIAN_GIVEN_M))
            else:
                f_names[i] = str(rng.choice(RUSSIAN_GIVEN_F))
            l_names[i] = str(rng.choice(RUSSIAN_SURNAMES))
        elif is_la[i]:
            nat = ILLEGAL_ALIEN_NATIONALITIES[rng.integers(0, len(ILLEGAL_ALIEN_NATIONALITIES))]
            if nat in ("VN","PH","BD"):
                f_names[i] = str(rng.choice(SEA_FIRST_M if rng.random()<0.5 else SEA_FIRST_F))
                l_names[i] = str(rng.choice(SEA_LAST))
            else:
                f_names[i] = str(rng.choice(LATAM_FIRST_M if rng.random()<0.5 else LATAM_FIRST_F))
                l_names[i] = str(rng.choice(LATAM_LAST))
        else:
            if rng.random() < 0.5:
                f_names[i] = str(rng.choice(US_FIRST_M))
            else:
                f_names[i] = str(rng.choice(US_FIRST_F))
            l_names[i] = str(rng.choice(US_LAST))

    # ── Gender (Male/Female only) ─────────────────────────────────────────────
    genders = rand_choice(["Male","Female"], N, weights=[0.50, 0.50])

    # ── DOB ───────────────────────────────────────────────────────────────────
    age_lo = np.where(is_cn|is_la, 18,
             np.where(patterns=="P2_MoneyMule_CMLN", 18,
             np.where(is_ru, 35, 18)))
    age_hi = np.where(patterns=="P2_MoneyMule_CMLN", 28,
             np.where(is_ru, 70, 75))
    ages   = np.array([int(rng.integers(int(age_lo[i]), int(age_hi[i])+1)) for i in range(N)])
    dob_years = END_DATE.year - ages
    dobs = pd.to_datetime(
        [datetime(int(y), int(rng.integers(1,13)), int(rng.integers(1,29))) for y in dob_years]
    ).date

    # ── Nationality ───────────────────────────────────────────────────────────
    nat_arr = np.empty(N, dtype=object)
    for i in range(N):
        if is_cn[i]:   nat_arr[i] = "CN"
        elif is_ru[i]: nat_arr[i] = rng.choice(["RU","BY","KZ","UA"])
        elif is_la[i]: nat_arr[i] = ILLEGAL_ALIEN_NATIONALITIES[rng.integers(0,len(ILLEGAL_ALIEN_NATIONALITIES))]
        else:          nat_arr[i] = NATIONALITIES_NORMAL[rng.integers(0,len(NATIONALITIES_NORMAL))]

    residence  = rand_choice(US_STATES, N)
    res_country= np.full(N, "US")
    is_non_res = ((nat_arr != "US") & (rng.random(N) < 0.20)).astype(bool)
    # P6 illegal aliens: mostly non-resident
    is_non_res = np.where(is_la, rng.random(N) < 0.70, is_non_res).astype(bool)
    tax_res    = np.where(nat_arr == "US", "US",
                 np.where(is_non_res, nat_arr, "US"))

    # ── Occupation / Employment / Industry ────────────────────────────────────
    occ_arr = np.empty(N, dtype=object); emp_arr = np.empty(N, dtype=object)
    ind_arr = np.empty(N, dtype=object)
    for i in range(N):
        pat = patterns[i]
        if pat in ("P1_ChinaStructuring",):
            occ_arr[i] = str(rng.choice(["Business Owner","Self-Employed Consultant","Import/Export Manager","Private Investor"]))
            emp_arr[i] = "Self-Employed"
            ind_arr[i] = str(rng.choice(["Import/Export","Technology","Trading","Finance"]))
        elif pat == "P2_MoneyMule_CMLN":
            occ_arr[i] = str(rng.choice(OCCUPATIONS_MULE))
            emp_arr[i] = "Student"
            ind_arr[i] = "Education"
        elif pat == "P5_RussianOligarch":
            occ_arr[i] = str(rng.choice(OCCUPATIONS_OLIGARCH))
            emp_arr[i] = "Self-Employed"
            ind_arr[i] = str(rng.choice(["Finance","Real Estate","Energy","Mining","Technology"]))
        elif pat == "P6_IllegalAlienMSB":
            occ_arr[i] = str(rng.choice(OCCUPATIONS_ILLEGAL))
            emp_arr[i] = str(rng.choice(["Employed","Unemployed","Part-Time"]))
            ind_arr[i] = str(rng.choice(["Construction","Agriculture","Hospitality","Manufacturing"]))
        elif pat == "P7_DrugReference":
            occ_arr[i] = str(rng.choice(["Unemployed","Part-Time Worker","Cash Business Owner",
                                          "Gig Worker","Student","Retail Worker"]))
            emp_arr[i] = str(rng.choice(["Unemployed","Part-Time","Employed"]))
            ind_arr[i] = str(rng.choice(["Retail","Hospitality","Other"]))
        elif pat in ("P3_RapidMovement","P4_Smurfing"):
            occ_arr[i] = str(rng.choice(["Business Owner","Accountant","Cash Business Owner",
                                          "Retail Business Owner","Self-Employed"]))
            emp_arr[i] = "Self-Employed"
            ind_arr[i] = str(rng.choice(["Retail","Real Estate","Construction","Finance"]))
        else:
            occ_arr[i] = str(rng.choice(OCCUPATIONS_NORMAL))
            emp_arr[i] = str(rng.choice(["Employed"]*60+["Self-Employed"]*15+
                                          ["Retired"]*10+["Homemaker"]*5+
                                          ["Part-Time"]*5+["Unemployed"]*3+["Other"]*2))
            ind_arr[i] = str(rng.choice(INDUSTRIES_NORMAL))

    # ── Income + source of funds ──────────────────────────────────────────────
    income_arr = np.where(
        patterns=="P2_MoneyMule_CMLN",
        rand_uniform(CFG["p2_income_lo"], CFG["p2_income_hi"], N),
        np.where(patterns=="P5_RussianOligarch",
        rand_uniform(CFG["p5_income_lo"], CFG["p5_income_hi"], N),
        np.where(is_cn, rand_uniform(80_000, 350_000, N),
        np.where(is_la, rand_uniform(12_000, 35_000, N),
        np.where(patterns=="P7_DrugReference", rand_uniform(10_000, 40_000, N),
        rand_uniform(30_000, 200_000, N)))))
    ).round(2)

    sof_arr = np.where(
        np.isin(patterns,["P2_MoneyMule_CMLN","P7_DrugReference"]),
        "Other",
        np.where(patterns=="P5_RussianOligarch", "Business Income",
        np.where(is_la, "Salary",
        rand_choice(SOURCE_OF_FUNDS, N)))
    )

    # ── Education / marital / ID doc ──────────────────────────────────────────
    edu_arr = np.where(
        patterns=="P2_MoneyMule_CMLN",
        rand_choice(["Bachelor's Degree","Master's Degree","Some College"], N),
        rand_choice(EDUCATION_LEVELS, N,
                    weights=[0.22,0.10,0.32,0.20,0.05,0.04,0.05,0.02])
    )
    marital_arr = rand_choice(["Single","Married","Divorced","Widowed"], N,
                               weights=[0.40,0.45,0.10,0.05])
    id_doc_arr  = np.where(
        nat_arr == "US",
        rand_choice(["Driver's License","Passport","National ID"], N,
                    weights=[0.55,0.35,0.10]),
        rand_choice(["Passport","National ID","Residence Permit"], N,
                    weights=[0.60,0.25,0.15])
    )
    id_country_arr = nat_arr.copy()

    # ── Risk + PEP + Sanctions ────────────────────────────────────────────────
    risk_arr = np.where(
        np.isin(patterns,["P1_ChinaStructuring","P5_RussianOligarch"]),
        rand_choice(["Medium","Medium","High"], N),
        np.where(np.isin(patterns,["P2_MoneyMule_CMLN","P3_RapidMovement",
                                    "P4_Smurfing","P6_IllegalAlienMSB","P7_DrugReference"]),
        rand_choice(["Low","Low","Medium"], N),
        rand_choice(["Low"]*70+["Medium"]*25+["High"]*5, N))
    )
    is_pep_arr = np.where(
        patterns=="P5_RussianOligarch",
        rand_choice(["Yes","Yes","No"], N),
        np.where(risk_arr=="High", rand_choice(["Yes","No","No","No"], N), "No")
    )
    sanctions_arr = np.where(
        patterns=="P5_RussianOligarch",
        rand_choice(["Yes","Yes","No"], N),
        "No"
    )
    sar_arr = np.where(
        patterns == "Normal", "No",
        rand_choice(["Yes","Yes","Yes","No"], N)   # 75% SAR for known typologies
    )

    # ── Credit score ──────────────────────────────────────────────────────────
    cs_arr = np.where(
        patterns=="P2_MoneyMule_CMLN", rand_int(540,670,N),
        np.where(patterns=="P5_RussianOligarch", rand_int(700,820,N),
        np.where(is_la, rand_int(480,640,N),
        rand_int(580,850,N)))
    )

    # ── KYC dates ─────────────────────────────────────────────────────────────
    kyc_gap_days = np.where(risk_arr=="High", 365,
                   np.where(risk_arr=="Medium", 730, 1095))
    last_kyc_off = rng.integers(180, 1095, N)
    last_kyc = pd.to_datetime(
        [END_DATE - timedelta(days=int(d)) for d in last_kyc_off]
    ).date
    next_kyc = pd.to_datetime(
        [END_DATE - timedelta(days=int(last_kyc_off[i])) +
         timedelta(days=int(kyc_gap_days[i])) for i in range(N)]
    ).date

    since_days = np.where(
        np.isin(patterns,["P2_MoneyMule_CMLN","P6_IllegalAlienMSB"]),
        rand_int(180, 2*365, N),
        rand_int(180, 10*365, N)
    )
    cust_since = pd.to_datetime(
        [END_DATE - timedelta(days=int(d)) for d in since_days]
    ).date

    # ── Customer category ─────────────────────────────────────────────────────
    cust_cat = np.where(
        patterns=="P5_RussianOligarch", "HNI",
        np.where(nat_arr!="US", "NRA",
        np.where(ages>=60, "Senior Citizen",
        np.where(ages<18, "Minor", "Retail")))
    )

    return pd.DataFrame({
        "customer_id"               : make_ids("CUST", N),
        "customer_type"             : "Individual",
        "customer_segment"          : "Retail Banking",
        "customer_category"         : pd.Categorical(cust_cat),
        "first_name"                : f_names,
        "last_name"                 : l_names,
        "gender"                    : pd.Categorical(genders, categories=["Male","Female"]),
        "date_of_birth"             : dobs,
        "marital_status"            : pd.Categorical(marital_arr,
                                          categories=["Single","Married","Divorced","Widowed"]),
        "nationality"               : pd.Categorical(nat_arr),
        "country_of_birth"          : pd.Categorical(nat_arr),
        "residential_country"       : "US",
        "residence_state"           : pd.Categorical(residence),
        "tax_residence_country"     : pd.Categorical(tax_res),
        "is_non_resident"           : is_non_res,
        "id_document_type"          : pd.Categorical(id_doc_arr),
        "id_issuing_country"        : pd.Categorical(id_country_arr),
        "occupation"                : pd.Categorical(occ_arr),
        "industry"                  : pd.Categorical(ind_arr),
        "employment_status"         : pd.Categorical(emp_arr, categories=EMPLOYMENT_STATUS),
        "education"                 : pd.Categorical(edu_arr, categories=EDUCATION_LEVELS),
        "declared_annual_income"    : income_arr,
        "source_of_funds"           : pd.Categorical(sof_arr),
        "credit_fico_score"         : cs_arr.astype(np.int16),
        "customer_risk_rating"      : pd.Categorical(risk_arr,
                                          categories=["Low","Medium","High"], ordered=True),
        "is_pep"                    : pd.Categorical(is_pep_arr),
        "sanctions_screening_flag"  : pd.Categorical(sanctions_arr),
        "sar_filing_indicator"      : pd.Categorical(sar_arr),
        "credit_card_holder"        : "No",         # updated after accounts
        "onboarding_date"           : cust_since,
        "last_kyc_review_date"      : last_kyc,
        "next_kyc_review_date"      : next_kyc,
        "aml_pattern"               : pd.Categorical(patterns),
    })

# ─────────────────────────────────────────────────────────────────────────────
# 7.  ACCOUNT GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_accounts(cust_df: pd.DataFrame) -> pd.DataFrame:
    ACCT_MIX = {
        "Normal"             :(["Checking","Savings","Credit Card"],[0.50,0.30,0.20],1,3),
        "P1_ChinaStructuring":(["Checking","Savings"],[0.60,0.40],2,3),
        "P2_MoneyMule_CMLN"  :(["Checking","Credit Card","Prepaid"],[0.35,0.40,0.25],3,6),
        "P3_RapidMovement"   :(["Checking","Savings"],[0.70,0.30],2,3),
        "P4_Smurfing"        :(["Checking"],[1.0],1,2),
        "P5_RussianOligarch" :(["Checking","Savings","Credit Card"],[0.30,0.30,0.40],3,5),
        "P6_IllegalAlienMSB" :(["Checking"],[1.0],1,2),
        "P7_DrugReference"   :(["Checking","Prepaid"],[0.70,0.30],1,3),
    }
    CURR_POOL = list(FX.keys())
    CURR_W    = [0.70, 0.08, 0.06, 0.04, 0.04, 0.04, 0.02, 0.01, 0.01]
    # Pad weights to match FX keys length
    while len(CURR_W) < len(CURR_POOL): CURR_W.append(0.01)
    CURR_W_arr = np.array(CURR_W[:len(CURR_POOL)], dtype=float)
    CURR_W_arr /= CURR_W_arr.sum()

    STATUS_POOL = ["Active"]*5 + ["Dormant","Closed","Frozen"]
    rows = []
    has_cc = set()

    for _, cust in cust_df.iterrows():
        pat = str(cust["aml_pattern"])
        types, wts, lo, hi = ACCT_MIX.get(pat, ACCT_MIX["Normal"])
        n     = int(rng.integers(lo, hi+1))
        chosen= list(rng.choice(types, size=n, p=np.array(wts)/sum(wts), replace=True))

        for i, atype in enumerate(chosen):
            status   = "Active" if i == 0 else str(rng.choice(STATUS_POOL))
            currency = str(rng.choice(CURR_POOL, p=CURR_W_arr))
            open_days= int(rng.integers(180, 10*365))
            open_dt  = (END_DATE - timedelta(days=open_days)).date()
            tenure   = int((END_DATE.date() - open_dt).days // 30)

            credit_lim = None
            if atype == "Credit Card":
                credit_lim = float(rng.choice([2_000,3_000,5_000,7_500,10_000,15_000,20_000,50_000]))
                has_cc.add(str(cust["customer_id"]))
            elif atype == "Prepaid":
                credit_lim = round(float(rng.uniform(500, 5_000)), 2)

            bal_base = rng.uniform(500, 15_000)
            if atype == "Savings": bal_base = rng.uniform(1_000, 80_000)
            if pat == "P5_RussianOligarch": bal_base = rng.uniform(50_000, 2_000_000)

            st = str(cust["residence_state"])
            rows.append({
                "account_id"              : make_ids("ACC", 1)[0],
                "linked_customer_id"      : cust["customer_id"],
                "account_type"            : atype,
                "product_subtype"         : _subtype(atype, pat),
                "product_code"            : PRODUCT_CODE_MAP.get(atype, "GEN001"),
                "currency_code"           : currency,
                "account_opening_date"    : open_dt,
                "account_status"          : status,
                "account_ownership_type"  : "Individual",
                "account_purpose"         : str(rng.choice(ACCOUNT_PURPOSES)),
                "account_tenure_months"   : tenure,
                "credit_limit"            : credit_lim,
                "current_balance"         : round(bal_base, 2),
                "account_opening_channel" : str(rng.choice(ACCOUNT_OPEN_CHANNELS)),
                "branch_code"             : f"BR{rng.integers(1,200):03d}",
                "branch_location"         : BRANCH_CITIES.get(st, "New York"),
                "interest_bearing"        : "Yes" if atype in ("Savings","Money Market") else "No",
            })

    df = pd.DataFrame(rows)
    for c in ["account_type","product_subtype","product_code","currency_code",
              "account_status","account_ownership_type","account_purpose",
              "account_opening_channel","interest_bearing"]:
        df[c] = pd.Categorical(df[c])
    # Update credit_card_holder on customers
    cust_df["credit_card_holder"] = cust_df["customer_id"].isin(has_cc).map({True:"Yes",False:"No"})
    return df

def _subtype(atype, pat):
    if atype == "Credit Card":
        if pat == "P2_MoneyMule_CMLN":
            return str(rng.choice(["Student Credit Card","Secured Card","Basic Rewards"]))
        if pat == "P5_RussianOligarch":
            return str(rng.choice(["Platinum Rewards","World Elite","Black Card"]))
        return str(rng.choice(["Rewards","Cashback","Travel Rewards","Secured"]))
    if atype == "Prepaid":
        return str(rng.choice(["Visa Prepaid","Mastercard Prepaid","Gift Card Reload"]))
    if atype == "Savings":
        return str(rng.choice(["Regular Savings","High-Yield Savings","Money Market"]))
    return atype

# ─────────────────────────────────────────────────────────────────────────────
# 8.  SEGMENT TRANSACTION BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_normal_txns(chunk: pd.DataFrame, acct_pool: dict,
                       all_accts: np.ndarray) -> pd.DataFrame:
    cats     = [c for c in MCC_CATALOGUE if c not in
                ("Luxury - Jewelry","Luxury - Art","Luxury - Goods","Real Estate",
                 "MSB Transfer","Intl Wire","Gift Cards","Prepaid Cards","CN Airline")]
    n_per    = rand_int(CFG["txn_normal_lo"], CFG["txn_normal_hi"], len(chunk))
    total    = int(n_per.sum())
    cust_ids = np.repeat(chunk["customer_id"].values, n_per)
    states   = np.repeat(chunk["residence_state"].astype(str).values, n_per)
    acct_ids = _fast_acct(cust_ids, acct_pool)
    dates    = rand_timestamps(total)
    cat_arr  = rand_choice(cats, total)
    chs      = np.array([str(rng.choice(MCC_CATALOGUE[c][4])) for c in cat_arr])
    amounts  = np.exp(rng.normal(4.5, 1.2, total)).clip(1, 8_000).round(2)
    is_p2p   = cat_arr == "P2P Transfer"
    is_intra = is_p2p & (rng.random(total) < 0.50)
    cpty_ctys= np.where(rng.random(total) < 0.02,
                        rand_choice(["CA","MX","GB","DE","FR"], total), "US")
    cpty_ns  = np.array([
        str(rng.choice(MCC_CATALOGUE.get(c, MCC_CATALOGUE["Retail - General"])[3]))
        for c in cat_arr
    ], dtype=object)
    txn_typs = np.where(is_p2p,
                        rand_choice(["Debit","Credit"], total, weights=[0.55,0.45]),
                        "Debit")
    remarks  = remarks_for(cat_arr)
    return _make_txn_frame(
        cust_ids, acct_ids, amounts, dates, cat_arr, chs, txn_typs,
        cpty_ns, cpty_ctys, is_intra, all_accts, np.full(total,"USD"),
        np.full(total,"Normal"), np.full(total,"NONE"), remarks, states
    )


def build_p1_txns(chunk: pd.DataFrame, acct_pool: dict, all_accts: np.ndarray) -> pd.DataFrame:
    frames = []
    # Structuring wires — core anomaly signal
    wc   = rand_int(CFG["p1_wires_lo"], CFG["p1_wires_hi"], len(chunk))
    nw   = int(wc.sum())
    wcid = np.repeat(chunk["customer_id"].values, wc)
    wst  = np.repeat(chunk["residence_state"].astype(str).values, wc)
    waid = _fast_acct(wcid, acct_pool)
    wamt = rand_uniform(CFG["p1_struct_lo"], CFG["p1_struct_hi"], nw)
    wrem = np.array([f"Family support transfer to China - personal remittance {i}" for i in range(nw)], dtype=object)
    wcpty= np.array([f"{rng.choice(CHINESE_SURNAMES)} Family Account" for _ in range(nw)], dtype=object)
    frames.append(_make_txn_frame(
        wcid, waid, wamt, rand_timestamps(nw), np.full(nw,"Intl Wire"),
        np.full(nw,"Wire"), np.full(nw,"Debit"), wcpty, np.full(nw,"CN"),
        np.zeros(nw,bool), all_accts, np.full(nw,"USD"),
        np.full(nw,"P1_ChinaStructuring"), np.full(nw,"STRUCT_WIRE_CN_BELOW_50K"),
        wrem, wst
    ))
    # Cover transactions
    cc   = rand_int(CFG["txn_p1_lo"], CFG["txn_p1_hi"], len(chunk))
    nc   = int(cc.sum())
    ccid = np.repeat(chunk["customer_id"].values, cc)
    cst  = np.repeat(chunk["residence_state"].astype(str).values, cc)
    caid = _fast_acct(ccid, acct_pool)
    ccats= rand_choice(["Grocery","Restaurant","Gas Station","Retail - General","Online Services"], nc)
    crem = remarks_for(ccats)
    cch  = np.array([str(rng.choice(MCC_CATALOGUE[c][4])) for c in ccats])
    frames.append(_make_txn_frame(
        ccid, caid, np.exp(rng.normal(4.5,1.0,nc)).clip(1,2000).round(2),
        rand_timestamps(nc), ccats, cch, np.full(nc,"Debit"),
        np.array([str(rng.choice(MCC_CATALOGUE[c][3])) for c in ccats]),
        np.full(nc,"US"), np.zeros(nc,bool), all_accts, np.full(nc,"USD"),
        np.full(nc,"Normal"), np.full(nc,"NONE"), crem, cst
    ))
    return pd.concat(frames, ignore_index=True)


def build_p2_txns(chunk: pd.DataFrame, acct_pool: dict, all_accts: np.ndarray) -> pd.DataFrame:
    frames = []
    # Inbound ACH from shell companies (labelled tuition/living expenses)
    ic   = rand_int(CFG["p2_inbound_cnt_lo"], CFG["p2_inbound_cnt_hi"], len(chunk))
    ni   = int(ic.sum())
    icid = np.repeat(chunk["customer_id"].values, ic)
    ist  = np.repeat(chunk["residence_state"].astype(str).values, ic)
    iaid = _fast_acct(icid, acct_pool)
    irem = rand_choice(["Tuition fee from family sponsor","Living expense support from parents",
                         "Educational support transfer","Tuition and accommodation support",
                         "Monthly living allowance from family","Academic program support payment"], ni)
    frames.append(_make_txn_frame(
        icid, iaid, rand_uniform(CFG["p2_inbound_amt_lo"],CFG["p2_inbound_amt_hi"],ni),
        rand_timestamps(ni), np.full(ni,"Inbound ACH"), np.full(ni,"ACH"), np.full(ni,"Credit"),
        rand_choice(SHELL_NAMES, ni), np.full(ni,"US"), np.zeros(ni,bool), all_accts,
        np.full(ni,"USD"), np.full(ni,"P2_MoneyMule_CMLN"),
        np.full(ni,"MULE_INBOUND_SHELL_ACH"), irem, ist
    ))
    # Mule outbound spend
    sc    = rand_int(CFG["txn_p2_lo"], CFG["txn_p2_hi"], len(chunk))
    ns    = int(sc.sum())
    scid  = np.repeat(chunk["customer_id"].values, sc)
    sst   = np.repeat(chunk["residence_state"].astype(str).values, sc)
    said  = _fast_acct(scid, acct_pool)
    monthly= rng.uniform(CFG["p2_monthly_spend_lo"], CFG["p2_monthly_spend_hi"], len(chunk))
    ptavg = (monthly * 6) / np.maximum(sc, 1)
    ptavg_exp = np.repeat(ptavg, sc)
    samts = np.abs(rng.normal(ptavg_exp, ptavg_exp*0.35)).clip(20).round(2)
    scati = rng.choice(len(MULE_CATS), size=ns, p=MULE_WEIGHTS)
    scats = np.array(MULE_CATS)[scati]
    sctys = rand_choice(["US","US","CN","HK"], ns, weights=[0.55,0.15,0.20,0.10])
    sch   = np.array([str(rng.choice(MCC_CATALOGUE[c][4])) for c in scats])
    srem  = rand_choice(["Gift card purchase for family","Prepaid card reload",
                          "Electronics purchase","Phone plan payment","Airline ticket to China",
                          "Luxury goods payment","Card purchase - personal"], ns)
    sflgs = np.array([f"MULE_SPEND_{c.upper().replace(' ','_').replace('-','_')}" for c in scats])
    frames.append(_make_txn_frame(
        scid, said, samts, rand_timestamps(ns), scats, sch, np.full(ns,"Debit"),
        np.array([str(rng.choice(MCC_CATALOGUE[c][3])) for c in scats]),
        sctys, np.zeros(ns,bool), all_accts, np.full(ns,"USD"),
        np.full(ns,"P2_MoneyMule_CMLN"), sflgs, srem, sst
    ))
    # P2P to unknown third parties
    pc   = rand_int(3, 10, len(chunk))
    np_  = int(pc.sum())
    pcid = np.repeat(chunk["customer_id"].values, pc)
    pst  = np.repeat(chunk["residence_state"].astype(str).values, pc)
    paid = _fast_acct(pcid, acct_pool)
    prem = rand_choice(["Payment to contact","Transfer - personal","P2P payment","Send money"], np_)
    frames.append(_make_txn_frame(
        pcid, paid, rand_uniform(100, 3000, np_), rand_timestamps(np_),
        np.full(np_,"P2P Transfer"), rand_choice(["Mobile App","Online Banking"], np_),
        np.full(np_,"Debit"), rand_choice([f"Contact_{i:04d}" for i in range(200)], np_),
        rand_choice(["US","CN","HK"], np_, weights=[0.50,0.35,0.15]),
        np.zeros(np_,bool), all_accts, np.full(np_,"USD"),
        np.full(np_,"P2_MoneyMule_CMLN"), np.full(np_,"MULE_P2P_UNKNOWN_THIRD_PARTY"),
        prem, pst
    ))
    return pd.concat(frames, ignore_index=True)


def build_p3_txns(chunk: pd.DataFrame, acct_pool: dict, all_accts: np.ndarray) -> pd.DataFrame:
    """Pattern 3: Rapid movement of funds — large inbound followed by multiple quick outflows."""
    frames = []
    cluster_days = [int(rng.integers(5, 75)) for _ in range(CFG["p3_cluster_cnt"])]

    for cluster_day in cluster_days:
        cluster_start = START_DATE + timedelta(days=cluster_day)
        cluster_end   = cluster_start + timedelta(hours=48)

        n  = len(chunk)
        cids = chunk["customer_id"].values
        sts  = chunk["residence_state"].astype(str).values
        aids = _fast_acct(cids, acct_pool)

        # Inbound credit (placement)
        in_amts  = rand_uniform(CFG["p3_inbound_lo"], CFG["p3_inbound_hi"], n)
        in_dates = rand_timestamps(n, cluster_start, cluster_start + timedelta(hours=4))
        in_srcs  = rand_choice(["Overseas Investment Proceeds","Business Revenue Transfer",
                                  "Asset Liquidation Transfer","Portfolio Rebalancing Credit",
                                  "International Business Settlement"], n)
        in_ctys  = rand_choice(["US","CN","HK","AE"], n, weights=[0.40,0.25,0.20,0.15])
        frames.append(_make_txn_frame(
            cids, aids, in_amts, in_dates, np.full(n,"Intl Wire" if (in_ctys!="US").any() else "Wire Transfer"),
            np.full(n,"Wire"), np.full(n,"Credit"), in_srcs, in_ctys,
            np.zeros(n,bool), all_accts, np.full(n,"USD"),
            np.full(n,"P3_RapidMovement"), np.full(n,"RAPID_LARGE_INBOUND"),
            np.array([f"Large credit received - {s}" for s in in_srcs], dtype=object), sts
        ))
        # Multiple outbound within 48 hours (layering)
        out_cnt = rand_int(3, 8, n)
        n_out   = int(out_cnt.sum())
        o_cids  = np.repeat(cids, out_cnt)
        o_sts   = np.repeat(sts, out_cnt)
        o_aids  = _fast_acct(o_cids, acct_pool)
        # Amounts split: consume 80-100% of inbound
        in_amts_exp = np.repeat(in_amts, out_cnt)
        o_amts  = (in_amts_exp / np.repeat(out_cnt, out_cnt) *
                   rand_uniform(0.15, 0.30, n_out)).round(2)
        o_dates = rand_timestamps(n_out, cluster_start + timedelta(hours=6), cluster_end)
        o_ctys  = rand_choice(["US","CN","HK","AE","GB"], n_out,
                               weights=[0.30,0.25,0.20,0.15,0.10])
        o_cptys = rand_choice(["Investment LLC","Trading Corp","Family Trust",
                                 "Consulting Group","Capital Partners","Holdings Ltd"], n_out)
        o_rem   = rand_choice(["Funds transfer - investment","Layered transfer",
                                 "Payment for services","Business disbursement",
                                 "Portfolio allocation transfer","Capital transfer"], n_out)
        frames.append(_make_txn_frame(
            o_cids, o_aids, o_amts, o_dates,
            np.where(o_ctys=="US", np.full(n_out,"Wire Transfer"), np.full(n_out,"Intl Wire")),
            np.full(n_out,"Wire"), np.full(n_out,"Debit"), o_cptys, o_ctys,
            np.zeros(n_out,bool), all_accts, np.full(n_out,"USD"),
            np.full(n_out,"P3_RapidMovement"), np.full(n_out,"RAPID_OUTBOUND_WITHIN_48H"),
            o_rem, o_sts
        ))
    return pd.concat(frames, ignore_index=True)


def build_p4_txns(chunk: pd.DataFrame, acct_pool: dict, all_accts: np.ndarray) -> pd.DataFrame:
    """Pattern 4: Domestic cash structuring (smurfing) — sub-$10k deposits at multiple branches."""
    frames = []
    n     = len(chunk)
    cids  = chunk["customer_id"].values
    sts   = chunk["residence_state"].astype(str).values

    # Multiple structured cash deposits in dense 30-day windows
    dep_cnt = rand_int(CFG["p4_deposit_cnt_lo"], CFG["p4_deposit_cnt_hi"], n)
    n_dep   = int(dep_cnt.sum())
    d_cids  = np.repeat(cids, dep_cnt)
    d_sts   = np.repeat(sts, dep_cnt)
    d_aids  = _fast_acct(d_cids, acct_pool)
    d_amts  = rand_uniform(CFG["p4_deposit_lo"], CFG["p4_deposit_hi"], n_dep)
    # All deposits within a 30-day window (structuring cluster)
    window_s = START_DATE + timedelta(days=int(rng.integers(0, 150)))
    window_e = window_s + timedelta(days=30)
    d_dates  = rand_timestamps(n_dep, window_s, window_e)
    d_rems   = rand_choice(["Cash deposit - business proceeds",
                              "Cash deposit - contractor payment received",
                              "Cash deposit - personal savings",
                              "Business cash proceeds deposit",
                              "Cash from sales - deposit",
                              "Daily business cash deposit"], n_dep)
    frames.append(_make_txn_frame(
        d_cids, d_aids, d_amts, d_dates, np.full(n_dep,"Cash Deposit"),
        rand_choice(["Branch","ATM"], n_dep, weights=[0.70,0.30]),
        np.full(n_dep,"Credit"), np.full(n_dep,"Cash Deposit"),
        np.full(n_dep,"US"), np.zeros(n_dep,bool), all_accts, np.full(n_dep,"USD"),
        np.full(n_dep,"P4_Smurfing"), np.full(n_dep,"SMURFING_SUB_CTR_CASH_DEPOSIT"),
        d_rems, d_sts
    ))
    # Consolidating outward wire after deposits
    c_aids  = _fast_acct(cids, acct_pool)
    c_amts  = np.array([
        rand_uniform(CFG["p4_deposit_lo"]*dep_cnt[i]*0.80,
                     CFG["p4_deposit_lo"]*dep_cnt[i]*0.95, 1)[0]
        for i in range(n)
    ])
    c_dates = rand_timestamps(n,
                               window_e + timedelta(days=1),
                               window_e + timedelta(days=7))
    c_ctys  = rand_choice(["US","CN","MX"], n, weights=[0.60,0.25,0.15])
    c_rems  = rand_choice(["Consolidation transfer","Business wire - proceeds",
                             "Funds transfer to business account",
                             "Wire transfer - consolidated savings"], n)
    frames.append(_make_txn_frame(
        cids, c_aids, c_amts, c_dates,
        np.where(c_ctys=="US", np.full(n,"Wire Transfer"), np.full(n,"Intl Wire")),
        np.full(n,"Wire"), np.full(n,"Debit"),
        rand_choice(["Business Account","Family Account","Investment Account"], n),
        c_ctys, np.zeros(n,bool), all_accts, np.full(n,"USD"),
        np.full(n,"P4_Smurfing"), np.full(n,"SMURFING_CONSOLIDATING_WIRE"), c_rems, sts
    ))
    return pd.concat(frames, ignore_index=True)


def build_p5_txns(chunk: pd.DataFrame, acct_pool: dict, all_accts: np.ndarray) -> pd.DataFrame:
    """Pattern 5: Russian oligarch — Swiss inbound credit spike + UAE real estate wire + luxury."""
    frames = []
    n     = len(chunk)
    cids  = chunk["customer_id"].values
    sts   = chunk["residence_state"].astype(str).values

    # Swiss inbound credit card payments (spike in months 5-6 = testing window)
    # Train window: 1-2 payments per month, Test window: 4-6 payments per month
    def swiss_payments(start, end, cnt_per_cust, flag):
        sc   = rand_int(*cnt_per_cust, n)
        ns   = int(sc.sum())
        s_c  = np.repeat(cids, sc)
        s_s  = np.repeat(sts, sc)
        s_a  = _fast_acct(s_c, acct_pool)
        s_am = rand_uniform(5_000, 80_000, ns)
        s_src= rand_choice(SWISS_ORIGIN_NAMES, ns)
        s_rem= rand_choice(["Credit card payment from Swiss account",
                              "Monthly credit facility payment - Switzerland",
                              "Card statement payment - offshore account",
                              "International card payment - private banking"], ns)
        return _make_txn_frame(
            s_c, s_a, s_am, rand_timestamps(ns, start, end),
            np.full(ns,"Inbound ACH"), np.full(ns,"Wire"), np.full(ns,"Credit"),
            s_src, np.full(ns,"CH"), np.zeros(ns,bool), all_accts, np.full(ns,"USD"),
            np.full(ns,"P5_RussianOligarch"), np.full(ns,flag), s_rem, s_s
        )
    # Train: low frequency
    frames.append(swiss_payments(START_DATE, TRAIN_CUT, (1,2), "OLIGARCH_SWISS_INBOUND_NORMAL"))
    # Test: spike (pre-sanction analog)
    frames.append(swiss_payments(TRAIN_CUT, END_DATE, (4,6), "OLIGARCH_SWISS_INBOUND_SPIKE"))

    # Large wire to UAE real estate
    aids  = _fast_acct(cids, acct_pool)
    uae_amts = rand_uniform(CFG["p5_wire_lo"], CFG["p5_wire_hi"], n)
    uae_rems = rand_choice([
        "Purchase and sale of residential premises in UAE",
        "Real estate acquisition deposit - Dubai property",
        "Property purchase payment - UAE",
        "Pre-sale residential property payment Dubai",
        "Investment property acquisition - UAE real estate",
        "Luxury apartment purchase - Dubai Marina",
    ], n)
    frames.append(_make_txn_frame(
        cids, aids, uae_amts, rand_timestamps(n, TRAIN_CUT, END_DATE),
        np.full(n,"Real Estate"), np.full(n,"Wire"), np.full(n,"Debit"),
        rand_choice(UAE_REAL_ESTATE, n), np.full(n,"AE"),
        np.zeros(n,bool), all_accts, np.full(n,"USD"),
        np.full(n,"P5_RussianOligarch"), np.full(n,"OLIGARCH_UAE_REAL_ESTATE_WIRE"),
        uae_rems, sts
    ))
    # Luxury goods spend
    lc   = rand_int(3, 10, n)
    nl   = int(lc.sum())
    l_c  = np.repeat(cids, lc)
    l_s  = np.repeat(sts, lc)
    l_a  = _fast_acct(l_c, acct_pool)
    l_cats = rand_choice(["Luxury - Jewelry","Luxury - Art","Luxury - Goods"], nl,
                          weights=[0.35,0.30,0.35])
    l_amts = rand_uniform(5_000, 200_000, nl)
    l_rems = rand_choice(["Jewelry acquisition - private collection",
                           "Art purchase - gallery",
                           "Luxury goods - personal purchase",
                           "High-value watch purchase",
                           "Auction house payment - artwork",
                           "Private sale - collectibles"], nl)
    frames.append(_make_txn_frame(
        l_c, l_a, l_amts, rand_timestamps(nl), l_cats,
        np.array([str(rng.choice(MCC_CATALOGUE[c][4])) for c in l_cats]),
        np.full(nl,"Debit"),
        np.array([str(rng.choice(MCC_CATALOGUE[c][3])) for c in l_cats]),
        rand_choice(["US","AE","GB","CH","FR"], nl, weights=[0.30,0.30,0.20,0.10,0.10]),
        np.zeros(nl,bool), all_accts, np.full(nl,"USD"),
        np.full(nl,"P5_RussianOligarch"), np.full(nl,"OLIGARCH_LUXURY_PURCHASE"),
        l_rems, l_s
    ))
    # Asset transfer to family member
    fam_aids = _fast_acct(cids, acct_pool)
    fam_amts = rand_uniform(100_000, 1_000_000, n)
    fam_rems = rand_choice(["Transfer to family member - personal",
                              "Asset transfer - family trust",
                              "Gift to family member",
                              "Transfer to spouse account",
                              "Family support - asset movement"], n)
    frames.append(_make_txn_frame(
        cids, fam_aids, fam_amts, rand_timestamps(n, START_DATE, TRAIN_CUT),
        np.full(n,"Wire Transfer"), np.full(n,"Wire"), np.full(n,"Debit"),
        rand_choice([f"Family Member {i}" for i in range(50)], n),
        rand_choice(["US","AE","CH","CY","MT"], n, weights=[0.30,0.30,0.20,0.10,0.10]),
        np.zeros(n,bool), all_accts, np.full(n,"USD"),
        np.full(n,"P5_RussianOligarch"), np.full(n,"OLIGARCH_ASSET_TRANSFER_FAMILY"),
        fam_rems, sts
    ))
    return pd.concat(frames, ignore_index=True)


def build_p6_txns(chunk: pd.DataFrame, acct_pool: dict, all_accts: np.ndarray) -> pd.DataFrame:
    """Pattern 6: Illegal alien / undocumented worker MSB remittances."""
    frames = []
    n     = len(chunk)
    cids  = chunk["customer_id"].values
    sts   = chunk["residence_state"].astype(str).values
    # Assign home countries based on nationality
    home_ctys = rand_choice(["MX","GT","SV","HN","VN","PH","BD"], n,
                              weights=[0.35,0.15,0.12,0.10,0.10,0.10,0.08])

    # Cash deposits (fragmented, from informal employment)
    cc   = rand_int(8, 20, n)
    nc   = int(cc.sum())
    c_c  = np.repeat(cids, cc)
    c_s  = np.repeat(sts, cc)
    c_a  = _fast_acct(c_c, acct_pool)
    c_am = rand_uniform(CFG["p6_cash_lo"], CFG["p6_cash_hi"], nc)
    c_rem= rand_choice(["Cash deposit - wages","Cash from work",
                          "Cash deposit - weekly pay","Cash wages deposit",
                          "Daily wage deposit - cash","Work cash deposit"], nc)
    frames.append(_make_txn_frame(
        c_c, c_a, c_am, rand_timestamps(nc),
        np.full(nc,"Cash Deposit"), rand_choice(["Branch","ATM"], nc, weights=[0.60,0.40]),
        np.full(nc,"Credit"), np.full(nc,"Cash Deposit - Employment"),
        np.full(nc,"US"), np.zeros(nc,bool), all_accts, np.full(nc,"USD"),
        np.full(nc,"P6_IllegalAlienMSB"), np.full(nc,"ILLEGAL_ALIEN_CASH_DEPOSIT"),
        c_rem, c_s
    ))
    # Immediate MSB transfer to home country
    mc   = rand_int(6, 15, n)
    nm   = int(mc.sum())
    m_c  = np.repeat(cids, mc)
    m_s  = np.repeat(sts, mc)
    m_hc = np.repeat(home_ctys, mc)
    m_a  = _fast_acct(m_c, acct_pool)
    m_am = rand_uniform(CFG["p6_msb_lo"], CFG["p6_msb_hi"], nm)
    m_op = rand_choice(MSB_OPERATORS, nm)
    m_rem= rand_choice(["Remittance to family","Money transfer - family support",
                          "Send money home","Family support remittance",
                          "International money transfer - family",
                          "Remittance - monthly support"], nm)
    frames.append(_make_txn_frame(
        m_c, m_a, m_am, rand_timestamps(nm), np.full(nm,"MSB Transfer"),
        rand_choice(["Branch","Agent","Online Banking"], nm, weights=[0.50,0.30,0.20]),
        np.full(nm,"Debit"), m_op, m_hc, np.zeros(nm,bool), all_accts, np.full(nm,"USD"),
        np.full(nm,"P6_IllegalAlienMSB"), np.full(nm,"ILLEGAL_ALIEN_MSB_REMITTANCE"),
        m_rem, m_s
    ))
    return pd.concat(frames, ignore_index=True)


def build_p7_txns(chunk: pd.DataFrame, acct_pool: dict, all_accts: np.ndarray) -> pd.DataFrame:
    """Pattern 7: Drug reference in transaction remarks + behavioural signals."""
    frames = []
    n     = len(chunk)
    cids  = chunk["customer_id"].values
    sts   = chunk["residence_state"].astype(str).values

    # Small P2P transfers with drug remarks (core signal)
    dc   = rand_int(10, 25, n)
    nd   = int(dc.sum())
    d_c  = np.repeat(cids, dc)
    d_s  = np.repeat(sts, dc)
    d_a  = _fast_acct(d_c, acct_pool)
    d_am = rand_uniform(CFG["p7_p2p_lo"], CFG["p7_p2p_hi"], nd)
    d_rem= rand_choice(DRUG_REMARKS, nd)
    # Force late-night timestamps
    d_ts = np.array([
        (START_DATE + timedelta(
            days=int(rng.integers(0,183)),
            hours=int(rng.choice([22,23,0,1,2,3,4])),
            minutes=int(rng.integers(0,60))
        )).timestamp() for _ in range(nd)
    ])
    d_dates = pd.to_datetime(d_ts, unit="s").round("s")
    d_cptys = rand_choice([f"User_{i:05d}" for i in range(500)], nd)
    frames.append(_make_txn_frame(
        d_c, d_a, d_am, d_dates, np.full(nd,"P2P Transfer"),
        rand_choice(["Mobile App","Online Banking"], nd, weights=[0.75,0.25]),
        np.full(nd,"Debit"), d_cptys, np.full(nd,"US"),
        np.zeros(nd,bool), all_accts, np.full(nd,"USD"),
        np.full(nd,"P7_DrugReference"), np.full(nd,"DRUG_REF_P2P_PAYMENT"),
        d_rem, d_s
    ))
    # Cash deposits (drug sale proceeds)
    xc   = rand_int(5, 15, n)
    nx   = int(xc.sum())
    x_c  = np.repeat(cids, xc)
    x_s  = np.repeat(sts, xc)
    x_a  = _fast_acct(x_c, acct_pool)
    x_am = rand_uniform(200, 2_500, nx)
    x_rem= rand_choice(["Cash deposit","Daily cash","Cash from work","Cash deposit - misc"], nx)
    frames.append(_make_txn_frame(
        x_c, x_a, x_am, rand_timestamps(nx),
        np.full(nx,"Cash Deposit"), rand_choice(["ATM","Branch"],nx,weights=[0.60,0.40]),
        np.full(nx,"Credit"), np.full(nx,"Cash Deposit"),
        np.full(nx,"US"), np.zeros(nx,bool), all_accts, np.full(nx,"USD"),
        np.full(nx,"P7_DrugReference"), np.full(nx,"DRUG_REF_CASH_PROCEEDS"),
        x_rem, x_s
    ))
    return pd.concat(frames, ignore_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# 9.  NORMAL POPULATION NOISE (11 types)
# ─────────────────────────────────────────────────────────────────────────────

def build_noise_txns(normal_df: pd.DataFrame, acct_pool: dict,
                      all_accts: np.ndarray) -> pd.DataFrame:
    frames = []
    N    = len(normal_df)
    cids = normal_df["customer_id"].values
    sts  = normal_df["residence_state"].astype(str).values

    def sub(pct): return rng.choice(N, size=max(1,int(N*pct)), replace=False)
    def expand(idx, cnt):
        exp_c = np.repeat(cids[idx], cnt)
        exp_s = np.repeat(sts[idx], cnt)
        return exp_c, exp_s, _fast_acct(exp_c, acct_pool)

    # 1. Sub-CTR ATM withdrawals
    idx = sub(CFG["noise_sub_ctr_pct"]); cnt = rand_int(2,4,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt); ws=START_DATE+timedelta(days=int(rng.integers(0,150)))
    frames.append(_make_txn_frame(ec,ea,rand_uniform(8000,9500,n),rand_timestamps(n,ws,ws+timedelta(days=30)),
        np.full(n,"ATM Withdrawal"),np.full(n,"ATM"),np.full(n,"Debit"),
        rand_choice(MCC_CATALOGUE["ATM Withdrawal"][3],n),np.full(n,"US"),
        np.zeros(n,bool),all_accts,np.full(n,"USD"),np.full(n,"Normal"),
        np.full(n,"NOISE_SUB_CTR_WITHDRAWAL"),
        rand_choice(["ATM cash for contractor","Cash withdrawal - personal use","Sub-threshold ATM"],n),es))

    # 2. Legit international wire
    idx = sub(CFG["noise_legit_intl_pct"]); cnt = rand_int(1,2,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    d_ctys = rand_choice(["IN","MX","PH","CA","DE","GB"],n)
    frames.append(_make_txn_frame(ec,ea,rand_uniform(5000,40000,n),rand_timestamps(n),
        np.full(n,"Intl Wire"),rand_choice(["Wire","Branch"],n,weights=[0.70,0.30]),np.full(n,"Debit"),
        rand_choice(["University Fee","Family Remittance","Property Deposit","Medical Payment"],n),
        d_ctys,np.zeros(n,bool),all_accts,np.full(n,"USD"),np.full(n,"Normal"),
        np.full(n,"NOISE_LEGIT_INTL_WIRE"),
        rand_choice(["International wire - family support","Overseas property payment","Tuition remittance"],n),es))

    # 3. Freelancer ACH inflows
    idx = sub(CFG["noise_freelancer_pct"]); cnt = rand_int(3,6,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    frames.append(_make_txn_frame(ec,ea,rand_uniform(500,8000,n),rand_timestamps(n),
        np.full(n,"Inbound ACH"),np.full(n,"ACH"),np.full(n,"Credit"),
        rand_choice(FREELANCER_PAYERS,n),np.full(n,"US"),np.zeros(n,bool),all_accts,
        np.full(n,"USD"),np.full(n,"Normal"),np.full(n,"NOISE_FREELANCER_ACH"),
        rand_choice(["Freelance payment received","Gig income deposit","Project payment"],n),es))

    # 4. Bulk gift cards
    idx = sub(CFG["noise_giftcard_pct"]); cnt = rand_int(3,8,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    ws=START_DATE+timedelta(days=int(rng.integers(0,168)))
    frames.append(_make_txn_frame(ec,ea,rand_uniform(50,300,n),rand_timestamps(n,ws,ws+timedelta(days=14)),
        np.full(n,"Gift Cards"),np.full(n,"POS"),np.full(n,"Debit"),
        rand_choice(MCC_CATALOGUE["Gift Cards"][3],n),np.full(n,"US"),
        np.zeros(n,bool),all_accts,np.full(n,"USD"),np.full(n,"Normal"),
        np.full(n,"NOISE_BULK_GIFTCARD"),
        rand_choice(["Gift card purchase - holiday gifting","Corporate gift cards","Birthday gifts"],n),es))

    # 5. Round amount domestic transfers
    idx = sub(CFG["noise_round_amt_pct"]); cnt = rand_int(2,4,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    rnd_amts = rand_choice([5000.0,10000.0,15000.0,20000.0,25000.0],n,weights=[0.35,0.30,0.15,0.12,0.08]).astype(float)
    frames.append(_make_txn_frame(ec,ea,rnd_amts,rand_timestamps(n),
        np.full(n,"Wire Transfer"),rand_choice(["Wire","ACH"],n,weights=[0.50,0.50]),np.full(n,"Debit"),
        rand_choice(["Landlord - Rent","Loan Repayment","Family Transfer","Down Payment"],n),
        np.full(n,"US"),rng.random(n)<0.30,all_accts,np.full(n,"USD"),np.full(n,"Normal"),
        np.full(n,"NOISE_ROUND_AMT_DOMESTIC"),
        rand_choice(["Monthly rent payment","Personal loan repayment","Round transfer - domestic"],n),es))

    # 6. HRC travel burst
    idx = sub(CFG["noise_hrc_travel_pct"]); cnt = rand_int(10,20,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    hrc_ctys = rand_choice(["CN","HK","RU","VN","MM"],n,weights=[0.35,0.25,0.20,0.12,0.08])
    ws=START_DATE+timedelta(days=int(rng.integers(0,170)))
    frames.append(_make_txn_frame(ec,ea,rand_uniform(20,600,n),rand_timestamps(n,ws,ws+timedelta(days=10)),
        rand_choice(["Restaurant","Travel - Hotel","Retail - General"],n),np.full(n,"POS"),np.full(n,"Debit"),
        rand_choice(["Hotel Stay","Restaurant","Local Transport","Souvenir Shop"],n),
        hrc_ctys,np.zeros(n,bool),all_accts,np.full(n,"USD"),np.full(n,"Normal"),
        np.full(n,"NOISE_HRC_TRAVEL_BURST"),
        rand_choice(["Business travel expense","Hotel accommodation abroad","Travel dining"],n),es))

    # 7. Velocity spike
    idx = sub(CFG["noise_velocity_pct"]); cnt = rand_int(15,25,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    ws=START_DATE+timedelta(days=int(rng.integers(5,178)))
    frames.append(_make_txn_frame(ec,ea,np.exp(rng.normal(4.2,0.9,n)).clip(10,2000).round(2),
        rand_timestamps(n,ws,ws+timedelta(days=3)),
        rand_choice(["Retail - General","Grocery","Restaurant","Online Services"],n),
        rand_choice(["POS","Online Banking","Mobile App"],n,weights=[0.40,0.35,0.25]),
        np.full(n,"Debit"),rand_choice(["Amazon","Target","Walmart","Best Buy"],n),
        np.full(n,"US"),np.zeros(n,bool),all_accts,np.full(n,"USD"),np.full(n,"Normal"),
        np.full(n,"NOISE_VELOCITY_SPIKE"),
        rand_choice(["Shopping spree - home renovation","Back to school purchase","General retail"],n),es))

    # 8. Large inbound + redistribution
    idx = sub(CFG["noise_large_inbound_pct"])
    n_c = len(idx); in_aids = _fast_acct(cids[idx], acct_pool)
    in_am = rand_uniform(30000,150000,n_c)
    in_src= rand_choice(["Estate Settlement","Fidelity Investments","State Farm Insurance",
                          "Court Settlement","Charles Schwab","Tax Refund"],n_c)
    in_dts= rand_timestamps(n_c,START_DATE,START_DATE+timedelta(days=30))
    frames.append(_make_txn_frame(
        cids[idx],in_aids,in_am,in_dts,np.full(n_c,"Wire Transfer"),
        np.full(n_c,"Wire"),np.full(n_c,"Credit"),in_src,np.full(n_c,"US"),
        np.zeros(n_c,bool),all_accts,np.full(n_c,"USD"),np.full(n_c,"Normal"),
        np.full(n_c,"NOISE_LARGE_INBOUND_REDISTRIB"),
        np.array([f"Inheritance/settlement - {s}" for s in in_src],dtype=object),sts[idx]))
    out_cnt = rand_int(3,8,n_c); n_out=int(out_cnt.sum())
    o_c=np.repeat(cids[idx],out_cnt); o_s=np.repeat(sts[idx],out_cnt)
    o_a=_fast_acct(o_c,acct_pool)
    o_am_base=np.repeat(in_am,out_cnt)
    o_am=(o_am_base/np.repeat(out_cnt,out_cnt)*rand_uniform(0.15,0.30,n_out)).round(2)
    o_dts=np.repeat(in_dts,out_cnt)+pd.to_timedelta(rng.integers(1,15,n_out),unit="D")
    frames.append(_make_txn_frame(
        o_c,o_a,o_am,o_dts,np.full(n_out,"Wire Transfer"),
        rand_choice(["Wire","ACH"],n_out,weights=[0.60,0.40]),np.full(n_out,"Debit"),
        rand_choice(["Morgan Stanley","TD Ameritrade","Family Member","Mortgage Payoff"],n_out),
        rand_choice(["US","UK","CA"],n_out,weights=[0.70,0.15,0.15]),
        np.zeros(n_out,bool),all_accts,np.full(n_out,"USD"),np.full(n_out,"Normal"),
        np.full(n_out,"NOISE_LARGE_INBOUND_REDISTRIB"),
        rand_choice(["Redistribution - investment","Estate distribution payment"],n_out),o_s))

    # 9. Odd-hours transactions
    idx = sub(CFG["noise_odd_hours_pct"]); cnt = rand_int(5,15,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    night_ts=np.array([(START_DATE+timedelta(days=int(rng.integers(0,183)),
                         hours=int(rng.choice([22,23,0,1,2,3,4])),
                         minutes=int(rng.integers(0,60)))).timestamp() for _ in range(n)])
    night_dates=pd.to_datetime(night_ts,unit="s").round("s")
    frames.append(_make_txn_frame(ec,ea,np.exp(rng.normal(4.0,1.0,n)).clip(5,500).round(2),
        night_dates,rand_choice(["Online Services","Retail - General","P2P Transfer"],n),
        rand_choice(["Online Banking","Mobile App"],n,weights=[0.50,0.50]),
        np.full(n,"Debit"),rand_choice(["Netflix","Amazon","Zelle","Online Merchant"],n),
        np.full(n,"US"),rng.random(n)<0.20,all_accts,np.full(n,"USD"),np.full(n,"Normal"),
        np.full(n,"NOISE_ODD_HOURS"),
        rand_choice(["Late night online purchase","Night shift worker transaction"],n),es))

    # 10. Legit CN airline
    idx = sub(CFG["noise_cn_airline_pct"]); cnt = rand_int(1,3,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    cn_al=rand_choice(["Air China","China Eastern Airlines","Cathay Pacific","Hainan Airlines"],n)
    frames.append(_make_txn_frame(ec,ea,rand_uniform(400,1800,n),rand_timestamps(n),
        np.full(n,"CN Airline"),rand_choice(["Online Banking","Mobile App"],n,weights=[0.60,0.40]),
        np.full(n,"Debit"),cn_al,np.full(n,"CN"),np.zeros(n,bool),all_accts,np.full(n,"USD"),
        np.full(n,"Normal"),np.full(n,"NOISE_CN_AIRLINE_LEGIT"),
        rand_choice(["Airline ticket - China visit","Flight to China - family visit","Business trip flight"],n),es))

    # 11. Dormancy reactivation
    idx = sub(CFG["noise_dormancy_pct"]); cnt = rand_int(8,20,len(idx))
    n=int(cnt.sum()); ec,es,ea = expand(idx,cnt)
    react_s=END_DATE-timedelta(days=30); react_e=END_DATE
    frames.append(_make_txn_frame(ec,ea,np.exp(rng.normal(4.2,1.0,n)).clip(5,1000).round(2),
        rand_timestamps(n,react_s,react_e),
        rand_choice(["Grocery","Restaurant","Gas Station","Utilities"],n),
        rand_choice(["POS","Mobile App","Online Banking"],n,weights=[0.50,0.30,0.20]),
        np.full(n,"Debit"),rand_choice(["Walmart","Starbucks","Shell","AT&T"],n),
        np.full(n,"US"),np.zeros(n,bool),all_accts,np.full(n,"USD"),np.full(n,"Normal"),
        np.full(n,"NOISE_DORMANCY_REACTIVATION"),
        rand_choice(["Post-dormancy regular purchase","Reactivated account spend"],n),es))

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# 10.  POST-TRANSACTION RUNNING BALANCE  (vectorised)
# ─────────────────────────────────────────────────────────────────────────────

def compute_running_balance(txn_df: pd.DataFrame,
                             acct_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute post_transaction_balance per account as a running balance.
    Logic:
      signed_amount = +amount (Credit) or -amount (Debit)
      opening_balance = current_balance - total_net_flow_in_window
      post_transaction_balance[i] = opening_balance + cumsum(signed)[i]
    This ensures the last transaction for each account leaves a balance
    equal to current_balance in the accounts table.
    """
    curr_bal = acct_df.set_index("account_id")["current_balance"].to_dict()

    txn_df   = txn_df.sort_values(["account_id","transaction_datetime"]).copy()
    txn_df["_signed"] = np.where(
        txn_df["debit_credit_indicator"] == "Credit",
        txn_df["transaction_amount_usd"],
        -txn_df["transaction_amount_usd"]
    )
    txn_df["_cumsum"] = txn_df.groupby("account_id")["_signed"].cumsum()
    total_net = txn_df.groupby("account_id")["_signed"].sum()

    opening = {
        acct: max(100.0, curr_bal.get(acct, 1000.0) - total_net.get(acct, 0.0))
        for acct in txn_df["account_id"].unique()
    }
    txn_df["post_transaction_balance"] = (
        txn_df["account_id"].map(opening) + txn_df["_cumsum"]
    ).round(2)
    txn_df.drop(columns=["_signed","_cumsum"], inplace=True)
    return txn_df

# ─────────────────────────────────────────────────────────────────────────────
# 11.  ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_transactions(cust_df: pd.DataFrame,
                           acct_df: pd.DataFrame) -> pd.DataFrame:
    acct_pool = _build_acct_pool(acct_df)
    all_accts = acct_df["account_id"].values
    chunk_sz  = CFG["chunk_customers"]

    seg = {p: cust_df[cust_df.aml_pattern==p].reset_index(drop=True)
           for p in cust_df["aml_pattern"].unique()}

    all_frames = []

    # Normal base
    normal_df = seg.get("Normal", pd.DataFrame())
    n_chunks  = max(1, (len(normal_df) + chunk_sz - 1) // chunk_sz)
    print(f"  Normal: {len(normal_df):,} customers / {n_chunks} chunks")
    for i in range(n_chunks):
        ch = normal_df.iloc[i*chunk_sz:(i+1)*chunk_sz]
        all_frames.append(build_normal_txns(ch, acct_pool, all_accts))
        if (i+1) % 2 == 0:
            print(f"    chunk {i+1}/{n_chunks}  frames so far={len(all_frames)}")
        gc.collect()

    # Normal noise
    print(f"  Building noise transactions …")
    noise = build_noise_txns(normal_df, acct_pool, all_accts)
    if len(noise): all_frames.append(noise)
    print(f"    noise rows: {len(noise):,}")

    # Typology segments
    builders = {
        "P1_ChinaStructuring" : build_p1_txns,
        "P2_MoneyMule_CMLN"   : build_p2_txns,
        "P3_RapidMovement"    : build_p3_txns,
        "P4_Smurfing"         : build_p4_txns,
        "P5_RussianOligarch"  : build_p5_txns,
        "P6_IllegalAlienMSB"  : build_p6_txns,
        "P7_DrugReference"    : build_p7_txns,
    }
    for pat, fn in builders.items():
        df_seg = seg.get(pat, pd.DataFrame())
        if len(df_seg) == 0: continue
        print(f"  {pat}: {len(df_seg):,} customers")
        built = fn(df_seg, acct_pool, all_accts)
        all_frames.append(built)
        gc.collect()

    print("  Concatenating all frames …")
    txn_df = pd.concat(all_frames, ignore_index=True)
    del all_frames; gc.collect()

    print("  Computing running balances …")
    txn_df = compute_running_balance(txn_df, acct_df)

    txn_df.sort_values("transaction_datetime", inplace=True)
    txn_df.reset_index(drop=True, inplace=True)
    return txn_df

# ─────────────────────────────────────────────────────────────────────────────
# 12.  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    import time
    t0 = time.time()
    print("=" * 68)
    print("  SYNTHETIC AML DATA GENERATOR v4  —  Retail Banking")
    print("=" * 68)
    print(f"  Window   : {START_DATE.date()}  →  {END_DATE.date()}  (6 months)")
    print(f"  Training : {START_DATE.date()}  →  {TRAIN_CUT.date()}  (first 4 months)")
    print(f"  Testing  : {TRAIN_CUT.date()}   →  {END_DATE.date()}  (last 2 months)")
    print(f"  n_normal : {CFG['n_normal']:,}")

    print("\n[1/3] Generating customers …")
    cust_df = generate_customers()
    pat_counts = cust_df["aml_pattern"].value_counts()
    print(f"  Total customers : {len(cust_df):,}")
    print(pat_counts.to_string())
    print(f"  Columns ({len(cust_df.columns)}): {list(cust_df.columns)}")
    print(f"  Memory : {cust_df.memory_usage(deep=True).sum()/1e6:.1f} MB")

    print("\n[2/3] Generating accounts …")
    acct_df = generate_accounts(cust_df)
    print(f"  Total accounts : {len(acct_df):,}")
    print(acct_df["account_type"].value_counts().to_string())
    print(f"  Columns ({len(acct_df.columns)}): {list(acct_df.columns)}")
    print(f"  Memory : {acct_df.memory_usage(deep=True).sum()/1e6:.1f} MB")

    print("\n[3/3] Generating transactions …")
    txn_df = generate_transactions(cust_df, acct_df)
    print(f"\n  Total transactions : {len(txn_df):,}")
    print(f"  Date range : {txn_df['transaction_datetime'].min()}  →  {txn_df['transaction_datetime'].max()}")
    print(f"  Columns ({len(txn_df.columns)}): {list(txn_df.columns)}")
    print(f"  Memory : {txn_df.memory_usage(deep=True).sum()/1e6:.1f} MB")

    print("\n── AML flag distribution ────────────────────────────────────────")
    print(txn_df["aml_flag"].value_counts().to_string())

    print("\n── AML pattern distribution (transactions) ──────────────────────")
    print(txn_df["aml_pattern_label"].value_counts().to_string())

    print("\n── Cross-currency sample ────────────────────────────────────────")
    xc = txn_df[txn_df["orig_currency"] != txn_df["bene_currency"]]
    print(f"  Cross-currency rows: {len(xc):,}")
    if len(xc):
        print(xc[["transaction_amount_usd","orig_currency","orig_curr_amount",
                   "bene_currency","bene_curr_amount","counterparty_country"]].head(3).to_string(index=False))

    print("\n── ID format samples ────────────────────────────────────────────")
    print(f"  customer_id    : {cust_df['customer_id'].iloc[0]}")
    print(f"  account_id     : {acct_df['account_id'].iloc[0]}")
    print(f"  transaction_id : {txn_df['transaction_id'].iloc[0]}")

    print("\n── Drug remarks sample (P7) ─────────────────────────────────────")
    drug_txns = txn_df[txn_df["aml_flag"]=="DRUG_REF_P2P_PAYMENT"]
    if len(drug_txns):
        print(drug_txns["transaction_remarks"].head(5).to_string())

    print("\n── Running balance sample ───────────────────────────────────────")
    sample_acct = txn_df["account_id"].iloc[0]
    bal_sample  = txn_df[txn_df["account_id"]==sample_acct][
        ["transaction_datetime","debit_credit_indicator",
         "transaction_amount_usd","post_transaction_balance"]].head(5)
    print(bal_sample.to_string(index=False))

    elapsed = time.time() - t0
    print(f"\n✓  Done in {elapsed:.1f}s")
    print("=" * 68)
    print("  Returning: (customers_df, accounts_df, transactions_df)")
    return cust_df, acct_df, txn_df


if __name__ == "__main__":
    customers_df, accounts_df, transactions_df = main()
    customers_df.to_csv(CUST_PATH, index=False)
    del customers_df
    accounts_df.to_csv(ACCT_PATH, index=False)
    del accounts_df
    transactions_df.to_csv(TXN_PATH, index=False)
    del transactions_df
    gc.collect()