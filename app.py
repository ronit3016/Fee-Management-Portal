import streamlit as st
import pandas as pd
import os
import urllib.parse

st.set_page_config(page_title="Fee Management Portal", page_icon="📊", layout="wide")


FILE = "students.csv"

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]

# Load data
def load_data():
    if not os.path.exists(FILE):
        return pd.DataFrame(columns=["name", "class", "phone", "fees", "months"])
    
    df = pd.read_csv(FILE)

    if "months" not in df.columns:
        df["months"] = ""

    return df

# Save data
def save_data(df):
    df.to_csv(FILE, index=False)

# Convert string → dict
def parse_months(month_str):
    result = {m: "Pending" for m in MONTHS}
    if pd.isna(month_str) or month_str == "":
        return result

    for item in month_str.split(","):
        m, s = item.split(":")
        result[m] = s
    return result

# Convert dict → string
def format_months(month_dict):
    return ",".join([f"{m}:{month_dict[m]}" for m in MONTHS])

st.title("📚 Fee Management Portal")

menu = st.sidebar.selectbox("Menu", ["Add Student", "View Students", "Dashboard"])

df = load_data()


def get_whatsapp_link(phone, name, fees, month_dict):
    pending_months = [m for m, status in month_dict.items() if status == "Pending"]

    if not pending_months:
        return None

    message = f"Hello {name},\n\nYour tuition fees are pending for:\n"

    total_due = 0

    for m in pending_months:
        message += f"• {m} - ₹{fees}\n"
        total_due += fees

    message += f"\nTotal Due: ₹{total_due}\n\nPlease pay at your earliest convenience. Thank you!"

    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/91{phone}?text={encoded_message}"

# ---------------- ADD STUDENT ----------------
if menu == "Add Student":
    st.subheader("➕ Add New Student")

    name = st.text_input("Name")
    student_class = st.text_input("Class")
    phone = st.text_input("Phone")
    fees = st.number_input("Fees", min_value=0)

    if st.button("Add Student"):
        month_dict = {m: "Pending" for m in MONTHS}
        new_data = pd.DataFrame([[name, student_class, phone, fees, format_months(month_dict)]],
                                columns=df.columns)
        df = pd.concat([df, new_data], ignore_index=True)
        save_data(df)
        st.success("Student Added Successfully!")

# ---------------- VIEW STUDENTS ----------------
elif menu == "View Students":
    st.subheader("📋 Student List")

    search = st.text_input("Search by name")

    df_display = df.copy()
    if search:
        df_display = df_display[df_display["name"].str.contains(search, case=False, na=False)]

    if df_display.empty:
        st.warning("No students found.")
    else:
        for original_index in df_display.index:
            row = df.loc[original_index]

            st.markdown(f"### 👤 {row['name']} | Class {row['class']} | ₹{row['fees']}")

            month_dict = parse_months(row["months"])

            cols = st.columns(4)

            # 🔁 ALL MONTHS TOGGLE
            for idx, m in enumerate(MONTHS):
                col = cols[idx % 4]
                key = f"{original_index}_{m}"

                if month_dict[m] == "Paid":
                    if col.button(f"✅ {m}", key=key):
                        month_dict[m] = "Pending"
                        df.at[original_index, "months"] = format_months(month_dict)
                        save_data(df)
                        st.rerun()
                else:
                    if col.button(f"❌ {m}", key=key):
                        month_dict[m] = "Paid"
                        df.at[original_index, "months"] = format_months(month_dict)
                        save_data(df)
                        st.rerun()

            # 📲 WhatsApp Reminder (if ANY month pending)
            if "Pending" in month_dict.values():
                whatsapp_link = get_whatsapp_link(row["phone"], row["name"], row["fees"], month_dict)

                if whatsapp_link:
                   st.markdown(f"[📲 Send Reminder]({whatsapp_link})")

            # 🗑️ Delete
            if st.button("Delete Student", key=f"delete_{original_index}"):
                df = df.drop(original_index)
                save_data(df)
                st.rerun()

            st.divider()

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    st.subheader("📊 Dashboard")

    total_students = len(df)

    paid_students = 0
    pending_students = 0
    total_collection = 0

    for _, row in df.iterrows():
        month_dict = parse_months(row["months"])

        # If ALL months paid → student paid
        if all(status == "Paid" for status in month_dict.values()):
            paid_students += 1
        else:
            pending_students += 1

        # Collection = sum of all paid months
        for m in MONTHS:
            if month_dict[m] == "Paid":
                total_collection += row["fees"]

    st.metric("Total Students", total_students)
    st.metric("Paid Students (All Months)", paid_students)
    st.metric("Pending Students", pending_students)
    st.metric("Total Collection ₹", total_collection)