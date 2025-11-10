import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import httpx
import sys

# Sample data
FIRST_NAMES = ["John", "Sarah", "Michael", "Emily", "David", "Lisa", "James", "Jennifer", "Robert", "Mary",
               "William", "Patricia", "Richard", "Linda", "Joseph", "Barbara", "Thomas", "Elizabeth", "Charles", "Susan"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

US_CITIES = [
    ("New York", "US", 40.7128, -74.0060),
    ("Los Angeles", "US", 34.0522, -118.2437),
    ("Chicago", "US", 41.8781, -87.6298),
    ("Houston", "US", 29.7604, -95.3698),
    ("Boston", "US", 42.3601, -71.0589),
    ("San Francisco", "US", 37.7749, -122.4194),
    ("Seattle", "US", 47.6062, -122.3321),
    ("Miami", "US", 25.7617, -80.1918),
]

INTERNATIONAL_CITIES = [
    ("Hong Kong", "CN", 22.3193, 114.1694),
    ("London", "GB", 51.5074, -0.1278),
    ("Tokyo", "JP", 35.6762, 139.6503),
    ("Singapore", "SG", 1.3521, 103.8198),
    ("Dubai", "AE", 25.2048, 55.2708),
    ("Sydney", "AU", -33.8688, 151.2093),
]

NORMAL_MERCHANTS = [
    ("Whole Foods Market", "Grocery"),
    ("Starbucks", "Dining"),
    ("Shell Gas Station", "Gas"),
    ("Target", "Retail"),
    ("Walgreens Pharmacy", "Healthcare"),
    ("AT&T Wireless", "Utilities"),
    ("Electric Company", "Utilities"),
    ("Olive Garden", "Dining"),
    ("McDonald's", "Dining"),
    ("CVS Pharmacy", "Healthcare"),
]

HIGH_VALUE_MERCHANTS = [
    ("Best Buy Electronics", "Electronics"),
    ("Apple Store", "Electronics"),
    ("Tiffany & Co", "Jewelry"),
    ("Rolex Boutique", "Jewelry"),
    ("Delta Airlines", "Travel"),
    ("Marriott Hotels", "Travel"),
]

SUSPICIOUS_MERCHANTS = [
    ("Electronics Warehouse Ltd", "Electronics"),
    ("Crypto Exchange Global", "Cryptocurrency"),
    ("Bitcoin Trading Platform", "Cryptocurrency"),
    ("Wire Transfer Service", "Financial"),
]

TRANSACTION_TYPES = ["CARD", "WIRE", "ATM", "ACH"]


class DataGenerator:
    def __init__(self, api_url: str = "http://localhost:8000/api/v1"):
        self.api_url = api_url
        self.client = httpx.Client(timeout=30.0)
        self.transaction_counter = 1
        
    def generate_account_number(self, account_id: int) -> str:
        """Generate masked account number"""
        return f"**** {4500 + account_id:04d}"
    
    def generate_transaction_id(self) -> str:
        """Generate transaction ID"""
        txn_id = f"TXN-{8000 + self.transaction_counter}"
        self.transaction_counter += 1
        return txn_id
    
    def create_account_holder(self, account_id: int) -> tuple:
        """Create account holder name and home location"""
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        home_city = random.choice(US_CITIES)
        return name, home_city
    
    def build_transaction_data(
        self,
        account_number: str,
        account_holder: str,
        amount: Decimal,
        merchant_name: str,
        category: str,
        txn_type: str,
        city: str,
        country: str,
        lat: float,
        lng: float,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Build transaction data dict for API POST"""
        return {
            "account_number": account_number,
            "account_holder_name": account_holder,
            "amount": str(amount),
            "merchant_name": merchant_name,
            "merchant_category": category,
            "transaction_type": txn_type,
            "location_city": city,
            "location_country": country,
            "latitude": lat,
            "longitude": lng,
            "timestamp": timestamp.isoformat()
        }
    
    def create_transaction_via_api(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Post transaction to API endpoint"""
        try:
            response = self.client.post(
                f"{self.api_url}/transactions",
                json=transaction_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            print(f"\n❌ ERROR: Cannot connect to API at {self.api_url}")
            print(f"Make sure the backend is running:")
            print(f"  cd backend")
            print(f"  uvicorn app.main:app --reload")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            print(f"\n❌ ERROR: API returned error {e.response.status_code}")
            print(f"Response: {e.response.text}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ ERROR: Failed to create transaction: {e}")
            sys.exit(1)
    
    def generate_normal_transaction(
        self,
        account_number: str,
        account_holder: str,
        home_city: tuple,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Generate a normal transaction"""
        merchant_name, category = random.choice(NORMAL_MERCHANTS)
        amount = Decimal(str(round(random.uniform(5, 500), 2)))
        
        # Add some randomness to location (same city or nearby)
        city, country, lat, lng = home_city
        
        return self.build_transaction_data(
            account_number=account_number,
            account_holder=account_holder,
            amount=amount,
            merchant_name=merchant_name,
            category=category,
            txn_type=random.choice(["CARD", "ACH"]),
            city=city,
            country=country,
            lat=lat + random.uniform(-0.1, 0.1),
            lng=lng + random.uniform(-0.1, 0.1),
            timestamp=timestamp
        )
    
    def generate_medium_risk_transaction(
        self,
        account_number: str,
        account_holder: str,
        home_city: tuple,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Generate a medium risk transaction"""
        merchant_name, category = random.choice(HIGH_VALUE_MERCHANTS)
        amount = Decimal(str(round(random.uniform(500, 2000), 2)))
        
        # Might be international
        if random.random() < 0.3:
            city, country, lat, lng = random.choice(INTERNATIONAL_CITIES)
        else:
            city, country, lat, lng = home_city
        
        return self.build_transaction_data(
            account_number=account_number,
            account_holder=account_holder,
            amount=amount,
            merchant_name=merchant_name,
            category=category,
            txn_type=random.choice(TRANSACTION_TYPES),
            city=city,
            country=country,
            lat=lat,
            lng=lng,
            timestamp=timestamp
        )
    
    def generate_suspicious_transaction(
        self,
        account_number: str,
        account_holder: str,
        home_city: tuple,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Generate a suspicious transaction (might trigger fraud rules, but we don't know)"""
        scenario = random.choice([
            "international_night",
            "high_amount",
            "velocity",
            "crypto"
        ])
        
        if scenario == "international_night":
            # International transaction at odd hours
            merchant_name, category = random.choice(SUSPICIOUS_MERCHANTS)
            amount = Decimal(str(round(random.uniform(5000, 15000), 2)))
            city, country, lat, lng = random.choice(INTERNATIONAL_CITIES)
            # Set time to 2-4 AM
            timestamp = timestamp.replace(hour=random.randint(2, 4), minute=random.randint(0, 59))
            txn_type = "WIRE"
            
        elif scenario == "high_amount":
            merchant_name = random.choice(["Wire Transfer", "Cash Withdrawal", "Bitcoin Exchange"])
            category = "Financial"
            amount = Decimal(str(round(random.uniform(12000, 25000), 2)))
            city, country, lat, lng = home_city
            txn_type = "WIRE"
            
        elif scenario == "velocity":
            # Part of velocity attack (will be generated in bulk)
            merchant_name = random.choice(["Online Store", "Gift Card Purchase", "Gaming Platform"])
            category = "Retail"
            amount = Decimal(str(round(random.uniform(100, 500), 2)))
            city, country, lat, lng = home_city
            txn_type = "CARD"
            
        else:  # crypto
            merchant_name = random.choice(["Crypto Exchange Global", "Bitcoin ATM", "Coinbase Pro"])
            category = "Cryptocurrency"
            amount = Decimal(str(round(random.uniform(8000, 20000), 2)))
            city, country, lat, lng = random.choice(INTERNATIONAL_CITIES)
            txn_type = "WIRE"
        
        return self.build_transaction_data(
            account_number=account_number,
            account_holder=account_holder,
            amount=amount,
            merchant_name=merchant_name,
            category=category,
            txn_type=txn_type,
            city=city,
            country=country,
            lat=lat,
            lng=lng,
            timestamp=timestamp
        )
    
    def seed_database(self, total_transactions: int = 1000):
        """Seed the database with transaction data via API"""
        print(f"\n🌱 Starting to seed {total_transactions} transactions via API...")
        print(f"API endpoint: {self.api_url}/transactions\n")
        
        # Create 50 accounts
        num_accounts = 50
        accounts = []
        
        for i in range(num_accounts):
            account_number = self.generate_account_number(i)
            account_holder, home_city = self.create_account_holder(i)
            accounts.append({
                "number": account_number,
                "holder": account_holder,
                "home_city": home_city
            })
        
        # Generate transactions over last 30 days
        now = datetime.now()
        
        transactions_per_account = total_transactions // num_accounts
        
        created_count = 0
        
        for idx, account in enumerate(accounts):
            print(f"  Seeding account {idx+1}/{num_accounts} ({account['number']})...", end="\r")
            
            # Determine if this account should have suspicious activity
            is_suspicious_account = random.random() < 0.2  # 20% of accounts
            
            for i in range(transactions_per_account):
                # Random timestamp in the last 30 days
                days_ago = random.uniform(0, 30)
                timestamp = now - timedelta(days=days_ago)
                timestamp = timestamp.replace(
                    hour=random.randint(6, 23),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                
                # Decide transaction type - just generating random data
                # We don't know what will be flagged as fraud
                rand = random.random()
                
                if is_suspicious_account and rand < 0.15:
                    # Generate potentially suspicious patterns
                    transaction_data = self.generate_suspicious_transaction(
                        account["number"],
                        account["holder"],
                        account["home_city"],
                        timestamp
                    )
                elif rand < 0.30:
                    # Generate higher value transactions
                    transaction_data = self.generate_medium_risk_transaction(
                        account["number"],
                        account["holder"],
                        account["home_city"],
                        timestamp
                    )
                else:
                    # Generate normal everyday transactions
                    transaction_data = self.generate_normal_transaction(
                        account["number"],
                        account["holder"],
                        account["home_city"],
                        timestamp
                    )
                
                # Send to API - let it handle fraud detection
                self.create_transaction_via_api(transaction_data)
                created_count += 1
        
        print()  # New line after progress
        
        # Generate velocity attack pattern for one random account
        velocity_account = random.choice(accounts)
        velocity_time = now - timedelta(hours=2)
        
        print("\n🚀 Creating velocity attack scenario (8 rapid transactions)...")
        for i in range(8):
            timestamp = velocity_time + timedelta(minutes=i * 5)
            city, country, lat, lng = velocity_account["home_city"]
            
            transaction_data = self.build_transaction_data(
                account_number=velocity_account["number"],
                account_holder=velocity_account["holder"],
                amount=Decimal("299.99"),
                merchant_name="Online Gaming Store",
                category="Entertainment",
                txn_type="CARD",
                city=city,
                country=country,
                lat=lat,
                lng=lng,
                timestamp=timestamp
            )
            
            # Send to API
            self.create_transaction_via_api(transaction_data)
            created_count += 1
        
        # Close API client
        self.client.close()
        
        print(f"\n✅ Seeding complete!")
        print(f"📊 Total transactions created: {created_count}")
        print(f"👥 Accounts: {num_accounts}")
        print(f"\nℹ️  The API has analyzed all transactions and applied fraud detection rules.")
        print(f"   Check the frontend to see which ones were flagged!")


def seed_database_from_cli():
    """Entry point for seeding from command line"""
    generator = DataGenerator()
    generator.seed_database(1000)


if __name__ == "__main__":
    seed_database_from_cli()
