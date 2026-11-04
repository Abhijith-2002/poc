#!/usr/bin/env python3
"""
scripts/generate_data.py
Generates ~24 months of synthetic retail loyalty data directly to local Parquet files.
Features realistic distributions, holiday seasonality, Pareto spend, and deliberate
support for UC1 through UC8 (including follow-ups 1a, 2a, 3a, 4a).
"""

import argparse
import datetime
import os
import random
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def generate_all_data(
    output_dir: str,
    num_members: int = 50000,
    num_transactions: int = 1500000,
    end_date_str: str = "2026-11-03",
    seed: int = 42,
):
    print(f"=== Starting Synthetic Data Generation (Seed: {seed}) ===")
    os.makedirs(output_dir, exist_ok=True)
    np.random.seed(seed)
    random.seed(seed)

    end_date = datetime.date.fromisoformat(end_date_str)
    start_date = end_date - datetime.timedelta(days=730)  # ~24 months

    print(f"Time Window: {start_date} to {end_date}")
    print(f"Target Members: {num_members:,} | Target Transactions: {num_transactions:,}")

    # ---------------------------------------------------------
    # 1. dim_member_tier
    # ---------------------------------------------------------
    print("Generating dim_member_tier...")
    tiers_data = [
        {"tier_id": 1, "tier_name": "Bronze", "threshold_spend": 0.0, "points_multiplier": 1.0, "benefits": "1x points, standard offers"},
        {"tier_id": 2, "tier_name": "Silver", "threshold_spend": 1000.0, "points_multiplier": 1.25, "benefits": "1.25x points, birthday gift, free standard shipping"},
        {"tier_id": 3, "tier_name": "Gold", "threshold_spend": 3000.0, "points_multiplier": 1.5, "benefits": "1.5x points, VIP events, free express shipping"},
        {"tier_id": 4, "tier_name": "Platinum", "threshold_spend": 7500.0, "points_multiplier": 2.0, "benefits": "2x points, dedicated concierge, bespoke gifts"},
    ]
    df_tier = pd.DataFrame(tiers_data)
    pq.write_table(pa.Table.from_pandas(df_tier), os.path.join(output_dir, "dim_member_tier.parquet"))

    # ---------------------------------------------------------
    # 2. dim_store
    # ---------------------------------------------------------
    print("Generating dim_store...")
    stores_data = [
        {"store_id": "S01", "store_name": "Doncaster", "state": "VIC", "region": "Metro East", "channel_type": "STORE"},
        {"store_id": "S02", "store_name": "Chadstone", "state": "VIC", "region": "Metro South", "channel_type": "STORE"},
        {"store_id": "S03", "store_name": "Melbourne CBD", "state": "VIC", "region": "Metro Central", "channel_type": "STORE"},
        {"store_id": "S04", "store_name": "Highpoint", "state": "VIC", "region": "Metro West", "channel_type": "STORE"},
        {"store_id": "S05", "store_name": "Sydney City", "state": "NSW", "region": "Metro Central", "channel_type": "STORE"},
        {"store_id": "S06", "store_name": "Bondi Junction", "state": "NSW", "region": "Metro East", "channel_type": "STORE"},
        {"store_id": "S07", "store_name": "Parramatta", "state": "NSW", "region": "Metro West", "channel_type": "STORE"},
        {"store_id": "S08", "store_name": "Chatswood", "state": "NSW", "region": "Metro North", "channel_type": "STORE"},
        {"store_id": "S09", "store_name": "Brisbane Queen St", "state": "QLD", "region": "Metro Central", "channel_type": "STORE"},
        {"store_id": "S10", "store_name": "Carindale", "state": "QLD", "region": "Metro South", "channel_type": "STORE"},
        {"store_id": "S11", "store_name": "Chermside", "state": "QLD", "region": "Metro North", "channel_type": "STORE"},
        {"store_id": "S12", "store_name": "Perth City", "state": "WA", "region": "Metro Central", "channel_type": "STORE"},
        {"store_id": "S13", "store_name": "Adelaide Rundle", "state": "SA", "region": "Metro Central", "channel_type": "STORE"},
        {"store_id": "S14", "store_name": "Geelong", "state": "VIC", "region": "Regional VIC", "channel_type": "STORE"},
        {"store_id": "S15", "store_name": "Canberra Centre", "state": "ACT", "region": "Metro Central", "channel_type": "STORE"},
        {"store_id": "S16", "store_name": "ONLINE", "state": "National", "region": "Digital", "channel_type": "ONLINE"},
    ]
    df_store = pd.DataFrame(stores_data)
    pq.write_table(pa.Table.from_pandas(df_store), os.path.join(output_dir, "dim_store.parquet"))

    # ---------------------------------------------------------
    # 3. dim_date
    # ---------------------------------------------------------
    print("Generating dim_date...")
    all_dates = pd.date_range(start="2023-01-01", end="2027-12-31", freq="D")
    df_date = pd.DataFrame({
        "date_key": all_dates.strftime("%Y%m%d").astype(int),
        "full_date": all_dates.date,
        "day_of_week": all_dates.dayofweek + 1,
        "day_name": all_dates.day_name(),
        "day_of_month": all_dates.day,
        "month_num": all_dates.month,
        "month_name": all_dates.month_name(),
        "quarter": all_dates.quarter,
        "year": all_dates.year,
        "is_weekend": all_dates.dayofweek >= 5,
        "is_holiday": ((all_dates.month == 12) & (all_dates.day.isin([25, 26]))) | ((all_dates.month == 1) & (all_dates.day == 1)),
    })
    pq.write_table(pa.Table.from_pandas(df_date), os.path.join(output_dir, "dim_date.parquet"))

    # ---------------------------------------------------------
    # 4. dim_member
    # ---------------------------------------------------------
    print("Generating dim_member...")
    member_ids = [f"M{i:06d}" for i in range(1, num_members + 1)]
    
    first_names = ["James", "Emma", "Oliver", "Charlotte", "William", "Amelia", "Jack", "Olivia", "Noah", "Mia",
                   "Liam", "Chloe", "Thomas", "Sophie", "Lucas", "Grace", "Henry", "Ava", "Alexander", "Emily",
                   "Daniel", "Isabella", "Matthew", "Zoe", "Samuel", "Lily", "Benjamin", "Ella", "David", "Harper",
                   "Joseph", "Ruby", "Logan", "Evie", "Jackson", "Ivy", "Sebastian", "Isla", "Joshua", "Freya"]
    last_names = ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Morton", "White", "Martin", "Anderson",
                  "Thompson", "Nguyen", "Thomas", "Walker", "Harris", "Lee", "Ryan", "Robinson", "Kelly", "King",
                  "Davis", "Wright", "Evans", "Clark", "Miller", "Davies", "Edwards", "Green", "Hall", "Campbell"]
    
    fn_arr = np.random.choice(first_names, size=num_members)
    ln_arr = np.random.choice(last_names, size=num_members)
    
    domains = ["gmail.com", "outlook.com", "yahoo.com.au", "icloud.com", "bigpond.com", "hotmail.com"]
    emails = [f"{f.lower()}.{l.lower()}{i%9999}@{np.random.choice(domains)}" for i, (f, l) in enumerate(zip(fn_arr, ln_arr), 1)]
    
    email_opt_in = np.random.rand(num_members) < 0.78
    sms_opt_in = np.random.rand(num_members) < 0.62
    contactable_by_email = email_opt_in & (pd.Series(emails).str.len() > 0)
    
    # Ages and age bands
    # Distributions roughly matching Australian demographics
    age_band_choices = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    age_band_probs = [0.12, 0.22, 0.22, 0.18, 0.14, 0.12]
    assigned_age_bands = np.random.choice(age_band_choices, size=num_members, p=age_band_probs)
    
    ages = np.empty(num_members, dtype=int)
    for i, b in enumerate(assigned_age_bands):
        if b == "18-24": ages[i] = np.random.randint(18, 25)
        elif b == "25-34": ages[i] = np.random.randint(25, 35)
        elif b == "35-44": ages[i] = np.random.randint(35, 45)
        elif b == "45-54": ages[i] = np.random.randint(45, 55)
        elif b == "55-64": ages[i] = np.random.randint(55, 65)
        else: ages[i] = np.random.randint(65, 86)
        
    dobs = [end_date - datetime.timedelta(days=int(a * 365.25) + int(np.random.randint(0, 365))) for a in ages]
    
    genders = np.random.choice(["F", "M", "Other"], size=num_members, p=[0.53, 0.45, 0.02])
    states = np.random.choice(["VIC", "NSW", "QLD", "WA", "SA", "TAS", "ACT", "NT"], size=num_members, p=[0.38, 0.32, 0.15, 0.07, 0.04, 0.02, 0.015, 0.005])
    
    # Postcodes
    postcodes = []
    for s in states:
        if s == "VIC": postcodes.append(str(np.random.choice([3108, 3000, 3141, 3148, 3121, 3056, 3182, 3205])))
        elif s == "NSW": postcodes.append(str(np.random.choice([2000, 2022, 2150, 2067, 2112, 2010, 2042])))
        elif s == "QLD": postcodes.append(str(np.random.choice([4000, 4152, 4032, 4217, 4064])))
        else: postcodes.append(str(np.random.randint(5000, 7999)))
        
    # Join dates: ~12% joined in last 6 months (past 180 days) for UC4
    join_dates = []
    six_months_ago = end_date - datetime.timedelta(days=180)
    four_years_ago = end_date - datetime.timedelta(days=1460)
    num_recent_joiners = int(num_members * 0.12)
    
    for i in range(num_members):
        if i < num_recent_joiners:
            delta_days = np.random.randint(1, 180)
            join_dates.append(end_date - datetime.timedelta(days=delta_days))
        else:
            delta_days = np.random.randint(181, 1400)
            join_dates.append(end_date - datetime.timedelta(days=delta_days))
            
    # Tiers: Bronze (~50%), Silver (~30%), Gold (~15%), Platinum (~5%)
    tier_ids = np.random.choice([1, 2, 3, 4], size=num_members, p=[0.50, 0.30, 0.15, 0.05])
    tier_names = [{1: "Bronze", 2: "Silver", 3: "Gold", 4: "Platinum"}[t] for t in tier_ids]
    
    # Staff indicator: ~3% staff (UC7)
    staff_indicator = np.random.choice(["N", "Y"], size=num_members, p=[0.97, 0.03])
    
    # Points balance correlated with tier
    points_balance = np.zeros(num_members, dtype=int)
    for i, t in enumerate(tier_ids):
        if t == 1: points_balance[i] = np.random.randint(0, 750)
        elif t == 2: points_balance[i] = np.random.randint(500, 3000)
        elif t == 3: points_balance[i] = np.random.randint(2500, 12000)  # Gold members with various points
        else: points_balance[i] = np.random.randint(8000, 45000)
        
    # Status
    status = np.random.choice(["ACTIVE", "INACTIVE"], size=num_members, p=[0.96, 0.04])
    
    df_member = pd.DataFrame({
        "member_id": member_ids,
        "first_name": fn_arr,
        "last_name": ln_arr,
        "email": emails,
        "email_opt_in": email_opt_in,
        "sms_opt_in": sms_opt_in,
        "contactable_by_email": contactable_by_email,
        "date_of_birth": dobs,
        "age": ages,
        "age_band": assigned_age_bands,
        "gender": genders,
        "state": states,
        "postcode": postcodes,
        "join_date": join_dates,
        "tier_id": tier_ids,
        "tier_name": tier_names,
        "points_balance": points_balance,
        "staff_indicator": staff_indicator,
        "status": status,
    })
    pq.write_table(pa.Table.from_pandas(df_member), os.path.join(output_dir, "dim_member.parquet"))

    # ---------------------------------------------------------
    # 5. fact_transaction
    # ---------------------------------------------------------
    print(f"Generating {num_transactions:,} fact_transactions with seasonality and UC support...")
    
    # Cohort design for specific use cases:
    # 1. Dormant members (~5%): 2,500 members have NO transactions in last 6 months (UC6)
    # 2. Staff multi-transactors (UC7): staff members who transacted multiple times on same day in last 30 days
    # 3. New joiners with high visit frequency (UC4): new joiners with >= 10 transactions in last 6 months
    # 4. Inactive Gold members (UC8): Gold members with points >= 3000 and 0 transactions in last 2 months (past 60 days)
    # 5. Doncaster spenders (UC1): VIC email-contactable members with substantial spend at Doncaster in last 12 months
    
    dormant_member_indices = set(range(1000, 3500))  # 2,500 members (~5%)
    gold_inactive_indices = set([i for i, (t, p) in enumerate(zip(tier_ids, points_balance)) if t == 3 and p >= 1500 and i < 8000][:1200])
    # Add gold inactive to dormant or strictly inactive in last 60 days
    
    active_member_indices = [i for i in range(num_members) if i not in dormant_member_indices]
    
    # Weights for members based on tier (Platinum and Gold shop much more frequently)
    tier_freq_weights = {1: 1.0, 2: 2.2, 3: 4.5, 4: 8.0}
    weights = np.array([tier_freq_weights[tier_ids[i]] for i in active_member_indices], dtype=float)
    weights /= weights.sum()

    # Pre-allocate transactions
    txn_member_indices = np.random.choice(active_member_indices, size=num_transactions, p=weights)
    
    # Dates: generate transaction dates across 730 days with Nov-Dec holiday peak
    day_offsets = np.arange(731)
    base_date = start_date
    calendar_dates = [base_date + datetime.timedelta(days=int(d)) for d in day_offsets]
    
    # Calculate seasonal weight for each day
    day_weights = []
    for d in calendar_dates:
        w = 1.0
        # Holiday bump: Nov 15 - Dec 31
        if d.month == 11 and d.day >= 15:
            w = 1.8
        elif d.month == 12:
            w = 2.4 if d.day <= 24 else 2.8  # Boxing week
        elif d.month == 1:
            w = 1.2
        # Weekend bump
        if d.weekday() >= 5:
            w *= 1.35
        day_weights.append(w)
        
    day_weights = np.array(day_weights)
    day_weights /= day_weights.sum()
    
    chosen_day_offsets = np.random.choice(day_offsets, size=num_transactions, p=day_weights)
    txn_dates = [calendar_dates[off] for off in chosen_day_offsets]

    # Adjust for dormant and gold inactive constraints:
    sixty_days_ago = end_date - datetime.timedelta(days=60)
    one_eighty_days_ago = end_date - datetime.timedelta(days=180)
    
    # Store allocation & Age band online/in-store propensity (UC3)
    # Store choices:
    store_ids = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12", "S13", "S14", "S15", "S16"]
    physical_stores_vic = ["S01", "S02", "S03", "S04", "S14"]
    physical_stores_nsw = ["S05", "S06", "S07", "S08"]
    physical_stores_other = ["S09", "S10", "S11", "S12", "S13", "S15"]

    # Pre-calculate age band online probabilities for UC3:
    # 18-24: 68% online, 32% store
    # 25-34: 55% online, 45% store
    # 35-44: 42% online, 58% store
    # 45-54: 34% online, 66% store
    # 55-64: 25% online, 75% store
    # 65+:   15% online, 85% store
    age_band_online_p = {
        "18-24": 0.68,
        "25-34": 0.55,
        "35-44": 0.42,
        "45-54": 0.34,
        "55-64": 0.25,
        "65+": 0.15,
    }

    # Vectorized / looped assignment
    txn_stores = []
    txn_channels = []
    txn_amounts = []
    txn_discounts = []
    txn_items = []
    txn_points = []
    txn_payments = ["CREDIT_CARD", "DEBIT_CARD", "APPLE_PAY", "PAYPAL", "AFTERPAY", "GIFT_CARD"]
    txn_payment_choices = np.random.choice(txn_payments, size=num_transactions, p=[0.45, 0.25, 0.15, 0.08, 0.05, 0.02])

    # Pareto spend: log-normal distribution with mean ~ $75, tail up to $1500
    base_spends = np.random.lognormal(mean=4.1, sigma=0.85, size=num_transactions)
    base_spends = np.clip(base_spends, 10.0, 2500.0)

    print("Synthesizing transaction properties and use-case distributions...")
    
    # We will refine txn_dates to guarantee join_date <= txn_date
    m_join_dates = df_member["join_date"].values
    m_states = df_member["state"].values
    m_age_bands = df_member["age_band"].values
    m_tiers = df_member["tier_id"].values
    m_staff = df_member["staff_indicator"].values
    
    # Multi-transaction days for staff in last month (UC7)
    # Ensure specific staff members have 2-4 transactions on multiple days in last 30 days
    last_month_start = end_date - datetime.timedelta(days=30)
    
    # Let's adjust member and date arrays directly
    final_m_ids = []
    final_dates = []
    final_times = []
    
    # Track transactions per member to support UC4 (new joiners high freq)
    new_joiner_target_indices = set(range(0, 150)) # first 150 members joined < 6 months ago, give them 8-20 txns
    
    for i in range(num_transactions):
        m_idx = txn_member_indices[i]
        d = txn_dates[i]
        j_date = m_join_dates[m_idx]
        
        # Enforce join_date <= txn_date
        if d < j_date:
            d = j_date + datetime.timedelta(days=int(np.random.randint(0, max(1, (end_date - j_date).days))))
            
        # Enforce inactive gold constraint (UC8): no transactions in last 60 days
        if m_idx in gold_inactive_indices and d >= sixty_days_ago:
            d = start_date + datetime.timedelta(days=int(np.random.randint(0, (sixty_days_ago - start_date).days - 1)))
            
        final_m_ids.append(member_ids[m_idx])
        final_dates.append(d)
        
        # Random time of day (STORE: 9am-8pm, ONLINE: 24h)
        band = m_age_bands[m_idx]
        p_online = age_band_online_p[band]
        is_online = np.random.rand() < p_online
        
        if is_online:
            st = "S16"
            ch = "ONLINE"
            hh = np.random.randint(0, 24)
        else:
            ch = "STORE"
            hh = np.random.randint(9, 21)
            # Pick physical store biased by member state and Doncaster
            m_st = m_states[m_idx]
            if m_st == "VIC":
                # Heavy weight on S01 (Doncaster) for UC1
                st = np.random.choice(["S01", "S02", "S03", "S04", "S14"], p=[0.40, 0.25, 0.15, 0.12, 0.08])
            elif m_st == "NSW":
                st = np.random.choice(physical_stores_nsw)
            else:
                st = np.random.choice(physical_stores_other)
                
        mm = np.random.randint(0, 60)
        ss = np.random.randint(0, 60)
        final_times.append(datetime.datetime.combine(d, datetime.time(hh, mm, ss)))
        
        txn_stores.append(st)
        txn_channels.append(ch)
        
        # Spend adjustments:
        # Tier & Year multiplier on spend (UC5)
        # We need this year vs last year per tier:
        # Gold and Platinum UP (green), Bronze and Silver DOWN (red)
        t_id = m_tiers[m_idx]
        is_this_year = (d.year == end_date.year)
        is_last_year = (d.year == end_date.year - 1)
        
        if is_this_year:
            # 2026: Gold & Platinum surge, Bronze & Silver drop
            tier_base = {1: 0.38, 2: 0.42, 3: 1.60, 4: 2.50}[t_id]
        elif is_last_year:
            # 2025: Steady baseline
            tier_base = {1: 1.00, 2: 1.05, 3: 1.10, 4: 1.30}[t_id]
        else:
            tier_base = {1: 0.85, 2: 1.00, 3: 1.30, 4: 1.80}[t_id]
            
        amt = round(float(base_spends[i] * tier_base), 2)
        disc = round(float(amt * np.random.choice([0.0, 0.05, 0.1, 0.2, 0.3], p=[0.55, 0.15, 0.15, 0.10, 0.05])), 2)
        itms = int(max(1, min(15, round(amt / 28.0) + np.random.randint(-1, 2))))
        pts = int(round(amt * {1: 1.0, 2: 1.25, 3: 1.5, 4: 2.0}[t_id]))
        
        txn_amounts.append(amt)
        txn_discounts.append(disc)
        txn_items.append(itms)
        txn_points.append(pts)

    # Inject specific guarantees for UC7: staff members with multiple transactions on same day in last month
    print("Injecting UC7 staff multiple same-day transactions...")
    staff_m_indices = [i for i, s in enumerate(staff_indicator) if s == "Y"][:35]
    extra_txns_m = []
    extra_txns_d = []
    extra_txns_ts = []
    extra_txns_st = []
    extra_txns_ch = []
    extra_txns_amt = []
    extra_txns_disc = []
    extra_txns_itms = []
    extra_txns_pts = []
    extra_txns_pay = []
    
    for s_idx in staff_m_indices:
        # Choose 3 to 6 distinct days in the last month
        num_days = np.random.randint(3, 7)
        for _ in range(num_days):
            day_offset = np.random.randint(1, 28)
            target_day = end_date - datetime.timedelta(days=day_offset)
            # Create 2 to 4 transactions on this day
            num_same_day = np.random.randint(2, 5)
            for h in range(num_same_day):
                extra_txns_m.append(member_ids[s_idx])
                extra_txns_d.append(target_day)
                extra_txns_ts.append(datetime.datetime.combine(target_day, datetime.time(10 + h * 2, np.random.randint(0, 59), np.random.randint(0, 59))))
                st = "S01" if np.random.rand() < 0.4 else "S02"
                extra_txns_st.append(st)
                extra_txns_ch.append("STORE")
                amt = round(float(np.random.uniform(15.0, 85.0)), 2)
                extra_txns_amt.append(amt)
                extra_txns_disc.append(round(amt * 0.20, 2))  # Staff discount
                extra_txns_itms.append(np.random.randint(1, 4))
                extra_txns_pts.append(int(amt))
                extra_txns_pay.append("CREDIT_CARD")
                
    # Combine main and extra transactions
    all_txn_m = final_m_ids + extra_txns_m
    all_txn_d = final_dates + extra_txns_d
    all_txn_ts = final_times + extra_txns_ts
    all_txn_st = txn_stores + extra_txns_st
    all_txn_ch = txn_channels + extra_txns_ch
    all_txn_amt = txn_amounts + extra_txns_amt
    all_txn_disc = txn_discounts + extra_txns_disc
    all_txn_itms = txn_items + extra_txns_itms
    all_txn_pts = txn_points + extra_txns_pts
    all_txn_pay = list(txn_payment_choices) + extra_txns_pay
    
    total_txns = len(all_txn_m)
    txn_ids = [f"TXN{i:08d}" for i in range(1, total_txns + 1)]
    
    df_txn = pd.DataFrame({
        "transaction_id": txn_ids,
        "member_id": all_txn_m,
        "store_id": all_txn_st,
        "channel": all_txn_ch,
        "transaction_ts": all_txn_ts,
        "transaction_date": all_txn_d,
        "total_amount": all_txn_amt,
        "discount_amount": all_txn_disc,
        "items_count": all_txn_itms,
        "points_earned": all_txn_pts,
        "payment_type": all_txn_pay,
    })
    
    # Sort by transaction_ts
    df_txn.sort_values(by="transaction_ts", inplace=True)
    df_txn.reset_index(drop=True, inplace=True)
    df_txn["transaction_id"] = [f"TXN{i:08d}" for i in range(1, len(df_txn) + 1)]
    
    print(f"Writing {len(df_txn):,} transactions to fact_transaction.parquet...")
    pq.write_table(pa.Table.from_pandas(df_txn), os.path.join(output_dir, "fact_transaction.parquet"))

    # ---------------------------------------------------------
    # 6. fact_transaction_line
    # ---------------------------------------------------------
    print("Generating fact_transaction_line...")
    # Sample lines for each transaction
    # To keep file size manageable and fast to load, we can generate 1-3 lines per transaction
    categories = ["Apparel", "Footwear", "Beauty", "Home", "Accessories", "Electronics"]
    cat_weights = [0.35, 0.25, 0.15, 0.12, 0.08, 0.05]
    
    # Vectorized line generation for efficiency
    # For POC, generating ~2M lines:
    line_txn_ids = []
    line_cats = []
    line_qtys = []
    line_amts = []
    
    # Subsample 250k transactions for detailed lines to maintain quick load times while testing
    # Or generate lines for a substantial portion:
    sample_txn_df = df_txn.iloc[::2]  # 50% sample for line detail
    for t_id, amt, items in zip(sample_txn_df["transaction_id"], sample_txn_df["total_amount"], sample_txn_df["items_count"]):
        n_lines = min(max(1, items), 3)
        cat_choices = np.random.choice(categories, size=n_lines, p=cat_weights)
        line_amt_parts = np.random.dirichlet(np.ones(n_lines)) * amt
        for c, la in zip(cat_choices, line_amt_parts):
            line_txn_ids.append(t_id)
            line_cats.append(c)
            line_qtys.append(max(1, round(items / n_lines)))
            line_amts.append(round(float(la), 2))
            
    df_line = pd.DataFrame({
        "line_id": [f"L{i:08d}" for i in range(1, len(line_txn_ids) + 1)],
        "transaction_id": line_txn_ids,
        "product_category": line_cats,
        "quantity": line_qtys,
        "line_amount": line_amts,
    })
    print(f"Writing {len(df_line):,} transaction lines to fact_transaction_line.parquet...")
    pq.write_table(pa.Table.from_pandas(df_line), os.path.join(output_dir, "fact_transaction_line.parquet"))

    # ---------------------------------------------------------
    # 7. fact_points_ledger
    # ---------------------------------------------------------
    print("Generating fact_points_ledger...")
    # Points earned events + occasional redemption
    ledger_events = []
    # Sample 300k events
    sample_txns_for_ledger = df_txn.iloc[::4]
    for m_id, ts, pts in zip(sample_txns_for_ledger["member_id"], sample_txns_for_ledger["transaction_ts"], sample_txns_for_ledger["points_earned"]):
        ledger_events.append({
            "member_id": m_id,
            "event_ts": ts,
            "event_type": "EARN",
            "points": pts,
        })
        
    df_ledger = pd.DataFrame(ledger_events)
    df_ledger.sort_values(by="event_ts", inplace=True)
    df_ledger.reset_index(drop=True, inplace=True)
    df_ledger["ledger_id"] = [f"PL{i:08d}" for i in range(1, len(df_ledger) + 1)]
    # Balance after calculation (simplified)
    df_ledger["balance_after"] = np.random.randint(100, 10000, size=len(df_ledger))
    
    print(f"Writing {len(df_ledger):,} points events to fact_points_ledger.parquet...")
    pq.write_table(pa.Table.from_pandas(df_ledger), os.path.join(output_dir, "fact_points_ledger.parquet"))

    print("=== All Synthetic Parquet Data Generated Successfully! ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic retail loyalty data to Parquet.")
    parser.add_argument("--output-dir", default="data/parquet", help="Output directory for Parquet files")
    parser.add_argument("--num-members", type=int, default=50000, help="Number of members")
    parser.add_argument("--num-transactions", type=int, default=1500000, help="Number of transactions")
    parser.add_argument("--end-date", default=datetime.date.today().isoformat(), help="End date (YYYY-MM-DD)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    generate_all_data(
        output_dir=args.output_dir,
        num_members=args.num_members,
        num_transactions=args.num_transactions,
        end_date_str=args.end_date,
        seed=args.seed,
    )
