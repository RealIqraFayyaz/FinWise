
"""FinWise AI — Smart Money Studio
Run: python -m streamlit run app.py
Educational budgeting dashboard with local calculations and optional LangChain AI.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()

st.set_page_config(
    page_title="FinWise AI | Smart Money Studio",
    page_icon="✦",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --mint:#71f5cb; --blue:#7da7ff; --muted:#9baac6; --line:rgba(164,190,255,.16); }
html, body, [class*="css"] { font-family:Manrope,sans-serif; }
.stApp { background:radial-gradient(ellipse at 8% 0%,rgba(69,104,255,.20),transparent 32%),radial-gradient(ellipse at 92% 8%,rgba(57,238,189,.10),transparent 28%),linear-gradient(145deg,#070b16,#0a1122 48%,#0c1428); color:#eaf1ff; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1440px; padding-top:1.5rem; padding-bottom:3rem; }
section[data-testid="stSidebar"] { background:rgba(7,13,27,.96); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] * { color:#eaf1ff; }
h1,h2,h3 { letter-spacing:-.04em; }
h1 { font-weight:800; }
p,label { color:#b8c5dc; }
div[data-testid="stMetric"] { background:linear-gradient(140deg,rgba(26,43,75,.80),rgba(14,25,46,.72)); border:1px solid var(--line); padding:18px; border-radius:18px; transition:transform .25s,border-color .25s; }
div[data-testid="stMetric"]:hover { transform:translateY(-3px); border-color:rgba(113,245,203,.55); }
div[data-testid="stMetricLabel"] { color:#9baac6; }
div[data-testid="stMetricValue"] { color:#f3f7ff; font-weight:800; }
.stButton>button,.stDownloadButton>button { border-radius:12px; border:1px solid rgba(113,245,203,.42); background:linear-gradient(100deg,#71f5cb,#8acbff); color:#071323; font-weight:800; transition:all .2s; }
.stButton>button:hover,.stDownloadButton>button:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(113,245,203,.18); }
.stTextInput input,.stNumberInput input,div[data-baseweb="select"]>div { background:#101b32!important; color:#f2f6ff!important; border-radius:10px!important; }
.hero { position:relative; overflow:hidden; padding:32px; border:1px solid rgba(155,183,255,.22); border-radius:28px; background:linear-gradient(115deg,rgba(29,48,87,.92),rgba(13,25,48,.83) 60%,rgba(16,54,61,.58)); box-shadow:0 24px 70px rgba(0,0,0,.22); animation:rise .7s ease both; }
.hero:after { content:''; position:absolute; width:230px; height:230px; right:-65px; top:-100px; border-radius:50%; border:1px solid rgba(113,245,203,.3); box-shadow:0 0 0 25px rgba(113,245,203,.035),0 0 0 50px rgba(113,245,203,.025),0 0 70px rgba(113,245,203,.12); animation:orbit 12s linear infinite; pointer-events:none; }
.hero h1 { margin:12px 0; font-size:clamp(2rem,4vw,3.4rem); color:#f6f8ff; }
.hero p { max-width:760px; font-size:1rem; line-height:1.8; }
.eyebrow,.section-kicker { color:var(--mint); font-size:.75rem; font-weight:800; letter-spacing:.15em; text-transform:uppercase; }
.glow { color:var(--mint); }
.pill { display:inline-block; padding:6px 10px; margin:5px 5px 0 0; border:1px solid rgba(113,245,203,.26); border-radius:999px; color:#a8f8df; background:rgba(113,245,203,.07); font-size:.72rem; }
.panel { padding:20px; border-radius:18px; background:linear-gradient(145deg,rgba(20,34,61,.76),rgba(12,22,41,.68)); border:1px solid var(--line); margin-bottom:12px; }
.small-muted { font-size:.82rem; color:var(--muted); }
.pulse-dot { display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--mint);margin-right:8px;animation:pulse 2s infinite; }
.stProgress>div>div>div>div { background:linear-gradient(90deg,#71f5cb,#7da7ff); }
@keyframes orbit { from{transform:rotate(0)} to{transform:rotate(360deg)} }
@keyframes rise { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
@keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(113,245,203,.6)} 70%{box-shadow:0 0 0 9px rgba(113,245,203,0)} 100%{box-shadow:0 0 0 0 rgba(113,245,203,0)} }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

DISCLAIMER = (
    "Educational prototype only. This dashboard is not financial, tax, legal, "
    "or investment advice. It does not connect to bank accounts or execute transactions."
)

CATEGORIES = [
    "Housing / rent", "Food", "Transportation", "Utilities", "Education",
    "Healthcare", "Entertainment", "Loan / debt", "Other", "Subscriptions"
]

DEFAULT_EXPENSES = {
    "Housing / rent": 800.0,
    "Food": 350.0,
    "Transportation": 120.0,
    "Utilities": 150.0,
    "Education": 0.0,
    "Healthcare": 50.0,
    "Entertainment": 80.0,
    "Loan / debt": 200.0,
    "Other": 100.0,
    "Subscriptions": 25.0,
}

GOALS = [
    "Save money", "Build an emergency fund", "Pay off debt",
    "Vacation", "Start a business", "Improve budgeting"
]

CURRENCIES = ["PKR", "USD", "GBP", "EUR", "INR", "AED", "SAR", "CAD", "AUD"]

SYMBOLS = {
    "PKR": "Rs ", "USD": "$", "GBP": "£", "EUR": "€",
    "INR": "₹", "AED": "AED ", "SAR": "SAR ",
    "CAD": "C$", "AUD": "A$"
}


def money(value: float, currency: str) -> str:
    return f"{SYMBOLS.get(currency, currency + ' ')}{value:,.2f}"


def calculate_finances(
    income: float,
    expenses: dict[str, float],
    savings: float
) -> dict[str, Any]:
    clean = {
        key: max(0.0, float(value or 0))
        for key, value in expenses.items()
    }

    total = sum(clean.values())
    remaining = float(income) - total

    expense_ratio = (
        total / income * 100
        if income > 0
        else (100.0 if total else 0.0)
    )

    savings_ratio = float(savings) / income * 100 if income > 0 else 0.0
    debt = clean.get("Loan / debt", 0.0)

    debt_ratio = (
        debt / income * 100
        if income > 0
        else (100.0 if debt else 0.0)
    )

    score = 50.0 + min(max(savings_ratio, 0), 30) * 0.9
    score += (
        max(min((income - total) / income * 25, 15), -35)
        if income > 0 else -15
    )
    score += max(min((70 - expense_ratio) * 0.25, 12), -25)
    score -= min(debt_ratio * 0.35, 20)

    if remaining < 0:
        score -= min(abs(remaining) / max(income, 1) * 15, 20)

    score = int(round(max(0, min(100, score))))

    risk = (
        "HIGH"
        if remaining < 0 or expense_ratio > 100 or debt_ratio >= 50
        else "MEDIUM"
        if remaining <= 0 or expense_ratio >= 80 or debt_ratio >= 30
        else "LOW"
    )

    return {
        "monthly_income": float(income),
        "expense_breakdown": clean,
        "total_expenses": total,
        "remaining_income": remaining,
        "savings": float(savings),
        "savings_ratio": savings_ratio,
        "expense_ratio": expense_ratio,
        "debt_ratio": debt_ratio,
        "preliminary_score": score,
        "preliminary_risk": risk,
    }


def local_analysis(fin: dict[str, Any], goal: str) -> dict[str, Any]:
    ranked = sorted(
        fin["expense_breakdown"].items(),
        key=lambda item: item[1],
        reverse=True
    )

    priorities = []

    if fin["remaining_income"] < 0:
        priorities.append(
            "Your expenses exceed income. Review flexible spending "
            "and find a realistic way to close the gap."
        )

    if fin["debt_ratio"] >= 30:
        priorities.append(
            "Review debt payments, interest rates, and possible repayment options."
        )

    if ranked and ranked[0][1] > 0:
        priorities.append(
            f"Review {ranked[0][0].lower()}, your largest listed expense."
        )

    priorities.append(
        f"Keep your monthly plan aligned with your goal: {goal.lower()}."
    )

    spending = [
        {
            "category": cat,
            "observation": f"{cat} is {amount:,.2f} per month.",
            "recommendation": (
                "Compare this expense with your needs and consider "
                "a realistic adjustment if appropriate."
            ),
        }
        for cat, amount in ranked[:5]
        if amount > 0
    ]

    return {
        "financial_summary": (
            f"Your monthly income is {fin['monthly_income']:,.2f}, "
            f"listed expenses total {fin['total_expenses']:,.2f}, "
            f"and remaining balance is {fin['remaining_income']:,.2f}."
        ),
        "financial_health_score": fin["preliminary_score"],
        "spending_analysis": spending,
        "risk_level": fin["preliminary_risk"],
        "top_priorities": priorities[:4],
        "budget_recommendations": [
            "Track flexible expenses weekly.",
            "Plan essential bills before discretionary spending.",
            "Review recurring subscriptions and irregular costs."
        ],
        "savings_strategy": [
            "If your budget allows, set aside a small amount regularly.",
            "Build an emergency reserve gradually according to your needs."
        ],
        "next_month_action_plan": [
            "Track expenses for the next 30 days.",
            "Choose one adjustable spending category to review.",
            "Compare actual spending with your plan at month-end."
        ],
    }


# -------------------- AI ANALYSIS --------------------

SYSTEM_PROMPT = """
You are FinWise AI, a careful personal budgeting assistant.
Use only the financial figures supplied in the user's data.
Never invent transactions, bank information, interest rates, or income.
Give practical educational budgeting suggestions, not investment,
tax, legal, or guaranteed financial advice.

Return a valid JSON object with these keys:
financial_summary, financial_health_score, spending_analysis,
risk_level, top_priorities, budget_recommendations,
savings_strategy, next_month_action_plan.

financial_health_score must be an integer from 0 to 100.
risk_level must be LOW, MEDIUM, or HIGH.
Use concise, supportive language. If data is missing, say so.
"""

AI_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{system_instructions}"),
    (
        "human",
        """Analyze this monthly budget.

Financial data:
{financial_data}

User's main financial goal:
{financial_goal}

Return only a JSON object matching the requested schema.
Do not put the JSON inside Markdown code fences."""
    ),
])


def get_ai_model() -> ChatOpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key or api_key == "your_actual_api_key_here":
        return None

    try:
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            api_key=api_key,
        )
    except Exception:
        return None


def parse_ai_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    # Remove Markdown fences if the model includes them.
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Attempt to extract a JSON object from surrounding text.
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "The AI response was not valid JSON. Please try again."
    )


def generate_ai_analysis(
    financial_data: dict[str, Any],
    financial_goal: str,
) -> dict[str, Any]:
    model = get_ai_model()

    if model is None:
        return local_analysis(financial_data, financial_goal)

    chain = AI_PROMPT | model | StrOutputParser()

    result = chain.invoke({
        "system_instructions": SYSTEM_PROMPT,
        "financial_data": json.dumps(
            financial_data,
            ensure_ascii=False,
            indent=2,
        ),
        "financial_goal": financial_goal,
    })

    parsed = parse_ai_response(result)

    # Keep the score and risk within valid, predictable limits.
    try:
        score = int(parsed.get(
            "financial_health_score",
            financial_data["preliminary_score"]
        ))
    except (TypeError, ValueError):
        score = financial_data["preliminary_score"]

    parsed["financial_health_score"] = max(0, min(100, score))

    risk = str(
        parsed.get(
            "risk_level",
            financial_data["preliminary_risk"]
        )
    ).upper()

    if risk not in {"LOW", "MEDIUM", "HIGH"}:
        risk = financial_data["preliminary_risk"]

    parsed["risk_level"] = risk

    return parsed


def safe_list(value: Any) -> list[Any]:
    """Convert a response field into a list for safe rendering."""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def display_analysis(analysis: dict[str, Any]) -> None:
    st.markdown("### Your financial briefing")

    summary = analysis.get(
        "financial_summary",
        "Your budget analysis is ready."
    )
    st.markdown(
        f'<div class="panel">{summary}</div>',
        unsafe_allow_html=True,
    )

    score = analysis.get("financial_health_score", 0)
    try:
        score = max(0, min(100, int(score)))
    except (TypeError, ValueError):
        score = 0

    risk = str(analysis.get("risk_level", "MEDIUM")).upper()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Financial health score", f"{score}/100")
        st.progress(score / 100)
    with col2:
        st.metric("Budget risk level", risk)

    st.markdown("#### Spending analysis")

    spending = safe_list(analysis.get("spending_analysis"))

    if spending:
        for item in spending:
            if isinstance(item, dict):
                category = item.get("category", "Budget item")
                observation = item.get("observation", "")
                recommendation = item.get("recommendation", "")

                with st.expander(str(category)):
                    if observation:
                        st.write(observation)
                    if recommendation:
                        st.write(recommendation)
            else:
                st.write(f"• {item}")
    else:
        st.info("No additional spending observations were returned.")

    sections = [
        ("Top priorities", "top_priorities"),
        ("Budget recommendations", "budget_recommendations"),
        ("Savings strategy", "savings_strategy"),
        ("Next-month action plan", "next_month_action_plan"),
    ]

    for title, key in sections:
        st.markdown(f"#### {title}")
        items = safe_list(analysis.get(key))

        if items:
            for item in items:
                if isinstance(item, dict):
                    st.write(
                        "• " + str(
                            item.get("recommendation")
                            or item.get("action")
                            or item.get("description")
                            or item
                        )
                    )
                else:
                    st.write(f"• {item}")
        else:
            st.caption("No items provided.")


# -------------------- SESSION STATE --------------------

if "expenses" not in st.session_state:
    st.session_state.expenses = DEFAULT_EXPENSES.copy()

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "last_financial_data" not in st.session_state:
    st.session_state.last_financial_data = None


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## ✦ FinWise AI")
    st.caption("Your personal budgeting studio")
    st.markdown("---")

    currency = st.selectbox(
        "Display currency",
        CURRENCIES,
        index=0,
    )

    st.markdown("### Monthly income")
    monthly_income = st.number_input(
        "Take-home income",
        min_value=0.0,
        value=3000.0,
        step=100.0,
        help="Enter your total monthly take-home income.",
    )

    st.markdown("### Monthly expenses")

    updated_expenses = {}

    for category in CATEGORIES:
        updated_expenses[category] = st.number_input(
            category,
            min_value=0.0,
            value=float(
                st.session_state.expenses.get(category, 0.0)
            ),
            step=10.0,
            key=f"expense_{category}",
        )

    st.session_state.expenses = updated_expenses

    st.markdown("### Financial goal")
    goal = st.selectbox(
        "Your main goal",
        GOALS,
        index=0,
    )

    monthly_savings = st.number_input(
        "Monthly savings contribution",
        min_value=0.0,
        value=100.0,
        step=10.0,
    )

    st.markdown("---")
    st.caption("AI analysis requires a valid OpenAI API key.")
    st.caption(DISCLAIMER)


# -------------------- CALCULATIONS --------------------

fin = calculate_finances(
    monthly_income,
    st.session_state.expenses,
    monthly_savings,
)

remaining = fin["remaining_income"]
total_expenses = fin["total_expenses"]

# -------------------- HERO --------------------

st.markdown("""
<div class="hero">
    <div class="eyebrow"><span class="pulse-dot"></span> SMART MONEY STUDIO</div>
    <h1>Make your money<br><span class="glow">work smarter.</span></h1>
    <p>
        A clearer view of your monthly budget, spending patterns, and
        financial goals — with practical insights to help you plan
        your next move.
    </p>
    <span class="pill">Budget planner</span>
    <span class="pill">Expense analytics</span>
    <span class="pill">AI financial briefing</span>
</div>
""", unsafe_allow_html=True)

st.write("")

# -------------------- METRIC CARDS --------------------

st.markdown(
    '<div class="section-kicker">YOUR MONTHLY SNAPSHOT</div>',
    unsafe_allow_html=True,
)
st.write("")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "Monthly income",
        money(monthly_income, currency),
    )

with m2:
    st.metric(
        "Total expenses",
        money(total_expenses, currency),
        delta=(
            f"{fin['expense_ratio']:.1f}% of income"
            if monthly_income > 0
            else "Income not entered"
        ),
        delta_color="inverse",
    )

with m3:
    st.metric(
        "Money remaining",
        money(remaining, currency),
        delta=(
            "Surplus" if remaining >= 0 else "Over budget"
        ),
        delta_color=(
            "normal" if remaining >= 0 else "inverse"
        ),
    )

with m4:
    st.metric(
        "Savings contribution",
        money(monthly_savings, currency),
        delta=(
            f"{fin['savings_ratio']:.1f}% of income"
            if monthly_income > 0
            else "Income not entered"
        ),
    )

st.write("")

if remaining < 0:
    st.warning(
        "Your listed expenses are higher than your income. "
        "Consider reviewing flexible spending and upcoming bills."
    )
elif monthly_income > 0 and fin["expense_ratio"] >= 80:
    st.info(
        "Most of your income is allocated to expenses. "
        "Review your budget to leave room for unexpected costs."
    )
elif monthly_income > 0:
    st.success(
        "Your listed expenses are within your monthly income. "
        "Keep tracking spending and planning for irregular costs."
    )
else:
    st.info("Enter your monthly income in the sidebar to start.")


# -------------------- CHARTS & BUDGET ANALYTICS --------------------

st.markdown(
    '<div class="section-kicker">EXPLORE YOUR MONEY</div>',
    unsafe_allow_html=True,
)
st.write("")

left, right = st.columns([1.1, 0.9], gap="large")

with left:
    st.markdown("### Where your money goes")

    chart_data = pd.DataFrame([
        {"Category": category, "Amount": amount}
        for category, amount in fin["expense_breakdown"].items()
        if amount > 0
    ])

    if not chart_data.empty:
        fig = px.pie(
            chart_data,
            names="Category",
            values="Amount",
            hole=0.67,
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="%{label}<br>%{value:,.2f}<extra></extra>",
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=10, r=10),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.08,
                xanchor="center",
                x=0.5,
            ),
            font=dict(color="#dce7ff"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Enter expense amounts in the sidebar to view the chart.")

with right:
    st.markdown("### Income allocation")

    allocation_data = pd.DataFrame({
        "Type": ["Expenses", "Savings contribution", "Remaining after expenses"],
        "Amount": [
            total_expenses,
            monthly_savings,
            remaining,
        ],
    })

    # Negative remaining balances are shown in the chart as a zero-length
    # segment; the actual negative balance is still shown in the metrics.
    allocation_data["Display amount"] = allocation_data["Amount"].clip(lower=0)

    fig2 = px.bar(
        allocation_data,
        x="Display amount",
        y="Type",
        orientation="h",
        text="Display amount",
        labels={
            "Display amount": f"Amount ({currency})",
            "Type": "",
        },
    )
    fig2.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
    )
    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20, l=10, r=30),
        font=dict(color="#dce7ff"),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

st.write("")

# -------------------- BUDGET BREAKDOWN TABLE --------------------

st.markdown("### Monthly expense breakdown")

breakdown = pd.DataFrame([
    {
        "Category": category,
        f"Monthly amount ({currency})": amount,
        "Share of expenses (%)": (
            amount / total_expenses * 100
            if total_expenses > 0
            else 0.0
        ),
    }
    for category, amount in fin["expense_breakdown"].items()
])

breakdown = breakdown.sort_values(
    by=f"Monthly amount ({currency})",
    ascending=False,
)

st.dataframe(
    breakdown.style.format({
        f"Monthly amount ({currency})": "{:,.2f}",
        "Share of expenses (%)": "{:.1f}%",
    }),
    use_container_width=True,
    hide_index=True,
)

# -------------------- AI FINANCIAL BRIEFING --------------------

st.markdown("---")
st.markdown(
    '<div class="section-kicker">YOUR PERSONAL MONEY COACH</div>',
    unsafe_allow_html=True,
)
st.markdown("## Get your financial briefing")
st.write(
    "Generate a summary of your budget, spending priorities, "
    "savings ideas, and a practical action plan."
)

ai_ready = bool(
    os.getenv("OPENAI_API_KEY", "").strip()
    and os.getenv("OPENAI_API_KEY", "").strip()
    != "your_actual_api_key_here"
)

if ai_ready:
    st.caption("AI mode is configured. A valid API key and network access are required.")
else:
    st.caption(
        "Local mode is available now. Add your OpenAI API key to your "
        ".env file to enable AI-generated analysis."
    )

if st.button("✦ Generate financial briefing", use_container_width=True):
    with st.spinner("Analyzing your budget..."):
        try:
            st.session_state.analysis = generate_ai_analysis(fin, goal)
            st.session_state.last_financial_data = {
                **fin,
                "financial_goal": goal,
                "currency": currency,
            }
        except Exception as exc:
            st.error(
                "The briefing could not be generated. "
                "Check your API key and internet connection if using AI mode."
            )
            st.caption(f"Technical details: {exc}")

if st.session_state.analysis is not None:
    display_analysis(st.session_state.analysis)

    st.write("")
    if st.button("Refresh briefing", use_container_width=False):
        st.session_state.analysis = None
        st.rerun()

# -------------------- EXPORT REPORT --------------------

st.markdown("---")
st.markdown("### Export your budget report")

report = {
    "application": "FinWise AI",
    "report_type": "Monthly personal budget",
    "currency": currency,
    "financial_goal": goal,
    "monthly_income": monthly_income,
    "monthly_expenses": fin["expense_breakdown"],
    "total_expenses": total_expenses,
    "remaining_after_expenses": remaining,
    "monthly_savings_contribution": monthly_savings,
    "expense_ratio_percent": round(fin["expense_ratio"], 2),
    "savings_ratio_percent": round(fin["savings_ratio"], 2),
    "preliminary_health_score": fin["preliminary_score"],
    "preliminary_risk_level": fin["preliminary_risk"],
    "disclaimer": DISCLAIMER,
}

if st.session_state.analysis is not None:
    report["financial_briefing"] = st.session_state.analysis

report_json = json.dumps(
    report,
    indent=2,
    ensure_ascii=False,
    default=str,
)

st.download_button(
    label="⬇ Download budget report (JSON)",
    data=report_json,
    file_name="finwise_budget_report.json",
    mime="application/json",
    use_container_width=True,
)

st.markdown(
    """
    <div class="panel">
        <div class="section-kicker">FINWISE AI</div>
        <p><b>Small steps. Clearer money decisions.</b></p>
        <p class="small-muted">
            Keep your budget updated as your income and expenses change.
            Review your plan regularly and adapt it to your circumstances.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(DISCLAIMER)
