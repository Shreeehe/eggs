import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import glob
import logging

# Page config
st.set_page_config(
    page_title="Egg Price Dashboard",
    page_icon="🥚",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EggPriceDashboard:
    def __init__(self, data_dir="egg_data"):
        self.data_dir = Path(data_dir)
        
    def get_all_monthly_files(self):
        """Get a list of all available monthly CSV files"""
        try:
            csv_files = sorted(self.data_dir.glob("egg_prices_*.csv"), reverse=True)
            return csv_files
        except Exception as e:
            st.error(f"Error finding data files: {e}")
            return []

    def load_monthly_data(self, file_path):
        """Load and process monthly data"""
        try:
            df = pd.read_csv(file_path)
            
            # Get file info
            filename = file_path.name
            year_month = filename.replace("egg_prices_", "").replace(".csv", "")
            year, month = year_month.split("_")
            
            return df, int(year), int(month)
            
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None, None, None
    
    # ... (the rest of your class methods remain the same) ...
    def get_current_prices(self, df, day):
        """Get a specific day's prices"""
        day_col = str(day)
        
        if day_col not in df.columns:
            return None
            
        current_data = df[["Name Of Zone / Day", day_col]].copy()
        current_data.columns = ["City", "Price"]
        
        current_data = current_data[current_data["Price"] != "-"]
        current_data = current_data[current_data["Price"].notna()]
        
        current_data["Price"] = pd.to_numeric(current_data["Price"], errors="coerce")
        current_data = current_data.dropna()
        
        return current_data.sort_values("Price", ascending=False)
    
    # ... (the rest of your class methods remain the same) ...

def main():
    """Main Streamlit app"""
    
    # Title and header
    st.title("Egg Price Dashboard 🥚")
    st.markdown("Real-time egg price monitoring across India")
    
    # Initialize dashboard
    dashboard = EggPriceDashboard()
    
    # Get all available files
    available_files = dashboard.get_all_monthly_files()
    if not available_files:
        st.error("No data files found. Please run the scraper first.")
        st.code("python egg_price_automation.py")
        return
        
    # Create month selector dropdown
    file_options = {file.stem.replace("egg_prices_", ""): file for file in available_files}
    selected_month = st.selectbox("Select Month", options=list(file_options.keys()), format_func=lambda x: datetime.strptime(x, "%Y_%m").strftime("%B %Y"))
    
    if not selected_month:
        st.warning("Please select a month to view data.")
        return
    
    # Load data for the selected month
    df, year, month = dashboard.load_monthly_data(file_options[selected_month])
    
    if df is None:
        st.error("Failed to load data for the selected month.")
        return
    
    # Display current month info
    st.info(f"📅 Showing data for: **{datetime(year, month, 1).strftime('%B %Y')}**")
    
    # Get a list of available days for the selected month
    available_days = [col for col in df.columns if col.isdigit()]
    
    # Create day selector
    if available_days:
        max_day = max([int(d) for d in available_days])
        selected_day = st.slider("Select Day", 1, max_day, max_day)
    else:
        st.info("No daily data available for this month.")
        selected_day = None
    
    # Auto-refresh
    if st.button("🔄 Refresh Data"):
        st.rerun()

    # Get current prices for the selected day
    current_data = dashboard.get_current_prices(df, selected_day)
    
    # Display statistics
    st.subheader("📊 Daily Market Summary")
    dashboard.display_statistics(current_data)
    
    st.divider()
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Price comparison chart
        st.subheader("🗺️ Prices by City")
        
        if current_data is not None and not current_data.empty:
            price_chart = dashboard.create_price_map(current_data)
            if price_chart:
                st.plotly_chart(price_chart, use_container_width=True)
        else:
            st.warning("No price data available for the selected day")
    
    with col2:
        # City selector for trends
        st.subheader("📈 Price Trends")
        
        if current_data is not None and not current_data.empty:
            cities = sorted(current_data["City"].tolist())
            selected_city = st.selectbox("Select City", cities)
            
            if selected_city:
                trend_data = dashboard.get_price_trends(df, selected_city)
                
                if trend_data is not None:
                    trend_chart = dashboard.create_trend_chart(trend_data, selected_city)
                    if trend_chart:
                        st.plotly_chart(trend_chart, use_container_width=True)
                    
                    # Show trend stats
                    if len(trend_data) > 1:
                        latest_price = trend_data["Price"].iloc[-1]
                        prev_price = trend_data["Price"].iloc[-2]
                        change = latest_price - prev_price
                        change_pct = (change / prev_price) * 100
                        
                        if change > 0:
                            st.success(f"📈 +₹{change:.0f} (+{change_pct:.1f}%)")
                        elif change < 0:
                            st.error(f"📉 ₹{change:.0f} ({change_pct:.1f}%)")
                        else:
                            st.info("➡️ No change")
                else:
                    st.info(f"No trend data available for {selected_city}")
        else:
            st.info("No cities available for trend analysis")
    
    st.divider()
    
    # Raw data table
    with st.expander("📋 View Raw Data"):
        st.dataframe(df, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "📍 Data source: [NECC](https://www.e2necc.com/home/eggprice) | "
        f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

if __name__ == "__main__":
    main()
