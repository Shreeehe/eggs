import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
    
    def get_price_trends(self, df, city):
        """Get price trend for a specific city"""
        try:
            city_row = df[df["Name Of Zone / Day"] == city]
            if city_row.empty:
                return None
                
            city_data = city_row.iloc[0]
            
            # Extract daily prices
            prices = []
            dates = []
            
            for day in range(1, 32):
                day_col = str(day)
                if day_col in city_data and city_data[day_col] != "-":
                    try:
                        price = float(city_data[day_col])
                        prices.append(price)
                        # Create date (assuming current month/year for now)
                        date = datetime.now().replace(day=day)
                        dates.append(date)
                    except:
                        pass
            
            if not prices:
                return None
                
            trend_df = pd.DataFrame({
                "Date": dates,
                "Price": prices
            })
            
            return trend_df
            
        except Exception as e:
            st.error(f"Error getting trends for {city}: {e}")
            return None
    
    def create_price_map(self, current_data):
        """Create a price comparison chart (placeholder for map)"""
        if current_data is None or current_data.empty:
            return None
            
        fig = px.bar(
            current_data.head(20),  # Top 20 cities
            x="Price",
            y="City",
            orientation="h",
            title="Current Egg Prices by City (₹ per 100 eggs)",
            color="Price",
            color_continuous_scale="RdYlGn_r"
        )
        
        fig.update_layout(
            height=600,
            yaxis={"categoryorder": "total ascending"}
        )
        
        return fig
    
    def create_trend_chart(self, trend_data, city):
        """Create price trend chart for a city"""
        if trend_data is None or trend_data.empty:
            return None
            
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_data["Date"],
            y=trend_data["Price"],
            mode="lines+markers",
            name=f"{city} Price Trend",
            line=dict(width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title=f"Egg Price Trend - {city}",
            xaxis_title="Date",
            yaxis_title="Price (₹ per 100 eggs)",
            hovermode="x unified"
        )
        
        return fig
    
    def display_statistics(self, current_data):
        """Display key statistics"""
        if current_data is None or current_data.empty:
            st.warning("No current price data available")
            return
            
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_price = current_data["Price"].mean()
            st.metric("Average Price", f"₹{avg_price:.0f}")
        
        with col2:
            max_price = current_data["Price"].max()
            if not pd.isna(max_price):
                max_city = current_data[current_data["Price"] == max_price]["City"].iloc[0]
                st.metric("Highest Price", f"₹{max_price:.0f}", f"{max_city}")
        
        with col3:
            min_price = current_data["Price"].min()
            if not pd.isna(min_price):
                min_city = current_data[current_data["Price"] == min_price]["City"].iloc[0]
                st.metric("Lowest Price", f"₹{min_price:.0f}", f"{min_city}")
        
        with col4:
            price_range = current_data["Price"].max() - current_data["Price"].min()
            if not pd.isna(price_range):
                st.metric("Price Range", f"₹{price_range:.0f}")

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
