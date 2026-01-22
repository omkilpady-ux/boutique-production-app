import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

DB_PATH = "boutique.db"

STAGES = [
    "With Designer",
    "With Manager",
    "At Dyeing",
    "Back From Dyeing",
    "Lining",
    "Master Marking",
    "Embroidery",
    "Master Cutting",
    "Tailor Stitching",
    "Finished With Vishwa",
    "Delivered",
    "Cancelled",
]


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT,
            client_name TEXT,
            phone TEXT,
            order_date TEXT,
            due_date TEXT,
            needs_dyeing INTEGER,
            needs_embroidery INTEGER,
            needs_market INTEGER,
            master_assigned TEXT,
            tailor_assigned TEXT,
            current_stage TEXT,
            comments TEXT,
            last_updated TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            name TEXT PRIMARY KEY,
            role TEXT,
            reports_to TEXT,
            active INTEGER
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS worklog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date TEXT,
            order_id INTEGER,
            staff_name TEXT,
            role TEXT,
            work_type TEXT,
            notes TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def seed_staff():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM staff")
    if cur.fetchone()[0] == 0:
        staff = [
            ("Mariswamy", "Master", "", 1),
            ("Hassan", "Master", "", 1),
            ("Shameen", "Master", "", 1),
            ("Abdul", "Master", "", 1),
            ("Anand Rao", "Tailor", "Mariswamy", 1),
            ("Lucky", "Tailor", "Mariswamy", 1),
            ("Aslam", "Tailor", "Hassan", 1),
            ("Shafiq", "Tailor", "Hassan", 1),
            ("Sameerul", "Tailor", "Hassan", 1),
            ("Sridhar", "Tailor", "Shameen", 1),
            ("Rashid", "Tailor", "Shameen", 1),
            ("Shaman", "Tailor", "Shameen", 1),
            ("Zajeer", "Tailor", "Shameen", 1),
        ]
        cur.executemany(
            "INSERT INTO staff VALUES (?, ?, ?, ?)", staff
        )
        conn.commit()
    conn.close()


def main():
    st.set_page_config(page_title="Boutique Production System", layout="wide")
    st.title("🧵 Boutique Production System")

    init_db()
    seed_staff()

    page = st.sidebar.radio(
        "Navigate",
        [
            "New Order",
            "Orders by Stage",
            "Log Work Done",
            "Masters Performance",
            "Tailors Performance",
            "Dashboard",
        ],
    )

    # ---------------- NEW ORDER ----------------
    if page == "New Order":
        with st.form("new_order"):
            order_number = st.text_input("Order number (from slip)")
            client_name = st.text_input("Client name")
            phone = st.text_input("Phone")
            order_date = st.date_input("Order date", date.today())
            due_date = st.date_input("Due date")

            needs_dyeing = st.checkbox("Needs dyeing?")
            needs_embroidery = st.checkbox("Needs embroidery?")
            needs_market = st.checkbox("Needs market blouse?")

            masters = pd.read_sql("SELECT name FROM staff WHERE role='Master'", get_conn())
            master = st.selectbox("Master assigned", masters["name"])

            tailors = pd.read_sql("SELECT name FROM staff WHERE role='Tailor'", get_conn())
            tailor = st.selectbox(
                "Tailor assigned (optional)",
                ["Assign later"] + tailors["name"].tolist(),
            )

            comments = st.text_area("Notes")
            submit = st.form_submit_button("Save Order")

        if submit:
            if not order_number or not client_name:
                st.error("Order number and client name required")
            else:
                conn = get_conn()
                conn.execute(
                    """
                    INSERT INTO orders
                    (order_number, client_name, phone, order_date, due_date,
                     needs_dyeing, needs_embroidery, needs_market,
                     master_assigned, tailor_assigned, current_stage, comments, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_number,
                        client_name,
                        phone,
                        order_date.isoformat(),
                        due_date.isoformat(),
                        int(needs_dyeing),
                        int(needs_embroidery),
                        int(needs_market),
                        master,
                        None if tailor == "Assign later" else tailor,
                        "With Designer",
                        comments,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                conn.close()
                st.success(f"Order {order_number} created ✅")

    # ---------------- ORDERS BY STAGE ----------------
    elif page == "Orders by Stage":
        orders = pd.read_sql("SELECT * FROM orders", get_conn())

        stage_filter = st.selectbox("Filter stage", ["All"] + STAGES)
        if stage_filter != "All":
            orders = orders[orders["current_stage"] == stage_filter]

        st.dataframe(orders)

        if not orders.empty:
            order_map = {
                row["id"]: f'{row["order_number"]} – {row["client_name"]}'
                for _, row in orders.iterrows()
            }

            selected_id = st.selectbox("Select order", order_map.keys(), format_func=lambda x: order_map[x])
            selected = orders[orders["id"] == selected_id].iloc[0]

            col1, col2 = st.columns(2)

            with col1:
                new_stage = st.selectbox("Change stage", STAGES, index=STAGES.index(selected["current_stage"]))
                if st.button("Update Stage"):
                    conn = get_conn()
                    conn.execute(
                        "UPDATE orders SET current_stage=?, last_updated=? WHERE id=?",
                        (new_stage, datetime.now().isoformat(), selected_id),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Stage updated")

                st.markdown("---")
                st.warning("Danger zone")

                confirm = st.checkbox(f"Confirm cancel {selected['order_number']}")
                if confirm and st.button("❌ Cancel Order"):
                    conn = get_conn()
                    conn.execute(
                        "UPDATE orders SET current_stage='Cancelled', last_updated=? WHERE id=?",
                        (datetime.now().isoformat(), selected_id),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Order cancelled")

            with col2:
                tailors = pd.read_sql("SELECT name FROM staff WHERE role='Tailor'", get_conn())
                new_tailor = st.selectbox("Assign / change tailor", ["No change"] + tailors["name"].tolist())
                if new_tailor != "No change" and st.button("Update Tailor"):
                    conn = get_conn()
                    conn.execute(
                        "UPDATE orders SET tailor_assigned=?, last_updated=? WHERE id=?",
                        (new_tailor, datetime.now().isoformat(), selected_id),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Tailor updated")

    # ---------------- DASHBOARD ----------------
    elif page == "Dashboard":
        orders = pd.read_sql("SELECT * FROM orders", get_conn())
        orders["due_date"] = pd.to_datetime(orders["due_date"])
        today = pd.to_datetime(date.today())

        active = orders[~orders["current_stage"].isin(["Delivered", "Cancelled"])]

        st.metric("Total Orders", len(orders))
        st.metric("Overdue", len(active[active["due_date"] < today]))
        st.metric("Due Today", len(active[active["due_date"] == today]))
        st.metric("Due Next 7 Days", len(active[(active["due_date"] > today) & (active["due_date"] <= today + timedelta(days=7))]))

        st.dataframe(orders)


if __name__ == "__main__":
    main()
