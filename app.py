import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

DB_PATH = "boutique.db"

STAGES = [
    "With Mom",
    "With Dad",
    "At Dyeing",
    "Back From Dyeing",
    "Lining",
    "Master Marking",
    "Embroidery",
    "Master Cutting",
    "Tailor Stitching",
    "Finished With Vishwa",
    "Delivered",
]


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Orders table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # Staff table
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

    # Work log table
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
    """Seed staff only if table is empty."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM staff")
    count = cur.fetchone()["c"]
    if count == 0:
        staff_rows = [
            # Masters
            ("Mariswamy", "Master", "", 1),
            ("Hassan", "Master", "", 1),
            ("Shameen", "Master", "", 1),
            ("Abdul", "Master", "", 1),
            # Tailors under masters
            ("Anand Rao", "Tailor", "Mariswamy", 1),
            ("Lucky", "Tailor", "Mariswamy", 1),
            ("Aslam", "Tailor", "Hassan", 1),
            ("Shafiq", "Tailor", "Hassan", 1),
            ("Sameerul", "Tailor", "Hassan", 1),
            ("Sridhar", "Tailor", "Shameen", 1),
            ("Rashid", "Tailor", "Shameen", 1),
            ("Shaman", "Tailor", "Shameen", 1),
            ("Zajeer", "Tailor", "Shameen", 1),
            # Add embroidery staff names here when you know them
            # ("XYZ", "Embroidery", "", 1),
        ]
        cur.executemany(
            "INSERT INTO staff (name, role, reports_to, active) VALUES (?, ?, ?, ?)",
            staff_rows,
        )
        conn.commit()
    conn.close()


def bool_to_int(b):
    return 1 if b else 0


def get_staff(role=None):
    conn = get_conn()
    if role:
        df = pd.read_sql_query(
            "SELECT * FROM staff WHERE role = ? AND active = 1 ORDER BY name",
            conn,
            params=(role,),
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM staff WHERE active = 1 ORDER BY role, name", conn
        )
    conn.close()
    return df


def get_orders(stage=None):
    conn = get_conn()
    if stage:
        df = pd.read_sql_query(
            "SELECT * FROM orders WHERE current_stage = ? ORDER BY due_date",
            conn,
            params=(stage,),
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM orders ORDER BY due_date", conn
        )
    conn.close()
    return df


def insert_order(
    client_name,
    phone,
    order_date,
    due_date,
    needs_dyeing,
    needs_embroidery,
    needs_market,
    master_assigned,
    tailor_assigned,
    comments,
):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        """
        INSERT INTO orders (
            client_name, phone, order_date, due_date,
            needs_dyeing, needs_embroidery, needs_market,
            master_assigned, tailor_assigned,
            current_stage, comments, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            client_name,
            phone,
            order_date,
            due_date,
            bool_to_int(needs_dyeing),
            bool_to_int(needs_embroidery),
            bool_to_int(needs_market),
            master_assigned,
            tailor_assigned if tailor_assigned else None,
            "With Mom",
            comments,
            now,
        ),
    )
    conn.commit()
    conn.close()


def update_order_stage(order_id, new_stage):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        "UPDATE orders SET current_stage = ?, last_updated = ? WHERE id = ?",
        (new_stage, now, order_id),
    )
    conn.commit()
    conn.close()


def update_order_tailor(order_id, tailor_name):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        "UPDATE orders SET tailor_assigned = ?, last_updated = ? WHERE id = ?",
        (tailor_name, now, order_id),
    )
    conn.commit()
    conn.close()


def log_work(work_date, order_id, staff_name, role, work_type, notes):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO worklog (work_date, order_id, staff_name, role, work_type, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (work_date, order_id, staff_name, role, work_type, notes),
    )
    conn.commit()
    conn.close()


def get_work_for_staff(staff_name, work_date=None):
    conn = get_conn()
    if work_date:
        df = pd.read_sql_query(
            """
            SELECT * FROM worklog
            WHERE staff_name = ? AND work_date = ?
            """,
            conn,
            params=(staff_name, work_date),
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM worklog WHERE staff_name = ?", conn, params=(staff_name,)
        )
    conn.close()
    return df


def main():
    st.set_page_config(page_title="Boutique Production System", layout="wide")
    st.title("🧵 Boutique Production System")

    init_db()
    seed_staff()

    pages = [
        "New Order",
        "Orders by Stage",
        "Log Work Done",
        "Masters Performance",
        "Tailors Performance",
        "Dashboard",
    ]
    page = st.sidebar.radio("Navigate", pages)

    if page == "New Order":
        st.header("Create New Order")

        with st.form("new_order_form"):
            client_name = st.text_input("Client name")
            phone = st.text_input("Phone")
            order_date = st.date_input("Order date", value=date.today())
            due_date = st.date_input("Due date")

            col1, col2, col3 = st.columns(3)
            with col1:
                needs_dyeing = st.checkbox("Needs dyeing?")
            with col2:
                needs_embroidery = st.checkbox("Needs embroidery?")
            with col3:
                needs_market = st.checkbox("Needs market blouse?")

            masters_df = get_staff("Master")
            master_assigned = st.selectbox(
                "Master assigned",
                masters_df["name"].tolist() if not masters_df.empty else [],
            )

            tailors_df = get_staff("Tailor")
            tailor_option = st.selectbox(
                "Tailor assigned (optional)",
                ["(Assign later)"]
                + (tailors_df["name"].tolist() if not tailors_df.empty else []),
            )
            tailor_assigned = (
                None if tailor_option == "(Assign later)" else tailor_option
            )

            comments = st.text_area("Notes / comments", "")

            submitted = st.form_submit_button("Save Order")

        if submitted:
            if not client_name or not master_assigned:
                st.error("Client name and Master are required.")
            else:
                insert_order(
                    client_name,
                    phone,
                    order_date.isoformat(),
                    due_date.isoformat(),
                    needs_dyeing,
                    needs_embroidery,
                    needs_market,
                    master_assigned,
                    tailor_assigned,
                    comments,
                )
                st.success("Order saved and set to stage: With Mom ✅")

    elif page == "Orders by Stage":
        st.header("Orders by Stage")

        stage_filter = st.selectbox("Filter by stage", ["All"] + STAGES)
        if stage_filter == "All":
            orders_df = get_orders()
        else:
            orders_df = get_orders(stage_filter)

        if orders_df.empty:
            st.info("No orders found.")
        else:
            st.dataframe(orders_df)

            st.subheader("Update an order")
            order_ids = orders_df["id"].tolist()
            selected_id = st.selectbox("Select order ID", order_ids)
            selected_row = orders_df[orders_df["id"] == selected_id].iloc[0]

            st.write(
                f"Client: **{selected_row['client_name']}** | Current stage: **{selected_row['current_stage']}**"
            )

            col1, col2 = st.columns(2)
            with col1:
                new_stage = st.selectbox(
                    "New stage", STAGES, index=STAGES.index(selected_row["current_stage"])
                )
                if st.button("Update Stage"):
                    update_order_stage(int(selected_id), new_stage)
                    st.success("Stage updated ✅")
            with col2:
                tailors_df = get_staff("Tailor")
                if not tailors_df.empty:
                    new_tailor = st.selectbox(
                        "Assign / change tailor",
                        ["(No change)"] + tailors_df["name"].tolist(),
                    )
                    if st.button("Update Tailor"):
                        if new_tailor != "(No change)":
                            update_order_tailor(int(selected_id), new_tailor)
                            st.success("Tailor updated ✅")

    elif page == "Log Work Done":
        st.header("Log Work Done (Marking / Cutting / Stitching)")

        orders_df = get_orders()
        staff_df = get_staff()

        if orders_df.empty or staff_df.empty:
            st.info("Need at least one order and one staff to log work.")
        else:
            with st.form("work_log_form"):
                work_date = st.date_input("Date", value=date.today())

                staff_name = st.selectbox("Staff name", staff_df["name"].tolist())
                role_default = (
                    staff_df.set_index("name").loc[staff_name]["role"]
                    if staff_name in staff_df["name"].values
                    else "Master"
                )
                role = st.selectbox(
                    "Role",
                    ["Master", "Tailor", "Embroidery"],
                    index=["Master", "Tailor", "Embroidery"].index(role_default),
                )

                order_id = st.selectbox("Order ID", orders_df["id"].tolist())

                if role == "Master":
                    work_type = st.selectbox("Work type", ["Marking", "Cutting"])
                elif role == "Tailor":
                    work_type = st.selectbox("Work type", ["Blouse Stitched"])
                else:
                    work_type = st.selectbox("Work type", ["Embroidery Done"])

                notes = st.text_area("Notes", "")

                submitted = st.form_submit_button("Save Work Entry")

            if submitted:
                log_work(
                    work_date.isoformat(),
                    int(order_id),
                    staff_name,
                    role,
                    work_type,
                    notes,
                )
                st.success("Work logged ✅")

    elif page == "Masters Performance":
        st.header("Masters Performance (Today)")

        masters_df = get_staff("Master")
        if masters_df.empty:
            st.info("No masters defined.")
        else:
            today_str = date.today().isoformat()
            rows = []
            for _, row in masters_df.iterrows():
                name = row["name"]
                work_df = get_work_for_staff(name, today_str)
                markings = len(
                    work_df[work_df["work_type"] == "Marking"]["order_id"].unique()
                )
                cuttings = len(
                    work_df[work_df["work_type"] == "Cutting"]["order_id"].unique()
                )

                rows.append(
                    {
                        "Master": name,
                        "Markings Today": markings,
                        "Markings Target": 4,
                        "Cuttings Today": cuttings,
                        "Cuttings Target": 6,
                    }
                )

            perf_df = pd.DataFrame(rows)
            st.dataframe(perf_df)

    elif page == "Tailors Performance":
        st.header("Tailors Performance (Today)")

        tailors_df = get_staff("Tailor")
        if tailors_df.empty:
            st.info("No tailors defined.")
        else:
            today_str = date.today().isoformat()
            rows = []
            for _, row in tailors_df.iterrows():
                name = row["name"]
                work_df = get_work_for_staff(name, today_str)
                stitched = len(
                    work_df[work_df["work_type"] == "Blouse Stitched"]["order_id"].unique()
                )

                rows.append(
                    {
                        "Tailor": name,
                        "Blouses Stitched Today": stitched,
                        "Target": 3,
                        "Reports To": row["reports_to"],
                    }
                )

            perf_df = pd.DataFrame(rows)
            st.dataframe(perf_df)

    elif page == "Dashboard":
        st.header("Dashboard")

        orders_df = get_orders()
        if orders_df.empty:
            st.info("No orders yet.")
        else:
            today_str = date.today().isoformat()

            orders_df["due_date"] = pd.to_datetime(orders_df["due_date"])
            today = pd.to_datetime(today_str)

            overdue = orders_df[
                (orders_df["due_date"] < today)
                & (orders_df["current_stage"] != "Delivered")
            ]
            due_today = orders_df[
                (orders_df["due_date"] == today)
                & (orders_df["current_stage"] != "Delivered")
            ]

            st.subheader("Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total orders", len(orders_df))
            with col2:
                st.metric("Overdue", len(overdue))
            with col3:
                st.metric("Due today", len(due_today))

            st.subheader("Overdue orders")
            if overdue.empty:
                st.write("✅ None overdue")
            else:
                st.dataframe(overdue)

            st.subheader("Due today")
            if due_today.empty:
                st.write("✅ None due today")
            else:
                st.dataframe(due_today)

            st.subheader("Orders by stage")
            stage_counts = orders_df.groupby("current_stage")["id"].count().reset_index()
            st.dataframe(stage_counts)


if __name__ == "__main__":
    main()
