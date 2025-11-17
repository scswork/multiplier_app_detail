import streamlit as st
import pandas as pd
from io import BytesIO
import openpyxl

# -------------------------------
# Replace with your new dataset raw GitHub CSV URL
url = "https://raw.githubusercontent.com/scswork/multiplier_app_detail/refs/heads/main/multiplier_2021_data_detail.csv"
# -------------------------------

# Load dataset
df = pd.read_csv(url)

st.title("Economic Impact Report")

# Sidebar layout
st.sidebar.header("Filters")

# Industry filter (for CAPEX/OPEX selection)
capex_industry = st.sidebar.selectbox("Select CAPEX Industry", options=df['Industry'].unique())
opex_industry = st.sidebar.selectbox("Select OPEX Industry", options=df['Industry'].unique())

# Type and Variable filters
type_filter = st.sidebar.multiselect("Filter by Multiplier Type", options=df['Multiplier type'].unique(), default=list(df['Multiplier type'].unique()))
variable_filter = st.sidebar.multiselect("Filter by Variable", options=df['Variable'].unique(), default=list(df['Variable'].unique()))

st.sidebar.markdown("---")
st.sidebar.subheader("Enter 15-Year Investment Data")

# Editable table with dropdown for CAPEX/OPEX
years = list(range(1, 16))
initial_data = pd.DataFrame({
    "Year": years,
    "Value": [0]*15,
    "Type": ["CAPEX"]*15
})

edited_data = st.sidebar.data_editor(
    initial_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Type": st.column_config.SelectboxColumn(
            "Type",
            options=["CAPEX", "OPEX"],
            default="CAPEX"
        )
    }
)

# Main panel
st.subheader("Impact Report")

if st.button("Generate Report"):
    # Convert Value to numeric
    edited_data['Value'] = pd.to_numeric(edited_data['Value'], errors='coerce').fillna(0)

    # Calculate totals
    capex_total = edited_data.loc[edited_data['Type'] == "CAPEX", 'Value'].sum()
    opex_total = edited_data.loc[edited_data['Type'] == "OPEX", 'Value'].sum()

    # Filter database for selected industries
    capex_db = df[df['Industry'] == capex_industry]
    opex_db = df[df['Industry'] == opex_industry]

    # Apply Type and Variable filters
    capex_db = capex_db[(capex_db['Multiplier type'].isin(type_filter)) & (capex_db['Variable'].isin(variable_filter))]
    opex_db = opex_db[(opex_db['Multiplier type'].isin(type_filter)) & (opex_db['Variable'].isin(variable_filter))]

    # Merge CAPEX and OPEX datasets
    report = pd.merge(capex_db, opex_db, on=['Multiplier type', 'Variable'], suffixes=('_CAPEX', '_OPEX'))

    # ------- UPDATED: Divide Jobs by 1,000,000 -------
    def calculate_impact(row, total, value_col):
        if "Jobs" in row['Variable']:
            return row[value_col] * (total / 1_000_000)
        else:
            return row[value_col] * total
    # -------------------------------------------------

    # Apply updated impact calculation
    report['CAPEX_Impact'] = report.apply(lambda r: calculate_impact(r, capex_total, 'VALUE_CAPEX'), axis=1)
    report['OPEX_Impact'] = report.apply(lambda r: calculate_impact(r, opex_total, 'VALUE_OPEX'), axis=1)

    # Formatting
    def format_value(row, col):
        if "Jobs" in row['Variable']:
            return f"{int(row[col]):,}"
        else:
            return f"${int(row[col]):,}"

    report['CAPEX_Impact'] = report.apply(lambda r: format_value(r, 'CAPEX_Impact'), axis=1)
    report['OPEX_Impact'] = report.apply(lambda r: format_value(r, 'OPEX_Impact'), axis=1)

    st.dataframe(report)

    # Download Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        report.to_excel(writer, index=False, sheet_name='Impact Report')
    st.download_button(
        label="Download Excel Report",
        data=output.getvalue(),
        file_name="impact_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
