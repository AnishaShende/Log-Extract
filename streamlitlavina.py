import re
import pandas as pd
import streamlit as st
import io
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

st.set_page_config(page_title="Log File Parser Dashboard", layout="wide")
st.title("Log Parser & Dashboard")

# -- File uploader
uploaded_file = st.sidebar.file_uploader("Upload a .log file", type=["log"])

# -- Helper functions
def parse_log(content):
    log_entries = content.split("**********")
    parsed_data = []

    header_pattern = re.compile(
        r"Error Trace::Version (?P<version>.*?)::(?P<datetime>[A-Za-z]{3} [A-Za-z]{3}\s+\d+ \d+:\d+:\d+ \d+)"
        r" \( (?P<time_detail>.*?) pid (?P<pid>\d+)\s+t@(?P<thread>[\-\d]+)(?: session (?P<session>[^ )]+))?"
    )
    message_pattern = re.compile(
        r"#\d+\s+(?P<level>\w+)\s+#(?P<code>\d+)\s+(?P<message>.+)"
    )

    for entry in log_entries:
        header_match = header_pattern.search(entry)
        message_match = message_pattern.search(entry)

        if header_match and message_match:
            data = {
                'Version': header_match.group('version'),
                'DateTime': header_match.group('datetime'),
                'TimeDetails': header_match.group('time_detail'),
                'PID': header_match.group('pid'),
                'Thread': header_match.group('thread'),
                'Session': header_match.group('session') if header_match.group('session') else '',
                'Level': message_match.group('level'),
                'Code': message_match.group('code'),
                'Message': message_match.group('message')
            }
            parsed_data.append(data)

    df = pd.DataFrame(parsed_data)
    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
    return df

# -- Main logic
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    df = parse_log(file_content)

    st.success("Log file parsed successfully!")
    st.dataframe(df, use_container_width=True)

    # -- Sidebar Filters
    st.sidebar.markdown("### Filter Options")
    level_filter = st.sidebar.multiselect("Select Log Level", df['Level'].unique(), default=list(df['Level'].unique()))
    code_filter = st.sidebar.multiselect("Select Error Code", df['Code'].unique(), default=list(df['Code'].unique()))

    df_filtered = df[df['Level'].isin(level_filter) & df['Code'].isin(code_filter)]

    # -- Download Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False)
    st.sidebar.download_button("Download Parsed Data", output.getvalue(), file_name="parsed_log.xlsx")

    # -- Charts Section
    st.subheader("Data Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top Error Codes")
        top_errors = df_filtered['Code'].value_counts().head(10)
        st.bar_chart(top_errors)

    with col2:
        st.markdown("#### Log Levels Distribution")
        level_counts = df_filtered['Level'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(level_counts, labels=level_counts.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)

    st.markdown("#### Logs Over Time")

    # -- Time granularity selection
    granularity = st.selectbox("Select Time Granularity", ["Hourly", "Daily"])

    time_chart = df_filtered.copy()

    if granularity == "Hourly":
        time_chart['TimeGroup'] = time_chart['DateTime'].dt.floor('H')
    else:
        time_chart['TimeGroup'] = time_chart['DateTime'].dt.date

    time_counts = time_chart.groupby('TimeGroup').size().reset_index(name='Log Count')

    fig_time = px.line(
        time_counts,
        x='TimeGroup',
        y='Log Count',
        title=f"Logs Over Time ({granularity})",
        markers=True,
        labels={'TimeGroup': 'Time', 'Log Count': 'Number of Logs'},
        template='plotly_white'
    )

    fig_time.update_traces(line=dict(color='royalblue', width=2), marker=dict(size=6))
    fig_time.update_layout(
        xaxis_title='Time',
        yaxis_title='Log Count',
        hovermode='x unified',
        margin=dict(l=40, r=40, t=40, b=40)
    )

    st.plotly_chart(fig_time, use_container_width=True)


    st.markdown("#### 📘 Frequent Error Messages")
    top_msgs = df_filtered['Message'].value_counts().head(20)
    for msg, count in top_msgs.items():
        st.info(f"{msg} ({count} times)")

else:
    st.info("Upload a log file to begin.")
