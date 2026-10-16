from datetime import datetime, timedelta
import json
import pandas as pd
import streamlit as st

from DataTypes import liftosaur

dateformat = '%d-%m-%Y'

class WeightManager:
    def __init__(self, df: pd.DataFrame):
        self.df = df.sort_values('datetime').reset_index(drop=True)

    @classmethod
    def from_liftosaur(cls, file_obj):
        jsondata = json.load(file_obj)
        data = liftosaur.LiftosaurStats.from_json(jsondata)

        rows = []
        for item in data.weight_history:
            if item.date and item.weight is not None:
                dt = datetime.strptime(item.date, dateformat)
                rows.append({"datetime": dt, "date_str": item.date, "weight": item.weight})

        df = pd.DataFrame(rows)
        return cls(df)

    def calculate_trend(self):
        if self.df.empty:
            self.df['trend'] = []
            return
            
        self.df['trend'] = self.df['weight'].ewm(alpha=0.1, adjust=False).mean()


st.set_page_config(page_title="Weight Trend Tracker", page_icon="📈", layout="centered")

st.title("📈 Weight & Smoothing Trend Tracker")
st.write(
    "Upload your weight export file to track smoothed trends and 7-day window comparisons.\n"
    "Supported file providers: Liftosaur"
)

uploaded_file = st.file_uploader("Upload your file", type=["json"])

if uploaded_file is not None:
    try:
        manager = WeightManager.from_liftosaur(uploaded_file)

        if not manager.df.empty:
            manager.calculate_trend()

            timeframe = st.selectbox(
                "Select Timeframe:",
                ["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "All Time"],
                index=1
            )

            latest_date = manager.df['datetime'].max().date()

            if timeframe == "Last 7 Days":
                cutoff_date = latest_date - timedelta(days=7)
            elif timeframe == "Last 30 Days":
                cutoff_date = latest_date - timedelta(days=30)
            elif timeframe == "Last 3 Months":
                cutoff_date = latest_date - timedelta(days=90)
            elif timeframe == "Last 6 Months":
                cutoff_date = latest_date - timedelta(days=180)
            else:
                cutoff_date = None

            if cutoff_date:
                manager.df = manager.df[manager.df['datetime'].dt.date >= cutoff_date]

        df = manager.df.copy()

        # 1. Main Clean Log
        st.subheader("📊 Weight & Trend Log")
        display_df = df[['date_str', 'weight', 'trend']].rename(
            columns={'date_str': 'Date', 'weight': 'Weight', 'trend': 'Smoothed Trend'}
        ).copy()
        
        display_df['Weight'] = display_df['Weight'].round(2)
        display_df['Smoothed Trend'] = display_df['Smoothed Trend'].round(2)
        display_df = display_df.iloc[::-1]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Date": st.column_config.TextColumn("Date"),
                "Weight": st.column_config.NumberColumn("Weight", format="%.2f kg"),
                "Smoothed Trend": st.column_config.NumberColumn("Smoothed Trend", format="%.2f kg"),
            }
        )

        # 2. Dedicated 7-Day Window Comparison Area
        st.subheader("📅 7-Day Window Comparisons")
        if not df.empty:
            min_dt = df['datetime'].min()
            df['block_id'] = (df['datetime'] - min_dt).dt.days // 7
            
            window_df = df.groupby('block_id').agg(
                start_date=('datetime', 'min'),
                end_date=('datetime', 'max'),
                avg_trend=('trend', 'mean')
            ).reset_index()
            
            window_df['Change'] = window_df['avg_trend'].diff()
            
            window_display = window_df.copy()
            window_display['Period'] = window_display['start_date'].dt.strftime('%d-%m-%Y') + " to " + window_display['end_date'].dt.strftime('%d-%m-%Y')
            window_display = window_display[['Period', 'avg_trend', 'Change']].rename(
                columns={'avg_trend': 'Avg Trend'}
            )
            
            window_display['Avg Trend'] = window_display['Avg Trend'].round(2)
            window_display['Change'] = window_display['Change'].round(2)
            window_display = window_display.iloc[::-1]

            st.dataframe(
                window_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Period": st.column_config.TextColumn("7-Day Window"),
                    "Avg Trend": st.column_config.NumberColumn("Avg Trend", format="%.2f kg"),
                    "Change": st.column_config.NumberColumn("Window Change", format="%.2f kg"),
                }
            )

    except Exception as e:
        st.error(f"Error processing file: {e}")