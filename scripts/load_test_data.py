from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to sys.path to import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cosmos_db import CosmosDBManager

def load_vessel_routes():
    """Load vessel routes data into CosmosDB"""
    cosmos_db = CosmosDBManager()
    
    # Base date for generating ETAs
    base_date = datetime.now()
    
    # Vessel routes data
    routes = [
        {
            "id": "route_9839272",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC SOFIA",
            "imo": "9839272",
            "eta": (base_date + timedelta(days=2)).strftime("%Y-%m-%d"),
            "origin": "Montreal",
            "destination": "Rotterdam",
            "route_status": "active",
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "route_9454436",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC VALENTINA",
            "imo": "9454436",
            "eta": (base_date + timedelta(days=3)).strftime("%Y-%m-%d"),
            "origin": "Halifax",
            "destination": "Hamburg",
            "route_status": "active",
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "route_9783615",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC LUCIA",
            "imo": "9783615",
            "eta": (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "origin": "Los Angeles",
            "destination": "Oakland",
            "route_status": "active",
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "route_9776171",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC ISABELLA",
            "imo": "9776171",
            "eta": (base_date + timedelta(days=5)).strftime("%Y-%m-%d"),
            "origin": "New York",
            "destination": "Montreal",
            "route_status": "scheduled",
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "route_9811000",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC CHIARA",
            "imo": "9811000",
            "eta": (base_date + timedelta(days=4)).strftime("%Y-%m-%d"),
            "origin": "Seattle",
            "destination": "Los Angeles",
            "route_status": "active",
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "route_9806079",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC GIULIA",
            "imo": "9806079",
            "eta": (base_date + timedelta(days=6)).strftime("%Y-%m-%d"),
            "origin": "Oakland",
            "destination": "Los Angeles",
            "route_status": "scheduled",
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "route_9812345",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC AURORA",
            "imo": "9812345",
            "eta": (base_date + timedelta(days=7)).strftime("%Y-%m-%d"),
            "origin": "Montreal",
            "destination": "Hamburg",
            "route_status": "scheduled",
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "route_9823456",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC BIANCA",
            "imo": "9823456",
            "eta": (base_date + timedelta(days=8)).strftime("%Y-%m-%d"),
            "origin": "Singapore",
            "destination": "Hong Kong",
            "route_status": "active",
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "route_9834567",
            "partitionKey": "vessel_route",
            "vessel_name": "MSC FRANCESCA",
            "imo": "9834567",
            "eta": (base_date + timedelta(days=9)).strftime("%Y-%m-%d"),
            "origin": "Dubai",
            "destination": "Singapore",
            "route_status": "scheduled",
            "last_updated": datetime.now().isoformat()
        }
    ]
    
    results = []
    for route in routes:
        result = cosmos_db.upsert_item(route)
        results.append(result)
        print(f"Loaded route for {route['vessel_name']} ({route['imo']})")
    
    return results

def main():
    try:
        print("Loading vessel routes...")
        routes_results = load_vessel_routes()
        print(f"\nSuccessfully loaded {len(routes_results)} vessel routes")
        
    except Exception as e:
        print(f"Error loading test data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 