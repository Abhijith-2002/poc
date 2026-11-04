"""
tests/test_use_case_routing.py
Evaluation test suite testing 35+ varied and paraphrased questions
against expected use-case IDs, follow-up chains, and out-of-scope rejections.
"""

import pytest
from agent.graph import LoyaltyDeepAgent

ROUTING_TEST_CASES = [
    # UC1
    ("Top 100 members by spend in the last 12 months at the Doncaster store who are contactable by email", "UC1"),
    ("Who are our highest spending customers at Doncaster over the past year who we can email?", "UC1"),
    ("List top 100 spenders at Doncaster with email opt-in over the last 12 months", "UC1"),
    ("Doncaster VIP campaign members top 100 by spend", "UC1"),

    # UC1a (chained from UC1)
    ("Of those 100, rank by number of purchases", "UC1a", "UC1"),
    ("Rank those 100 Doncaster members by their purchase count", "UC1a", "UC1"),
    ("Which of those top 100 members made the most purchases?", "UC1a", "UC1"),

    # UC2
    ("Average visit spend per member, broken down by member tier, past 3 months", "UC2"),
    ("What is the average visit spend across loyalty tiers over the last 90 days?", "UC2"),
    ("Show me spend per visit by tier for the past 3 months", "UC2"),
    ("Loyalty tier basket size average visit spend past 3 months", "UC2"),

    # UC2a (chained from UC2)
    ("Provide a pie graph of UC2", "UC2a", "UC2"),
    ("Show that breakdown as a pie chart", "UC2a", "UC2"),
    ("Can you chart average visit spend by tier as a pie graph?", "UC2a", "UC2"),

    # UC3
    ("Which age band is more likely to shop in store vs online, past 6 months", "UC3"),
    ("Compare online vs in store shopping propensity across demographic age bands over last 6 months", "UC3"),
    ("Which customer age group prefers digital e-commerce compared to brick and mortar stores?", "UC3"),

    # UC3a (chained from UC3)
    ("For the top age band, on average how many store visits per member in the past 6 months", "UC3a", "UC3"),
    ("How many times did members in that top in-store age group visit our stores?", "UC3a", "UC3"),
    ("Average store visits per member for the top age band past 6 months", "UC3a", "UC3"),

    # UC4
    ("Top 100 members who joined in the last 6 months with high visit frequency, ranked by member spend", "UC4"),
    ("Who are our top new joiners with high visit frequency ranked by spend?", "UC4"),
    ("List best new loyalty members from the last 6 months with frequent store visits", "UC4"),

    # UC4a (chained from UC4)
    ("Of those 100, show the break-up of online vs in-store spend", "UC4a", "UC4"),
    ("Break down their spend between online vs in-store for those top new joiners", "UC4a", "UC4"),
    ("What was the channel spend split for those 100 members?", "UC4a", "UC4"),

    # UC5
    ("Chart spend by member tier this year vs last year; highlight green when up, red when down", "UC5"),
    ("Compare Calendar YTD spend by loyalty tier against last year same period with variance colors", "UC5"),
    ("YoY tier spend comparison chart with green for positive and red for negative", "UC5"),
    ("Show spend by member tier this year vs last year", "UC5"),

    # UC6
    ("Demographic breakdown of members who have NOT spent in the last 6 months vs those who have", "UC6"),
    ("Compare active members vs lapsed dormant customers who have not spent in last 6 months", "UC6"),
    ("Who are our members who have not spent in the last 6 months broken down by demographics?", "UC6"),

    # UC7
    ("Rank top 100 members with staff_indicator = 'Y' by high transaction frequency in the last month", "UC7"),
    ("Show team members with highest transaction frequency including multiple transactions per day", "UC7"),
    ("Top staff members ranked by purchase frequency and multi-transaction days in the last month", "UC7"),

    # UC8
    ("Number of members in Gold tier with points >= 3000 who haven't transacted in the past 2 months", "UC8"),
    ("How many Gold customers with points >= 5000 are dormant for 2 months?", "UC8"),
    ("Count of Gold tier members with points >= 1500 and no transactions in past 2 months", "UC8"),

    # Out of Scope Queries (must return NONE)
    ("What is the weather forecast in Doncaster tomorrow?", "NONE"),
    ("Show me inventory count for shoe sku 12345 in Melbourne store", "NONE"),
    ("Who is the CEO of the retail company?", "NONE"),
]


@pytest.mark.asyncio
async def test_all_routing_cases():
    agent = LoyaltyDeepAgent()
    await agent.initialize()

    passed = 0
    total = len(ROUTING_TEST_CASES)

    for item in ROUTING_TEST_CASES:
        if len(item) == 2:
            question, expected_uc = item
            prev_state = None
        else:
            question, expected_uc, parent_uc = item
            prev_state = {"use_case_id": parent_uc}

        res = await agent.resolve_use_case(question, previous_state=prev_state)
        actual_uc = res.get("use_case_id")
        assert actual_uc == expected_uc, f"Failed for query '{question}': expected {expected_uc}, got {actual_uc}"
        passed += 1

    print(f"\n✓ Successfully evaluated {passed}/{total} routing test cases with 100% accuracy!")

