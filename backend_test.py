import requests
import sys
from datetime import datetime
import json

class StockDashboardAPITester:
    def __init__(self, base_url="https://stock-tracker-in-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:200]}

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response_data and isinstance(response_data, dict):
                    if 'stocks' in response_data:
                        print(f"   📊 Returned {len(response_data['stocks'])} stocks")
                    elif 'symbol' in response_data:
                        print(f"   📈 Stock: {response_data.get('symbol')} - Price: ₹{response_data.get('price', 'N/A')}")
                    elif 'results' in response_data:
                        print(f"   🔍 Search results: {len(response_data['results'])}")
                    elif 'status' in response_data:
                        print(f"   📊 Market status: {response_data.get('status')}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")

            self.test_results.append({
                "test": name,
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_preview": str(response_data)[:100] if response_data else "No data"
            })

            return success, response_data

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "test": name,
                "success": False,
                "error": str(e)
            })
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_nifty50_symbols(self):
        """Test NIFTY50 symbols endpoint"""
        success, response = self.run_test("NIFTY50 Symbols", "GET", "nifty50-symbols", 200)
        if success and 'symbols' in response:
            symbols = response['symbols']
            if len(symbols) == 50:
                print(f"   ✅ Correct number of NIFTY50 symbols: {len(symbols)}")
            else:
                print(f"   ⚠️  Expected 50 symbols, got {len(symbols)}")
        return success

    def test_all_stocks(self):
        """Test get all stocks endpoint"""
        success, response = self.run_test("All Stocks", "GET", "stocks", 200, timeout=45)
        if success and 'stocks' in response:
            stocks = response['stocks']
            if len(stocks) > 0:
                sample_stock = stocks[0]
                required_fields = ['symbol', 'name', 'price', 'change', 'changePercent']
                missing_fields = [field for field in required_fields if field not in sample_stock]
                if not missing_fields:
                    print(f"   ✅ Stock data structure is correct")
                else:
                    print(f"   ⚠️  Missing fields in stock data: {missing_fields}")
        return success

    def test_individual_stock(self, symbol="RELIANCE"):
        """Test individual stock endpoint"""
        success, response = self.run_test(f"Individual Stock ({symbol})", "GET", f"stock/{symbol}", 200)
        if success:
            required_fields = ['symbol', 'name', 'price', 'change', 'changePercent']
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                print(f"   ✅ Individual stock data structure is correct")
            else:
                print(f"   ⚠️  Missing fields: {missing_fields}")
        return success

    def test_stock_history(self, symbol="RELIANCE"):
        """Test stock history endpoint"""
        success, response = self.run_test(f"Stock History ({symbol})", "GET", f"stock/{symbol}/history", 200)
        if success and 'history' in response:
            history = response['history']
            if len(history) > 0:
                print(f"   ✅ History data available: {len(history)} data points")
            else:
                print(f"   ⚠️  No history data returned")
        return success

    def test_search_stocks(self):
        """Test stock search endpoint"""
        # Test search with query
        success1, response1 = self.run_test("Search Stocks (with query)", "GET", "search?q=RELIANCE", 200)
        
        # Test search without query
        success2, response2 = self.run_test("Search Stocks (empty query)", "GET", "search", 200)
        
        if success1 and 'results' in response1:
            if len(response1['results']) > 0:
                print(f"   ✅ Search returned results for 'RELIANCE'")
            else:
                print(f"   ⚠️  No search results for 'RELIANCE'")
        
        return success1 and success2

    def test_market_status(self):
        """Test market status endpoint"""
        success, response = self.run_test("Market Status", "GET", "market-status", 200)
        if success:
            required_fields = ['isOpen', 'status']
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                print(f"   ✅ Market status structure is correct")
                print(f"   📊 Market is {'OPEN' if response.get('isOpen') else 'CLOSED'}")
            else:
                print(f"   ⚠️  Missing fields: {missing_fields}")
        return success

    def test_stocks_batch(self):
        """Test batch stocks endpoint"""
        symbols = "RELIANCE,TCS,HDFCBANK"
        success, response = self.run_test("Batch Stocks", "GET", f"stocks/batch?symbols={symbols}", 200)
        if success and 'stocks' in response:
            stocks = response['stocks']
            if len(stocks) == 3:
                print(f"   ✅ Batch request returned correct number of stocks")
            else:
                print(f"   ⚠️  Expected 3 stocks, got {len(stocks)}")
        return success

    def test_status_endpoints(self):
        """Test status check endpoints"""
        # Test POST status
        test_data = {"client_name": "test_client"}
        success1, response1 = self.run_test("Create Status Check", "POST", "status", 200, data=test_data)
        
        # Test GET status
        success2, response2 = self.run_test("Get Status Checks", "GET", "status", 200)
        
        return success1 and success2

def main():
    print("🚀 Starting Indian Stock Dashboard API Tests")
    print("=" * 60)
    
    tester = StockDashboardAPITester()
    
    # Run all tests
    tests = [
        tester.test_api_root,
        tester.test_nifty50_symbols,
        tester.test_all_stocks,
        tester.test_individual_stock,
        tester.test_stock_history,
        tester.test_search_stocks,
        tester.test_market_status,
        tester.test_stocks_batch,
        tester.test_status_endpoints
    ]
    
    print(f"\n📋 Running {len(tests)} test suites...")
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test suite failed with error: {e}")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed.")
        print("\n📋 Failed Tests Summary:")
        for result in tester.test_results:
            if not result.get('success', False):
                print(f"   ❌ {result['test']}: {result.get('error', 'Status code mismatch')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())