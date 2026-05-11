import streamlit as st
import pyodbc
import pandas as pd
import datetime

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Sibling Inventory Bakeshop",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — Warm Modern Bakery Aesthetic
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap');

    :root {
        --vanilla:       #FAFAF7;
        --vanilla-dark:  #F0EDE6;
        --white:         #FFFFFF;
        --cocoa:         #4A3B32;
        --cocoa-light:   #6B5B50;
        --cocoa-dark:    #3A2D25;
        --terracotta:    #D98359;
        --terracotta-lt: #E5A07A;
        --terracotta-dk: #C06B42;
        --text-dark:     #2E2118;
        --text-med:      #5C4A3D;
        --text-light:    #8B7B6E;
        --border:        #DDD5CB;
    }

    /* ── Global ── */
    .stApp, .main .block-container {
        background-color: var(--vanilla) !important;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4A3B32 0%, #3A2D25 100%) !important;
        border-right: 1px solid var(--cocoa-light);
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown span:not(.material-symbols-rounded),
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stRadio label span:not(.material-symbols-rounded) {
        color: #F0EDE6 !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: var(--terracotta-lt) !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: var(--cocoa-light) !important;
        opacity: 0.4;
    }
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 0.15rem;
    }
    section[data-testid="stSidebar"] .stRadio > div > label {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(217,131,89,0.2);
        border-radius: 8px;
        padding: 0.65rem 1rem;
        transition: all 0.25s ease;
        cursor: pointer;
    }
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(217,131,89,0.12);
        border-color: var(--terracotta);
    }
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
        background: rgba(217,131,89,0.18) !important;
        border-color: var(--terracotta) !important;
    }

    /* ── Typography (targeted — excludes icon fonts) ── */
    h1, h2, h3, h4 {
        font-family: 'Montserrat', sans-serif !important;
        color: var(--cocoa) !important;
    }
    h1 { font-weight: 700 !important; }
    h2 { font-weight: 600 !important; border-bottom: 2px solid var(--terracotta-lt); padding-bottom: 0.4rem; }
    h3 { font-weight: 600 !important; color: var(--cocoa-light) !important; }

    /* Apply Montserrat only to text elements, NEVER to icon/symbol fonts */
    p, label,
    .stMarkdown p,
    .stMarkdown span:not(.material-symbols-rounded):not(.material-symbols-outlined):not(.material-icons),
    .stCaption,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] span:not(.material-symbols-rounded):not(.material-symbols-outlined) {
        font-family: 'Montserrat', -apple-system, sans-serif !important;
        color: var(--text-dark);
    }

    /* Protect icon fonts from any override */
    .material-symbols-rounded,
    .material-symbols-outlined,
    .material-icons,
    span.material-symbols-rounded {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    }

    /* ── Expander styling ── */
    details[data-testid="stExpander"] summary {
        font-family: 'Montserrat', sans-serif !important;
        color: var(--cocoa) !important;
        font-weight: 600 !important;
        background-color: var(--white) !important;
        border-radius: 12px;
    }
    details[data-testid="stExpander"] {
        background: var(--white) !important;
        border: 1px solid var(--border);
        border-radius: 12px;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 8px rgba(74,59,50,0.05);
    }

    /* ── DataFrames ── */
    .stDataFrame, div[data-testid="stDataFrame"] {
        background: var(--white);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(74,59,50,0.06);
    }

    /* ── Buttons (all contexts including inside expanders & forms) ── */
    .stButton > button,
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stFormSubmitButton"] > button,
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, var(--terracotta) 0%, var(--terracotta-dk) 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(217,131,89,0.3) !important;
    }
    .stButton > button:hover,
    div[data-testid="stButton"] button:hover,
    div[data-testid="stFormSubmitButton"] button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover,
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, var(--terracotta-dk) 0%, var(--cocoa) 100%) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(217,131,89,0.35) !important;
    }
    .stButton > button:active,
    div[data-testid="stFormSubmitButton"] button:active {
        background: var(--cocoa) !important;
        color: #FFFFFF !important;
    }
    /* Button text must always be white */
    .stButton > button *,
    div[data-testid="stFormSubmitButton"] button *,
    div[data-testid="stFormSubmitButton"] button p,
    div[data-testid="stFormSubmitButton"] button span {
        color: #FFFFFF !important;
    }

    /* ── Form Inputs (text, number, select — explicit light bg / dark text) ── */
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stSelectbox"] > div > div {
        background-color: var(--white) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--cocoa) !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div > input:focus,
    .stTextInput > div > div > input:focus,
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stNumberInput"] input:focus {
        border-color: var(--terracotta) !important;
        box-shadow: 0 0 0 3px rgba(217,131,89,0.15) !important;
    }
    /* Input label text */
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSelectbox"] label {
        color: var(--cocoa) !important;
        font-family: 'Montserrat', sans-serif !important;
    }

    /* ── Dropdown Menu (the popup list of options) ── */
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] ul,
    div[data-baseweb="menu"],
    ul[role="listbox"] {
        background-color: var(--white) !important;
        border-color: var(--border) !important;
    }
    div[data-baseweb="popover"] li,
    ul[role="listbox"] li,
    li[role="option"] {
        color: var(--cocoa) !important;
        font-family: 'Montserrat', sans-serif !important;
        background-color: var(--white) !important;
    }
    div[data-baseweb="popover"] li span,
    ul[role="listbox"] li span,
    li[role="option"] span {
        color: inherit !important;
    }
    div[data-baseweb="popover"] li:hover,
    ul[role="listbox"] li:hover,
    li[role="option"]:hover,
    li[aria-selected="true"] {
        background-color: var(--terracotta-lt) !important;
        color: #FFFFFF !important;
    }
    /* Selected value text inside the selectbox */
    .stSelectbox span[data-baseweb="tag"],
    .stSelectbox div[data-baseweb="select"] span:not(.material-symbols-rounded) {
        color: var(--cocoa) !important;
    }

    /* ── Alerts ── */
    .stAlert { border-radius: 10px !important; }

    /* ── Dividers ── */
    hr { border-color: var(--border) !important; }

    /* ── Card Containers ── */
    .card {
        background: var(--white);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.6rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(74,59,50,0.05);
    }
    .card-header {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--cocoa);
        margin-bottom: 0.8rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--vanilla-dark);
    }

    /* ── Page Header ── */
    .page-header { text-align: center; padding: 1rem 0 0.5rem; }
    .page-header h1 { font-size: 2rem; margin-bottom: 0; }
    .page-header .subtitle {
        font-family: 'Montserrat', sans-serif;
        color: var(--text-light);
        font-size: 0.92rem;
        font-weight: 400;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    .divider-accent {
        width: 60px; height: 3px;
        background: linear-gradient(90deg, var(--terracotta-lt), var(--terracotta), var(--terracotta-lt));
        margin: 0.6rem auto 1.2rem;
        border: none; border-radius: 4px;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] {
        background: var(--vanilla) !important;
        border-bottom: 1px solid var(--border);
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# ──────────────────────────────────────────────────────────────────────────────
#
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    ⚠  IMPORTANT — READ BEFORE RUNNING  ⚠              ║
# ║                                                                        ║
# ║  The SERVER is set to  .\SQLEXPRESS  (local default SQL Express).      ║
# ║  If your instance name differs, update the string below.              ║
# ║                                                                        ║
# ║  To find your server name:                                             ║
# ║    1. Open SQL Server Management Studio (SSMS).                        ║
# ║    2. Look at the "Server name" field in the Connect dialog.           ║
# ║    3. Copy that value and paste it below.                              ║
# ║                                                                        ║
# ║  Common formats:                                                       ║
# ║    • .\SQLEXPRESS                                                      ║
# ║    • DESKTOP-XXXXXXX\SQLEXPRESS                                        ║
# ║    • localhost\SQLEXPRESS                                               ║
# ║                                                                        ║
# ║  The DATABASE must match the one created by the SQL script ("Project").║
# ╚══════════════════════════════════════════════════════════════════════════╝
#

@st.cache_resource
def init_connection():
    """
    Establish a cached connection to SQL Server via pyodbc.
    Dynamically detects the installed ODBC driver version.
    Returns the connection object on success, or None on failure.
    """
    try:
        available_drivers = pyodbc.drivers()
        preferred = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server",
        ]
        driver = None
        for d in preferred:
            if d in available_drivers:
                driver = d
                break
        if driver is None:
            driver = "SQL Server"

        connection_string = (
            f"DRIVER={{{driver}}};"
            r"SERVER=.\SQLEXPRESS;"
            "DATABASE=Project;"
            "Trusted_Connection=yes;"
            "Timeout=5;"
        )
        if "18" in driver:
            connection_string += "Encrypt=no;TrustServerCertificate=yes;"

        return pyodbc.connect(connection_string, autocommit=False)

    except pyodbc.Error as e:
        st.session_state["db_error"] = str(e)
        return None
    except Exception as e:
        st.session_state["db_error"] = str(e)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# QUERY & EXECUTION HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def run_query(query, params=()):
    """
    Execute a SQL query safely.
    - For SELECT: returns a pandas DataFrame.
    """
    conn = init_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame.from_records(rows, columns=columns)
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Database error: {e}")
        return pd.DataFrame()


def execute_action(query, params=()):
    """
    Execute a write query (INSERT / UPDATE / DELETE / EXEC procedure).
    Returns (True, "Success") on success, or (False, error_string) on failure.
    This lets the UI display exact SQL trigger RAISERROR messages.
    """
    conn = init_connection()
    if conn is None:
        return False, "No database connection."
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True, "Success"
    except pyodbc.Error as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, str(e)
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, str(e)


def run_query_from_proc(query, params=()):
    """
    Execute a stored procedure that returns a result set (e.g. sp_CheckProductFeasibility).
    Returns a pandas DataFrame with the results.
    """
    conn = init_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame.from_records(rows, columns=columns)
        else:
            return pd.DataFrame()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        st.error(f"Database error: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem 0 0.25rem;">
        <span style="font-size: 2.5rem;">🍞</span>
        <h2 style="margin:0; font-size:1.25rem; color:#E5A07A !important;
                   font-family:'Montserrat',sans-serif !important;">
            The Sibling Inventory<br>Bakeshop
        </h2>
        <p style="margin:0.25rem 0 0; font-size:0.68rem; letter-spacing:2px;
                  text-transform:uppercase; color:#8B7B6E !important;">
            Management Dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    page = st.sidebar.radio(
        "Navigate",
        [
            "🧾  Point of Sale",
            "📦  Supply Chain & Inventory",
            "🧁  Recipes & Manufacturing",
            "🚚  Logistics & Delivery",
            "👨‍🍳  HR & Operations",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding-top:0.5rem;">
        <p style="font-size:0.68rem; color:#8B7B6E !important; letter-spacing:1px; margin:0;">
            DATABASE PROJECT · 2026
        </p>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# CONNECTION STATUS BANNER
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.get("db_error"):
    st.markdown(f"""
    <div style="background:#FDF0DB; border:1.5px solid #D4A843; border-radius:12px;
                padding:1.2rem 1.6rem; margin-bottom:1.5rem;">
        <p style="margin:0 0 0.4rem; font-family:'Montserrat',sans-serif;
                  font-size:1.05rem; font-weight:600; color:#8B6914;">
            ⚠ Database Connection Failed
        </p>
        <p style="margin:0; font-family:'Montserrat',sans-serif; font-size:0.85rem;
                  color:#5C4A3D; line-height:1.5;">
            The dashboard is running in <strong>offline mode</strong>. Open
            <code>app.py</code> and verify the SERVER name in
            <code>init_connection()</code>, then refresh.<br>
            <span style="color:#C06B42; font-weight:500;">Error:</span>
            <code style="word-break:break-all;">{st.session_state["db_error"]}</code>
        </p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — POINT OF SALE (Sales & Orders — Transactions & Triggers)
# ══════════════════════════════════════════════════════════════════════════════
if page == "🧾  Point of Sale":
    st.markdown("""
    <div class="page-header">
        <h1>Point of Sale</h1>
        <p class="subtitle">Sales &amp; Orders</p>
        <div class="divider-accent"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch lookup data ──
    customers_df = run_query(
        "SELECT CustomerID, First_Name + ' ' + Last_Name AS Name FROM Customers"
    )
    products_df = run_query(
        "SELECT ProductID, Product AS Name, Base_Price FROM vw_ActiveProducts"
    )
    orders_df_lookup = run_query(
        "SELECT Order_ID FROM Orders ORDER BY Order_ID DESC"
    )

    # ── Expander 1: Create & Populate Order ──
    with st.expander("📝 Create & Populate Order", expanded=False):
        st.caption(
            "**Step 1:** `EXEC sp_PlaceOrder` creates the order header.  \n"
            "**Step 2:** `INSERT INTO Order_Details` adds line items (triggers "
            "`trg_UpdateOrderTotalOnDetail` and `trg_DeductIngredientOnProduction`)."
        )

        with st.form("create_populate_order_form"):
            c1, c2 = st.columns(2)
            with c1:
                order_id_input = st.number_input("Order ID", min_value=1, value=200, step=1)
                if customers_df is not None and not customers_df.empty:
                    cust_display = customers_df.apply(
                        lambda r: f"{int(r['CustomerID'])} — {r['Name']}", axis=1
                    ).tolist()
                else:
                    cust_display = ["No customers loaded"]
                selected_cust = st.selectbox("Customer", cust_display, key="pos_cust")
            with c2:
                if products_df is not None and not products_df.empty:
                    prod_display = products_df.apply(
                        lambda r: f"{int(r['ProductID'])} — {r['Name']}  (Rs. {r['Base_Price']})",
                        axis=1,
                    ).tolist()
                else:
                    prod_display = ["No products loaded"]
                selected_prod = st.selectbox("Product", prod_display, key="pos_prod")
                quantity = st.number_input("Quantity", min_value=1, value=1, step=1, key="pos_qty")

            submitted_order = st.form_submit_button("Create Order & Add Item")

        if submitted_order:
            if (
                customers_df is not None and not customers_df.empty
                and selected_cust != "No customers loaded"
                and products_df is not None and not products_df.empty
                and selected_prod != "No products loaded"
            ):
                cust_id = int(selected_cust.split(" — ")[0])
                prod_id = int(selected_prod.split(" — ")[0])
                current_date = datetime.datetime.now().strftime('%Y-%m-%d')

                # Action 1: Create the order header
                ok1, msg1 = execute_action(
                    "EXEC sp_PlaceOrder @Order_ID=?, @CustomerID=?, "
                    "@Order_Date=?, @Tax_Amount=0, @Discount_Amount=0",
                    (order_id_input, cust_id, current_date),
                )
                if ok1:
                    st.success(f"✅ Order #{order_id_input} created successfully.")

                    # Action 2: Insert line item
                    prod_row = products_df[products_df["ProductID"] == prod_id].iloc[0]
                    unit_price = float(prod_row["Base_Price"])
                    line_total = unit_price * quantity

                    next_id_df = run_query(
                        "SELECT ISNULL(MAX(Order_Detail_ID), 0) + 1 AS NextID FROM Order_Details"
                    )
                    next_detail_id = int(next_id_df.iloc[0]["NextID"]) if not next_id_df.empty else 1

                    ok2, msg2 = execute_action(
                        "INSERT INTO Order_Details "
                        "(Order_Detail_ID, Order_ID, ProductID, Quantity, Unit_Price, Line_Total) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (next_detail_id, order_id_input, prod_id, quantity, unit_price, line_total),
                    )
                    if ok2:
                        st.success(
                            f"✅ Added {quantity}× item to Order #{order_id_input}. "
                            f"Triggers `trg_UpdateOrderTotalOnDetail` & `trg_DeductIngredientOnProduction` fired."
                        )
                    else:
                        st.error(f"Line item insertion failed: {msg2}")
                else:
                    st.error(f"Order creation failed: {msg1}")
            else:
                st.warning("Cannot create order — lookup data not loaded.")

    # ── Expander 2: Process Payment ──
    with st.expander("💳 Process Payment", expanded=False):
        st.caption(
            "Calls `EXEC sp_ProcessPayment`. This procedure checks if `Amount_Paid ≥ Final_Total`. "
            "**Try paying less than the order total to trigger the underpayment RAISERROR!**"
        )

        with st.form("process_payment_form"):
            p1, p2, p3 = st.columns(3)
            with p1:
                payment_id = st.number_input("Payment ID", min_value=1, value=100, step=1, key="pay_id")
            with p2:
                if orders_df_lookup is not None and not orders_df_lookup.empty:
                    order_ids_pay = orders_df_lookup["Order_ID"].astype(int).tolist()
                else:
                    order_ids_pay = [0]
                selected_order_pay = st.selectbox("Order ID", order_ids_pay, key="pay_order")
            with p3:
                amount_paid = st.number_input("Amount Paid (Rs.)", min_value=0, value=500, step=50, key="pay_amt")

            submitted_payment = st.form_submit_button("Process Payment")

        if submitted_payment:
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            ok, msg = execute_action(
                "EXEC sp_ProcessPayment @PaymentID=?, @OrderID=?, @PayDate=?, @AmountPaid=?",
                (payment_id, selected_order_pay, current_date, amount_paid),
            )
            if ok:
                st.success(f"✅ Payment #{payment_id} processed for Order #{selected_order_pay}.")
            else:
                st.error(f"🚫 Payment Rejected! {msg}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 1: Recent Orders ──
    st.subheader("Recent Orders")
    orders_df = run_query(
        "SELECT TOP 10 * FROM vw_OrderSummary ORDER BY Order_Date DESC"
    )
    st.dataframe(orders_df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 2: Top Selling Products ──
    st.subheader("Top Selling Products")
    top_df = run_query("SELECT * FROM vw_TopSellingProducts")
    st.dataframe(top_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — SUPPLY CHAIN & INVENTORY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📦  Supply Chain & Inventory":
    st.markdown("""
    <div class="page-header">
        <h1>Supply Chain & Inventory</h1>
        <p class="subtitle">Stock Levels &amp; Purchase Orders</p>
        <div class="divider-accent"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch lookup data ──
    suppliers_df = run_query(
        "SELECT SupplierID, Name FROM Suppliers ORDER BY SupplierID"
    )
    ingredients_df = run_query(
        "SELECT IngredientID, Name FROM Ingredients ORDER BY IngredientID"
    )

    # ── Expander 1: Place Purchase Order ──
    with st.expander("📋 Place Purchase Order", expanded=False):
        st.caption(
            "Calls `EXEC sp_PlacePurchaseOrder` to register a new purchase order with status 'Pending'."
        )

        with st.form("place_po_form"):
            po1, po2, po3 = st.columns(3)
            with po1:
                po_id = st.number_input("PO ID", min_value=1, value=200, step=1, key="po_id")
            with po2:
                if suppliers_df is not None and not suppliers_df.empty:
                    supp_display = suppliers_df.apply(
                        lambda r: f"{int(r['SupplierID'])} — {r['Name']}", axis=1
                    ).tolist()
                else:
                    supp_display = ["No suppliers loaded"]
                selected_supp = st.selectbox("Supplier", supp_display, key="po_supp")
            with po3:
                total_amount = st.number_input("Total Amount (Rs.)", min_value=1, value=5000, step=500, key="po_amt")

            submitted_po = st.form_submit_button("Place Purchase Order")

        if submitted_po:
            if suppliers_df is not None and not suppliers_df.empty and selected_supp != "No suppliers loaded":
                supp_id = int(selected_supp.split(" — ")[0])
                current_date = datetime.datetime.now().strftime('%Y-%m-%d')
                exp_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')

                ok, msg = execute_action(
                    "EXEC sp_PlacePurchaseOrder @PO_ID=?, @SupplierID=?, "
                    "@OrderDate=?, @ExpDate=?, @TotalAmount=?, @Status='Pending'",
                    (po_id, supp_id, current_date, exp_date, total_amount),
                )
                if ok:
                    st.success(f"✅ Purchase Order #{po_id} placed with supplier #{supp_id}.")
                else:
                    st.error(f"PO creation failed: {msg}")
            else:
                st.warning("Cannot create PO — no suppliers loaded.")

    # ── Expander 2: Receive Batch (Trigger Stock Update) ──
    with st.expander("📦 Receive Batch (Trigger Stock Update)", expanded=False):
        st.caption(
            "Calls `EXEC sp_ReceiveBatch`. Upon insertion into `Batches`, "
            "trigger **`trg_UpdateStockOnBatchReceive`** fires automatically to update "
            "`Ingredients.Current_stock`."
        )

        with st.form("receive_batch_form"):
            b1, b2 = st.columns(2)
            with b1:
                batch_id = st.number_input("Batch ID", min_value=1, value=100, step=1, key="batch_id")
                if ingredients_df is not None and not ingredients_df.empty:
                    ingr_display = ingredients_df.apply(
                        lambda r: f"{int(r['IngredientID'])} — {r['Name']}", axis=1
                    ).tolist()
                else:
                    ingr_display = ["No ingredients loaded"]
                selected_ingr = st.selectbox("Ingredient", ingr_display, key="batch_ingr")
            with b2:
                batch_po_id = st.number_input("PO ID (Reference)", min_value=1, value=101, step=1, key="batch_po")
                qty_received = st.number_input("Quantity Received", min_value=1, value=50, step=10, key="batch_qty")

            submitted_batch = st.form_submit_button("Receive Batch")

        if submitted_batch:
            if ingredients_df is not None and not ingredients_df.empty and selected_ingr != "No ingredients loaded":
                ingr_id = int(selected_ingr.split(" — ")[0])
                receive_date = datetime.datetime.now().strftime('%Y-%m-%d')
                expiry_date = (datetime.datetime.now() + datetime.timedelta(days=180)).strftime('%Y-%m-%d')

                ok, msg = execute_action(
                    "EXEC sp_ReceiveBatch @BatchID=?, @IngredientID=?, @PO_ID=?, "
                    "@ReceiveDate=?, @ExpiryDate=?, @QtyReceived=?",
                    (batch_id, ingr_id, batch_po_id, receive_date, expiry_date, qty_received),
                )
                if ok:
                    st.success(
                        f"✅ Batch #{batch_id} received! "
                        f"Trigger `trg_UpdateStockOnBatchReceive` updated stock for ingredient #{ingr_id}."
                    )
                else:
                    st.error(f"Batch receive failed: {msg}")
            else:
                st.warning("Cannot receive batch — no ingredients loaded.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 1: Live Kitchen Stock ──
    st.subheader("Live Kitchen Stock")
    stock_df = run_query("SELECT * FROM vw_CurrentStockLevels")
    st.dataframe(stock_df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 2: Pending Purchase Orders ──
    st.subheader("Pending Purchase Orders")
    po_df = run_query("SELECT * FROM vw_PendingPurchaseOrders")
    st.dataframe(po_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — RECIPES & MANUFACTURING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧁  Recipes & Manufacturing":
    st.markdown("""
    <div class="page-header">
        <h1>Recipes & Manufacturing</h1>
        <p class="subtitle">Product Menu &amp; Recipe Costing</p>
        <div class="divider-accent"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch lookup data ──
    products_df = run_query(
        "SELECT ProductID, Product AS Name FROM vw_ActiveProducts"
    )
    ingredients_df = run_query(
        "SELECT IngredientID, Name FROM Ingredients ORDER BY IngredientID"
    )

    # ── Expander 1: Can We Bake It? (Feasibility Check) ──
    with st.expander("🔍 Can We Bake It? (Feasibility Check)", expanded=False):
        st.caption(
            "Calls `EXEC sp_CheckProductFeasibility`. Returns a table showing whether "
            "each ingredient is sufficient for the requested batch quantity."
        )

        with st.form("feasibility_form"):
            f1, f2 = st.columns(2)
            with f1:
                if products_df is not None and not products_df.empty:
                    prod_display_f = products_df.apply(
                        lambda r: f"{int(r['ProductID'])} — {r['Name']}", axis=1
                    ).tolist()
                else:
                    prod_display_f = ["No products loaded"]
                selected_prod_f = st.selectbox("Product", prod_display_f, key="feas_prod")
            with f2:
                feas_qty = st.number_input("Quantity to Bake", min_value=1, value=10, step=1, key="feas_qty")

            submitted_feas = st.form_submit_button("Check Feasibility")

        if submitted_feas:
            if products_df is not None and not products_df.empty and selected_prod_f != "No products loaded":
                prod_id_f = int(selected_prod_f.split(" — ")[0])
                result_df = run_query_from_proc(
                    "EXEC sp_CheckProductFeasibility @ProductID=?, @Quantity=?",
                    (prod_id_f, feas_qty),
                )
                if not result_df.empty:
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No recipe data found for this product.")
            else:
                st.warning("No products loaded.")

    # ── Expander 2: Update Recipe ──
    with st.expander("📝 Update Recipe", expanded=False):
        st.caption(
            "Calls `EXEC sp_AddRecipeIngredient` to add or update a recipe ingredient mapping."
        )

        with st.form("update_recipe_form"):
            r1, r2 = st.columns(2)
            with r1:
                recipe_id = st.number_input("Recipe ID", min_value=1, value=100, step=1, key="rec_id")
                if products_df is not None and not products_df.empty:
                    prod_display_r = products_df.apply(
                        lambda r: f"{int(r['ProductID'])} — {r['Name']}", axis=1
                    ).tolist()
                else:
                    prod_display_r = ["No products loaded"]
                selected_prod_r = st.selectbox("Product", prod_display_r, key="rec_prod")
            with r2:
                if ingredients_df is not None and not ingredients_df.empty:
                    ingr_display_r = ingredients_df.apply(
                        lambda r: f"{int(r['IngredientID'])} — {r['Name']}", axis=1
                    ).tolist()
                else:
                    ingr_display_r = ["No ingredients loaded"]
                selected_ingr_r = st.selectbox("Ingredient", ingr_display_r, key="rec_ingr")
                qty_required = st.number_input(
                    "Quantity Required", min_value=0.01, value=1.00, step=0.25,
                    format="%.2f", key="rec_qty"
                )

            submitted_recipe = st.form_submit_button("Add / Update Recipe Ingredient")

        if submitted_recipe:
            if (
                products_df is not None and not products_df.empty
                and selected_prod_r != "No products loaded"
                and ingredients_df is not None and not ingredients_df.empty
                and selected_ingr_r != "No ingredients loaded"
            ):
                prod_id_r = int(selected_prod_r.split(" — ")[0])
                ingr_id_r = int(selected_ingr_r.split(" — ")[0])

                ok, msg = execute_action(
                    "EXEC sp_AddRecipeIngredient @RecipeID=?, @ProductID=?, @IngredientID=?, @QtyRequired=?",
                    (recipe_id, prod_id_r, ingr_id_r, qty_required),
                )
                if ok:
                    st.success(f"✅ Recipe #{recipe_id} updated — ingredient #{ingr_id_r} linked to product #{prod_id_r}.")
                else:
                    st.error(f"Recipe update failed: {msg}")
            else:
                st.warning("Lookup data not loaded.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 1: Active Bakery Menu ──
    st.subheader("Active Bakery Menu")
    menu_df = run_query("SELECT * FROM vw_ActiveProducts")
    st.dataframe(menu_df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 2: Master Recipe Costing ──
    st.subheader("Master Recipe Costing")
    recipe_df = run_query("SELECT * FROM vw_ProductRecipeDetail")
    st.dataframe(recipe_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — LOGISTICS & DELIVERY
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🚚  Logistics & Delivery":
    st.markdown("""
    <div class="page-header">
        <h1>Logistics & Delivery</h1>
        <p class="subtitle">Dispatch Board &amp; Rider Trigger Demo</p>
        <div class="divider-accent"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch lookup data ──
    orders_for_delivery = run_query("SELECT Order_ID FROM Orders ORDER BY Order_ID DESC")
    riders_df = run_query(
        "SELECT Rider_ID, First_Name + ' ' + Last_Name AS Name FROM Delivery_Riders"
    )
    active_deliveries_df = run_query(
        "SELECT Delivery_ID FROM Deliveries WHERE Delivery_Status = 0 ORDER BY Delivery_ID"
    )

    # ── Expander 1: Dispatch Rider ──
    with st.expander("🚴 Dispatch Rider", expanded=False):
        st.caption(
            "Calls `EXEC sp_AssignDelivery`. Trigger **`trg_ValidateRiderAvailability`** checks "
            "if the rider is already on an active delivery. **Try assigning a busy rider to see it reject!**"
        )

        with st.form("dispatch_rider_form"):
            d1, d2, d3 = st.columns(3)
            with d1:
                delivery_id_input = st.number_input("Delivery ID", min_value=1, value=100, step=1, key="del_id")
            with d2:
                if orders_for_delivery is not None and not orders_for_delivery.empty:
                    order_ids_del = orders_for_delivery["Order_ID"].astype(int).tolist()
                else:
                    order_ids_del = [0]
                selected_order_del = st.selectbox("Order ID", order_ids_del, key="del_order")
            with d3:
                if riders_df is not None and not riders_df.empty:
                    rider_display = riders_df.apply(
                        lambda r: f"{int(r['Rider_ID'])} — {r['Name']}", axis=1
                    ).tolist()
                else:
                    rider_display = ["No riders loaded"]
                selected_rider = st.selectbox("Rider", rider_display, key="del_rider")

            submitted_dispatch = st.form_submit_button("Dispatch Rider")

        if submitted_dispatch:
            if riders_df is not None and not riders_df.empty and selected_rider != "No riders loaded":
                rider_id = int(selected_rider.split(" — ")[0])
                ok, msg = execute_action(
                    "EXEC sp_AssignDelivery @DeliveryID=?, @OrderID=?, @RiderID=?, @AddressID=1",
                    (delivery_id_input, selected_order_del, rider_id),
                )
                if ok:
                    st.success(
                        f"✅ Delivery #{delivery_id_input} dispatched! "
                        f"Trigger `trg_SetDispatchTime` auto-stamped the time."
                    )
                else:
                    st.error(f"🚫 Trigger Rejection! {msg}")
            else:
                st.warning("Cannot assign — no riders loaded.")

    # ── Expander 2: Complete Delivery ──
    with st.expander("✅ Complete Delivery", expanded=False):
        st.caption(
            "Calls `EXEC sp_CompleteDelivery` to mark a delivery as completed "
            "and stamp the delivery time."
        )

        with st.form("complete_delivery_form"):
            if active_deliveries_df is not None and not active_deliveries_df.empty:
                active_del_ids = active_deliveries_df["Delivery_ID"].astype(int).tolist()
            else:
                active_del_ids = [0]
            selected_del_complete = st.selectbox(
                "Active Delivery ID", active_del_ids, key="del_complete"
            )

            submitted_complete = st.form_submit_button("Mark as Delivered")

        if submitted_complete:
            if active_deliveries_df is not None and not active_deliveries_df.empty:
                ok, msg = execute_action(
                    "EXEC sp_CompleteDelivery @DeliveryID=?",
                    (selected_del_complete,),
                )
                if ok:
                    st.success(f"✅ Delivery #{selected_del_complete} marked as completed!")
                else:
                    st.error(f"Completion failed: {msg}")
            else:
                st.warning("No active deliveries to complete.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 1: Active Dispatch Board ──
    st.subheader("Active Dispatch Board")
    dispatch_df = run_query("SELECT * FROM vw_ActiveDeliveries")
    st.dataframe(dispatch_df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 2: Rider Performance Metrics ──
    st.subheader("Rider Performance Metrics")
    rider_perf_df = run_query("SELECT * FROM vw_RiderPerformance")
    st.dataframe(rider_perf_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — HR & OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👨‍🍳  HR & Operations":
    st.markdown("""
    <div class="page-header">
        <h1>HR & Operations</h1>
        <p class="subtitle">Staff Management &amp; Equipment</p>
        <div class="divider-accent"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch lookup data ──
    equipment_df = run_query(
        "SELECT Equipment_ID, Equipment_Name FROM Kitchen_Equipment ORDER BY Equipment_ID"
    )

    # ── Expander 1: Hire New Staff ──
    with st.expander("👤 Hire New Staff", expanded=False):
        st.caption(
            "Calls `EXEC sp_HireEmployee`. Trigger **`trg_PreventNegativeSalary`** rejects "
            "any salary ≤ 0. **Try entering a negative salary to watch the trigger block it!**"
        )

        with st.form("hire_form"):
            h1, h2 = st.columns(2)
            with h1:
                emp_id = st.number_input("Employee ID", min_value=1, value=100, step=1, key="hire_id")
                first_name = st.text_input("First Name", key="hire_fname")
                last_name = st.text_input("Last Name", key="hire_lname")
            with h2:
                phone = st.text_input("Phone", key="hire_phone")
                salary = st.number_input(
                    "Salary (Rs.)", min_value=-99999, value=30000, step=1000, key="hire_salary"
                )
                st.markdown(
                    '<p style="font-size:0.78rem; color:#C06B42; margin-top:0.5rem;">'
                    '⚡ Enter a negative or zero salary to test the trigger rejection!</p>',
                    unsafe_allow_html=True,
                )

            hire_submitted = st.form_submit_button("Hire Employee")

        if hire_submitted:
            if first_name.strip() and last_name.strip():
                ok, msg = execute_action(
                    "EXEC sp_HireEmployee @EmpID=?, @FirstName=?, @LastName=?, @Phone=?, @Salary=?",
                    (emp_id, first_name.strip(), last_name.strip(), phone.strip(), salary),
                )
                if ok:
                    st.success(f"✅ Employee '{first_name} {last_name}' (ID: {emp_id}) hired successfully!")
                else:
                    st.error(f"🚫 Trigger Rejection! {msg}")
            else:
                st.warning("Please enter both first and last name.")

    # ── Expander 2: Update Equipment Status ──
    with st.expander("🔧 Update Equipment Status", expanded=False):
        st.caption(
            "Calls `EXEC sp_UpdateEquipmentStatus`. Valid statuses: "
            "'Working', 'Under Repair', 'Not Working'."
        )

        with st.form("update_equip_form"):
            e1, e2 = st.columns(2)
            with e1:
                if equipment_df is not None and not equipment_df.empty:
                    equip_display = equipment_df.apply(
                        lambda r: f"{int(r['Equipment_ID'])} — {r['Equipment_Name']}", axis=1
                    ).tolist()
                else:
                    equip_display = ["No equipment loaded"]
                selected_equip = st.selectbox("Equipment", equip_display, key="equip_sel")
            with e2:
                new_status = st.selectbox(
                    "New Status",
                    ["Working", "Under Repair", "Not Working"],
                    key="equip_status",
                )

            submitted_equip = st.form_submit_button("Update Status")

        if submitted_equip:
            if equipment_df is not None and not equipment_df.empty and selected_equip != "No equipment loaded":
                equip_id = int(selected_equip.split(" — ")[0])
                ok, msg = execute_action(
                    "EXEC sp_UpdateEquipmentStatus @EquipmentID=?, @NewStatus=?",
                    (equip_id, new_status),
                )
                if ok:
                    st.success(f"✅ Equipment #{equip_id} status updated to '{new_status}'.")
                else:
                    st.error(f"Status update failed: {msg}")
            else:
                st.warning("No equipment loaded.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 1: Equipment Warranty Tracking ──
    st.subheader("Equipment Warranty Tracking")
    equip_df = run_query("SELECT * FROM vw_EquipmentStatusSummary")
    st.dataframe(equip_df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table 2: Monthly Payroll Overview ──
    st.subheader("Monthly Payroll Overview")
    salary_df = run_query("SELECT * FROM vw_SalarySummary")
    st.dataframe(salary_df, use_container_width=True, hide_index=True)