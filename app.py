import pandas as pd
import streamlit as st

st.title("APH Probation Point Check")

st.write(
    "Upload the Flare points CSV, enter point requirements, and generate a probation-only results file."
)

# -----------------------------
# Step 1: Upload CSV
# -----------------------------
uploaded_file = st.file_uploader("Upload Flare points CSV", type=["csv"])

# -----------------------------
# Step 2: Enter point check date
# -----------------------------
date_input = st.text_input("Enter point check date (MM/DD/YY)", placeholder="10/15/26")

if uploaded_file is not None:
    # -----------------------------
    # Step 3: Read CSV
    # Flare CSV has a title row, so skiprows=1
    # -----------------------------
    df = pd.read_csv(uploaded_file, skiprows=1)

    st.subheader("CSV Preview")
    st.dataframe(df.head())

    # -----------------------------
    # Step 4: Detect point categories
    # -----------------------------
    name_column = "Name"
    excluded_columns = ["Name", "Total"]

    point_categories = [col for col in df.columns if col not in excluded_columns]

    st.subheader("Detected Point Categories")

    for category in point_categories:
        st.write(f"- {category}")

    confirm_categories = st.checkbox("These point categories are correct")

    if confirm_categories:
        # -----------------------------
        # Step 5: Convert blank point cells to 0
        # -----------------------------
        df[point_categories] = df[point_categories].fillna(0)

        for category in point_categories:
            df[category] = pd.to_numeric(df[category], errors="coerce").fillna(0)

        # -----------------------------
        # Step 6: Enter required points
        # -----------------------------
        st.subheader("Enter Required Points")

        requirements = {}

        for category in point_categories:
            requirements[category] = st.number_input(
                f"Required points for {category}",
                min_value=0.0,
                step=0.5,
                format="%.1f"
            )

        # -----------------------------
        # Step 7: Run point check
        # -----------------------------
        if st.button("Run Point Check"):
            if date_input.strip() == "":
                st.error("Please enter a point check date before running.")
            else:
                safe_date = date_input.replace("/", "-")

                probation_results = []

                for _, row in df.iterrows():
                    name = row[name_column]
                    missing_categories = []

                    for category in point_categories:
                        current_points = row[category]
                        required_points = requirements[category]

                        if current_points < required_points:
                            missing_categories.append(
                                f"{category}: {current_points:g}/{required_points:g} Points"
                            )

                    status = "On Probation" if missing_categories else "Good Standing"

                    probation_results.append({
                        "Name": name,
                        "Status": status,
                        "Missing Categories": "; ".join(missing_categories) if missing_categories else "None"
                    })

                results_df = pd.DataFrame(probation_results)

                # -----------------------------
                # Step 8: Create probation messages
                # -----------------------------
                def create_probation_message(row):
                    if row["Status"] == "Good Standing":
                        return ""

                    name = row["Name"]

                    missing_items = row["Missing Categories"].split("; ")
                    missing = "\n".join([f"- {item}" for item in missing_items])

                    message = f"""Howdy {name},

I am writing to inform you that, based on a recent review of your participation and involvement in Aggies Pursuing Healthcare, you have been placed on probation for the Fall 2026 semester due to not fulfilling the following membership point requirements:

{missing}

Please reach out if you have any questions."""

                    return message

                results_df["Probation Message"] = results_df.apply(create_probation_message, axis=1)

                # -----------------------------
                # Step 9: Keep only probation members
                # -----------------------------
                probation_only_df = results_df[results_df["Status"] == "On Probation"]

                st.subheader("Probation Results")
                st.write(f"Total members on probation: {len(probation_only_df)}")
                st.dataframe(probation_only_df)

                # -----------------------------
                # Step 10: Download CSV
                # -----------------------------
                output_filename = f"probation_results_{safe_date}.csv"

                csv = probation_only_df.to_csv(index=False)

                st.download_button(
                    label="Download Probation Results CSV",
                    data=csv,
                    file_name=output_filename,
                    mime="text/csv"
                )

                # -----------------------------
                # Step 11: Show copy/paste messages
                # -----------------------------
                st.subheader("Copy/Paste Probation Messages")

                for _, row in probation_only_df.iterrows():
                    st.text_area(
                        label=row["Name"],
                        value=row["Probation Message"],
                        height=250
                    )
