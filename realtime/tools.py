import json
import random
import chainlit as cl
from datetime import datetime, timedelta

# Function Definitions
get_product_info_def = {
    "name": "get_product_info",
    "description": "Retrieve information about a specific product",
    "parameters": {
      "type": "object",
      "properties": {
        "customer_id": {
          "type": "string",
          "description": "The unique identifier for the customer"
        },
        "product_id": {
          "type": "string",
          "description": "The unique identifier for the product"
        }
      },
      "required": ["customer_id", "product_id"]
    }
}

update_account_info_def = {
    "name": "update_account_info",
    "description": "Update a customer's account information",
    "parameters": {
      "type": "object",
      "properties": {
        "customer_id": {
          "type": "string",
          "description": "The unique identifier for the customer"
        },
        "field": {
          "type": "string",
          "description": "The account field to be updated (e.g., 'email', 'phone', 'address')"
        },
        "value": {
          "type": "string",
          "description": "The new value for the specified field"
        }
      },
      "required": ["customer_id", "field", "value"]
    }
}


  
cancel_order_def = {  
    "name": "cancel_order",  
    "description": "Cancel a customer's order before it is processed",  
    "parameters": {  
        "type": "object",  
        "properties": {  
            "customer_id": {
                "type": "string",
                "description": "The unique identifier for the customer"
            },
            "order_id": {  
                "type": "string",  
                "description": "The unique identifier of the order to be cancelled"  
            },  
            "reason": {  
                "type": "string",  
                "description": "The reason for cancelling the order"  
            }  
        },  
        "required": ["customer_id", "order_id", "reason"]  
    }  
}  

schedule_callback_def = {  
    "name": "schedule_callback",  
    "description": "Schedule a callback with a customer service representative",  
    "parameters": {  
        "type": "object",  
        "properties": {  
            "customer_id": {
                "type": "string",
                "description": "The unique identifier for the customer"
            },
            "callback_time": {  
                "type": "string",  
                "description": "Preferred time for the callback in a human readable format"  
            }  
        },  
        "required": ["customer_id", "callback_time"]  
    }  
}  

get_customer_info_def = {  
    "name": "get_customer_info",  
    "description": "Retrieve information about a specific customer",  
    "parameters": {  
        "type": "object",  
        "properties": {  
            "customer_id": {  
                "type": "string",  
                "description": "The unique identifier for the customer"  
            }  
        },  
        "required": ["customer_id"]  
    }  
}  

get_bill_of_lading_def = {
    "name": "get_bill_of_lading",
    "description": "Retrieve Bill of Lading (B/L) information for a shipment",
    "parameters": {
        "type": "object",
        "properties": {
            "bl_number": {
                "type": "string",
                "description": "The Bill of Lading number (e.g., MSCUBL123456789)"
            },
            "booking_reference": {
                "type": "string",
                "description": "The booking reference number"
            }
        },
        "required": ["bl_number", "booking_reference"]
    }
}

get_shipping_quote_def = {
    "name": "get_shipping_quote",
    "description": "Get a quote for shipping containers between locations",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Origin location (e.g., Rotterdam, Shanghai, New York, London)"
            },
            "destination": {
                "type": "string",
                "description": "Destination location"
            },
            "container_count": {
                "type": "integer",
                "description": "Number of containers to ship"
            },
            "container_type": {
                "type": "string",
                "description": "Type of container (e.g., 20GP, 40GP, 40HC)",
                "default": "40HC"
            }
        },
        "required": ["origin", "destination", "container_count"]
    }
}

get_shipping_guidelines_def = {
    "name": "get_shipping_guidelines",
    "description": "Get shipping guidelines, regulations, and requirements for a location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get shipping guidelines for (e.g., New York, Shanghai, Rotterdam)"
            },
            "guideline_type": {
                "type": "string",
                "description": "Type of guidelines to retrieve (e.g., import, export, general)",
                "enum": ["import", "export", "general"],
                "default": "general"
            }
        },
        "required": ["location"]
    }
}

async def cancel_order_handler(customer_id, order_id, reason):  
    status = "Cancelled"
    
    # Generate random cancellation details
    cancellation_date = datetime.now()
    refund_amount = round(random.uniform(10, 500), 2)
    
    # Read the HTML template
    with open('order_cancellation_template.html', 'r') as file:
        html_content = file.read()
    
    # Replace placeholders with actual data
    html_content = html_content.format(
        order_id=order_id,
        customer_id=customer_id,
        cancellation_date=cancellation_date.strftime("%B %d, %Y"),
        refund_amount=refund_amount,
        status=status
    )
    
    # Return the Chainlit message with HTML content
    await cl.Message(content=f"Your order has been cancelled. Here are the details:\n{html_content}").send()
    return f"Order {order_id} for customer {customer_id} has been cancelled. Reason: {reason}. A confirmation email has been sent."  
  
async def schedule_callback_handler(customer_id, callback_time):
    # Create a formatted message using markdown
    message_content = f"""
## Callback Schedule Details
- **Customer ID**: {customer_id}
- **Callback Time**: {callback_time}

A customer service representative will contact you at the scheduled time."""

    # Send the formatted message
    await cl.Message(content=message_content).send()
    return f"Callback scheduled for customer {customer_id} at {callback_time}. A representative will contact you then."
  
async def get_product_info_handler(customer_id, product_id):
    products = {
        "P001": {"name": "Wireless Earbuds", "price": 79.99, "stock": 50},
        "P002": {"name": "Smart Watch", "price": 199.99, "stock": 30},
        "P003": {"name": "Laptop Backpack", "price": 49.99, "stock": 100}
    }
    product_info = products.get(product_id, "Product not found")
    return f"Product information for customer {customer_id}: {json.dumps(product_info)}"

async def update_account_info_handler(customer_id, field, value):
    return f"Account information updated for customer {customer_id}. {field.capitalize()} changed to: {value}"

async def get_customer_info_handler(customer_id):  
    # Simulated customer data (using placeholder information)  
    customers = {  
        "C001": {"membership_level": "Gold", "account_status": "Active"},  
        "C002": {"membership_level": "Silver", "account_status": "Pending"},  
        "C003": {"membership_level": "Bronze", "account_status": "Inactive"},  
    }  
    customer_info = customers.get(customer_id)  
    if customer_info:  
        # Return customer information in JSON format  
        return json.dumps({  
            "customer_id": customer_id,  
            "membership_level": customer_info["membership_level"],  
            "account_status": customer_info["account_status"]  
        })  
    else:  
        return f"Customer with ID {customer_id} not found."  

async def get_bill_of_lading_handler(bl_number, booking_reference):
    # Simulate B/L data
    shipper = "ABC Trading Co., Ltd."
    consignee = "XYZ Imports Inc."
    notify_party = "XYZ Imports Inc."
    vessel = "MSC ISABELLA"
    voyage = "AE2-FE1-123"
    port_of_loading = "Shanghai, China"
    port_of_discharge = "Rotterdam, Netherlands"
    containers = [
        {"number": "MSCU1234567", "type": "40HC", "seal_number": "SL123456", "weight": "12500 KG"},
        {"number": "MSCU7654321", "type": "40HC", "seal_number": "SL654321", "weight": "13200 KG"}
    ]
    
    # Create a formatted message using markdown
    message_content = f"""
## Bill of Lading Details
- **B/L Number**: {bl_number}
- **Booking Reference**: {booking_reference}
- **Shipper**: {shipper}
- **Consignee**: {consignee}
- **Notify Party**: {notify_party}

### Voyage Information
- **Vessel**: {vessel}
- **Voyage Number**: {voyage}
- **Port of Loading**: {port_of_loading}
- **Port of Discharge**: {port_of_discharge}

### Container Details
"""
    
    # Add container information
    for container in containers:
        message_content += f"""
- Container {container['number']}:
  - Type: {container['type']}
  - Seal Number: {container['seal_number']}
  - Weight: {container['weight']}
"""

    # Send the formatted message
    await cl.Message(content=message_content).send()
    return f"Bill of Lading {bl_number} details retrieved successfully."

async def get_shipping_quote_handler(origin, destination, container_count, container_type="40HC"):
    # Simulate quote calculation
    # Base rate per container (varies by route)
    route_base_rates = {
        ("Rotterdam", "New York"): 2500,
        ("Shanghai", "Rotterdam"): 3000,
        ("Singapore", "Los Angeles"): 3500,
        ("London", "Dubai"): 2800,
        ("Hamburg", "Singapore"): 3200,
        ("Dubai", "Mumbai"): 1800,
        ("Tokyo", "Los Angeles"): 3300,
        ("New York", "London"): 2400
    }
    
    # Get base rate for the route or use average if route not found
    base_rate = route_base_rates.get(
        (origin, destination), 
        sum(route_base_rates.values()) / len(route_base_rates)
    )
    
    # Container type multipliers
    type_multipliers = {
        "20GP": 0.8,
        "40GP": 1.0,
        "40HC": 1.2
    }
    
    # Calculate total cost
    container_multiplier = type_multipliers.get(container_type, 1.0)
    base_cost = base_rate * container_multiplier
    total_cost = base_cost * container_count
    
    # Add random transit time between 15-45 days
    transit_time = random.randint(15, 45)
    
    # Calculate estimated dates
    departure_date = datetime.now() + timedelta(days=random.randint(3, 10))
    arrival_date = departure_date + timedelta(days=transit_time)
    
    # Create a formatted message using markdown
    message_content = f"""
## Shipping Quote Details
- **Route**: {origin} → {destination}
- **Containers**: {container_count}x {container_type}
- **Rate per Container**: USD {base_cost:,.2f}
- **Total Cost**: USD {total_cost:,.2f}

### Schedule
- **Estimated Departure**: {departure_date.strftime("%B %d, %Y")}
- **Estimated Arrival**: {arrival_date.strftime("%B %d, %Y")}
- **Transit Time**: {transit_time} days

### Additional Information
- Rate includes:
  - Ocean freight
  - Standard documentation
  - Terminal handling at origin and destination
- Excludes:
  - Local charges and fees
  - Customs clearance
  - Inland transportation
  - Insurance
- Quote valid for 7 days
- Subject to equipment and space availability

*For a detailed quote including all charges and to proceed with booking, please contact your MSC representative.*
"""

    # Send the formatted message
    await cl.Message(content=message_content).send()
    return f"Quote generated for {container_count}x {container_type} containers from {origin} to {destination}"

async def get_shipping_guidelines_handler(location, guideline_type="general"):
    # Simulate guidelines database
    guidelines_db = {
        "New York": {
            "general": {
                "port_authority": "Port Authority of New York and New Jersey",
                "operating_hours": "24/7",
                "documentation": [
                    "Bill of Lading",
                    "Commercial Invoice",
                    "Packing List",
                    "ISF (10+2) Filing"
                ],
                "key_regulations": [
                    "Customs and Border Protection (CBP) clearance required",
                    "Container Security Initiative (CSI) compliance",
                    "24-hour Advance Manifest Rule"
                ],
                "restricted_items": [
                    "Hazardous materials require special permits",
                    "Food products require FDA approval",
                    "Agricultural products require USDA clearance"
                ]
            },
            "import": {
                "required_documents": [
                    "Import License (if applicable)",
                    "Customs Bond",
                    "Entry Summary (CBP Form 7501)",
                    "ISF Filing 24 hours before loading"
                ],
                "customs_process": [
                    "Pre-arrival processing available",
                    "Physical inspection may be required",
                    "Customs examination fees may apply"
                ],
                "special_requirements": [
                    "FDA Prior Notice for food items",
                    "ISF Bond required",
                    "AMS requirements for certain commodities"
                ]
            },
            "export": {
                "required_documents": [
                    "Export License (if applicable)",
                    "Electronic Export Information (EEI)",
                    "Certificate of Origin",
                    "Dangerous Goods Declaration (if applicable)"
                ],
                "customs_process": [
                    "AES filing required for shipments over $2500",
                    "VGM certification required",
                    "Export control compliance check"
                ],
                "special_requirements": [
                    "SOLAS container weight verification",
                    "Hazmat certification if applicable",
                    "Wood packaging must meet ISPM 15 standards"
                ]
            }
        },
        # Add more locations with their guidelines...
    }
    
    # Get location guidelines or return default message if not found
    location_guidelines = guidelines_db.get(location, {}).get(guideline_type)
    if not location_guidelines:
        return f"Shipping guidelines for {location} are not available. Please contact your MSC representative for detailed information."
    
    # Create a formatted message using markdown
    message_content = f"""
## Shipping Guidelines for {location}
### Type: {guideline_type.capitalize()}
"""
    
    # Add guidelines based on type
    if guideline_type == "general":
        message_content += f"""
#### Port Authority
- {location_guidelines['port_authority']}

#### Operating Hours
- {location_guidelines['operating_hours']}

#### Required Documentation
{chr(10).join(f"- {doc}" for doc in location_guidelines['documentation'])}

#### Key Regulations
{chr(10).join(f"- {reg}" for reg in location_guidelines['key_regulations'])}

#### Restricted Items and Special Handling
{chr(10).join(f"- {item}" for item in location_guidelines['restricted_items'])}
"""
    else:
        message_content += f"""
#### Required Documents
{chr(10).join(f"- {doc}" for doc in location_guidelines['required_documents'])}

#### Customs Process
{chr(10).join(f"- {process}" for process in location_guidelines['customs_process'])}

#### Special Requirements
{chr(10).join(f"- {req}" for req in location_guidelines['special_requirements'])}
"""

    message_content += """
*Note: Regulations and requirements may change. Please verify with local authorities or contact your MSC representative for the most current information.*
"""

    # Send the formatted message
    await cl.Message(content=message_content).send()
    return f"Shipping guidelines for {location} ({guideline_type}) retrieved successfully."

check_container_status_def = {
    "name": "check_container_status",
    "description": "Check the status and location of a shipping container",
    "parameters": {
      "type": "object",
      "properties": {
        "container_number": {
          "type": "string",
          "description": "The container number (e.g., MSCU1234567)"
        },
        "booking_reference": {
          "type": "string",
          "description": "The booking reference number"
        }
      },
      "required": ["container_number", "booking_reference"]
    }
}

async def check_container_status_handler(container_number, booking_reference):
    # Simulate container tracking data
    status = "In Transit"
    current_location = "Port of Singapore"
    departure_date = datetime.now() - timedelta(days=random.randint(1, 5))
    eta = departure_date + timedelta(days=random.randint(3, 10))

    # Create a formatted message using markdown
    message_content = f"""
## Container Status Details
- **Container Number**: {container_number}
- **Booking Reference**: {booking_reference}
- **Current Location**: {current_location}
- **Departure Date**: {departure_date.strftime("%B %d, %Y")}
- **Estimated Arrival**: {eta.strftime("%B %d, %Y")}
- **Status**: {status}
"""

    # Send the formatted message
    await cl.Message(content=message_content).send()
    return f"Container {container_number} status: {status} at {current_location}"

# Tools list
tools = [
    (check_container_status_def, check_container_status_handler),
    (schedule_callback_def, schedule_callback_handler),
    (get_bill_of_lading_def, get_bill_of_lading_handler),
    (get_shipping_quote_def, get_shipping_quote_handler),
    (get_shipping_guidelines_def, get_shipping_guidelines_handler),      
]