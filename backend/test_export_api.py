
import requests
import datetime
import os

# Backend URL (Assuming localhost:8000)
BASE_URL = "http://localhost:8000/api/v1/stats/export"

def test_export_range():
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=7)
    end_date = today
    
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    print(f"Testing export range: {params}")
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            print("✅ Range Export Success (200 OK)")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response.headers.get('Content-Type', ''):
                 print("✅ Valid Excel Content-Type")
            else:
                 print("⚠️ Unexpected Content-Type")
        else:
            print(f"❌ Range Export Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

def test_export_all():
    print("Testing export all (no params)")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
             print("✅ All Export Success (200 OK)")
        else:
             print(f"❌ All Export Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_export_range()
    test_export_all()
