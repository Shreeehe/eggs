    #!/usr/bin/env python3
"""
Automated Egg Price Scraper for Raspberry Pi
Scrapes NECC egg prices daily and maintains monthly CSV files
"""

import requests
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('egg_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EggPriceScraper:
    def __init__(self, data_dir="egg_data"):
        self.url = "https://www.e2necc.com/home/eggprice"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def scrape_website(self):
        """Scrape live data from NECC website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table", {"border": "1px"})
            
            if not table:
                raise ValueError("Target table not found on website")
                
            return soup
            
        except Exception as e:
            logger.error(f"Failed to scrape website: {e}")
            raise
    
    def parse_table(self, soup):
        """Parse HTML table into DataFrame"""
        try:
            table = soup.find("table", {"border": "1px"})
            rows = table.find_all("tr")
            
            # Parse table
            data = []
            for row in rows:
                cols = row.find_all(["td", "th"])
                cols = [col.get_text(strip=True) for col in cols]
                if cols:
                    data.append(cols)
            
            if not data:
                raise ValueError("No data found in table")
                
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Clean data - remove header rows
            df = df[df["Name Of Zone / Day"] != "NECC SUGGESTED EGG PRICES"]
            df = df[df["Name Of Zone / Day"] != "Prevailing Prices"]
            df = df[df["Name Of Zone / Day"].notna()]
            
            logger.info(f"Parsed {len(df)} city records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to parse table: {e}")
            raise
    
    def get_clean_cities(self, df):
        """Extract and clean city list"""
        city_column = df["Name Of Zone / Day"]
        city_list = city_column.dropna().tolist()
        
        # Remove non-city headers
        city_list = [city for city in city_list 
                    if "egg price" not in city.lower() 
                    and "price" not in city.lower()
                    and city.strip() != ""]
        
        # Deduplicate and sort
        fixed_city_list = sorted(set(city_list))
        
        logger.info(f"Found {len(fixed_city_list)} unique cities")
        return fixed_city_list
    
    def get_monthly_csv_path(self, date=None):
        """Get path for monthly CSV file"""
        if date is None:
            date = datetime.now()
        
        filename = f"egg_prices_{date.year}_{date.month:02d}.csv"
        return self.data_dir / filename
    
    def update_monthly_csv(self, df, cities):
        """Update or create monthly CSV with today's data"""
        today = datetime.now()
        today_col = str(today.day)
        csv_path = self.get_monthly_csv_path(today)
        
        try:
            # Filter data for clean cities
            city_df = df[df["Name Of Zone / Day"].isin(cities)].copy()
            
            if csv_path.exists():
                # Load existing monthly data
                monthly_df = pd.read_csv(csv_path)
                logger.info(f"Loaded existing monthly file: {csv_path}")
                
                # Update today's column
                if today_col in monthly_df.columns:
                    logger.info(f"Updating existing data for day {today_col}")
                else:
                    logger.info(f"Adding new column for day {today_col}")
                    monthly_df[today_col] = "-"
                
                # Update prices for cities that have data
                for _, row in city_df.iterrows():
                    city_name = row["Name Of Zone / Day"]
                    if today_col in row and row[today_col] != "-":
                        # Find city in monthly_df and update
                        mask = monthly_df["Name Of Zone / Day"] == city_name
                        if mask.any():
                            monthly_df.loc[mask, today_col] = row[today_col]
                        else:
                            # Add new city if not exists
                            new_row = {col: "-" for col in monthly_df.columns}
                            new_row["Name Of Zone / Day"] = city_name
                            new_row[today_col] = row[today_col]
                            monthly_df = pd.concat([monthly_df, pd.DataFrame([new_row])], ignore_index=True)
                
            else:
                # Create new monthly file
                logger.info(f"Creating new monthly file: {csv_path}")
                
                # Create columns for all days of the month
                import calendar
                days_in_month = calendar.monthrange(today.year, today.month)[1]
                columns = ["Name Of Zone / Day"] + [str(i) for i in range(1, days_in_month + 1)] + ["Average"]
                
                # Initialize monthly dataframe
                monthly_data = []
                for city in cities:
                    row = {col: "-" for col in columns}
                    row["Name Of Zone / Day"] = city
                    monthly_data.append(row)
                
                monthly_df = pd.DataFrame(monthly_data)
                
                # Add today's data
                for _, row in city_df.iterrows():
                    city_name = row["Name Of Zone / Day"]
                    if today_col in row and row[today_col] != "-":
                        mask = monthly_df["Name Of Zone / Day"] == city_name
                        if mask.any():
                            monthly_df.loc[mask, today_col] = row[today_col]
            
            # Calculate average (excluding "-" values)
            def calc_average(row):
                prices = []
                for col in [str(i) for i in range(1, 32)]:
                    if col in row and row[col] != "-" and pd.notna(row[col]):
                        try:
                            prices.append(float(row[col]))
                        except:
                            pass
                return round(sum(prices) / len(prices), 2) if prices else "-"
            
            monthly_df["Average"] = monthly_df.apply(calc_average, axis=1)
            
            # Save updated monthly file
            monthly_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            logger.info(f"Successfully updated monthly CSV: {csv_path}")
            
            return csv_path
            
        except Exception as e:
            logger.error(f"Failed to update monthly CSV: {e}")
            raise
    
    def run_daily_scrape(self):
        """Main function to run daily scraping"""
        try:
            logger.info("Starting daily egg price scraping...")
            
            # Scrape website
            soup = self.scrape_website()
            
            # Parse table
            df = self.parse_table(soup)
            
            # Get clean cities
            cities = self.get_clean_cities(df)
            
            # Update monthly CSV
            csv_path = self.update_monthly_csv(df, cities)
            
            # Save today's simple format too (for backup)
            today = datetime.now()
            today_col = str(today.day)
            
            city_df = df[df["Name Of Zone / Day"].isin(cities)].copy()
            if today_col in df.columns:
                result = city_df[["Name Of Zone / Day", today_col]].copy()
                result.columns = ["City", "Rate"]
                
                daily_path = self.data_dir / f"daily_prices_{today.strftime('%Y%m%d')}.csv"
                result.to_csv(daily_path, index=False, encoding="utf-8-sig")
                logger.info(f"Saved daily backup: {daily_path}")
            
            logger.info("Daily scraping completed successfully!")
            return csv_path
            
        except Exception as e:
            logger.error(f"Daily scraping failed: {e}")
            raise

def main():
    """Main entry point"""
    scraper = EggPriceScraper()
    
    try:
        csv_path = scraper.run_daily_scrape()
        print(f"✅ Successfully updated: {csv_path}")
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())