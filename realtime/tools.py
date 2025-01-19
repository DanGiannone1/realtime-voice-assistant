import json
import random
from datetime import datetime, timedelta
import chainlit as cl
from typing import List, Dict, Any
import logging
import os
from cosmos_db import CosmosDBManager
from azure.communication.email import EmailClient
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
cosmos_db = CosmosDBManager()
email_client = EmailClient.from_connection_string(os.environ.get("COMMUNICATION_SERVICES_CONNECTION_STRING"))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")

# Conversation history


def log_tool_call(tool_name: str, inputs: Dict[str, Any], output: str, details: str = None):
    """Log tool calls and update conversation history"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "tool": tool_name,
        "inputs": inputs,
        "output": output,
        "details": details
    }
    
    # Log the tool call
    logger.info(f"\n{'='*80}")
    logger.info(f"Tool Call: {tool_name}")
    logger.info(f"Timestamp: {timestamp}")
    logger.info("\nInputs:")
    for key, value in inputs.items():
        logger.info(f"  {key}: {value}")
    logger.info(f"\nOutput Summary: {output}")
    if details:
        logger.info(f"\nDetailed Output:\n{details}")
    logger.info(f"{'='*80}\n")

# Function Definitions
show_whale_routes_def = {
    "name": "show_whale_routes",
    "description": "Show mandatory and voluntary slowdown guidance for whale protection in a specific region. This tool should be used when a user asks for whale routes, whale protection measures, migration patterns,or any information related to whale protection in a specific region.",
    "parameters": {
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "The region/area to check for whale protection measures (e.g., Gulf of St. Lawrence, Bay of Fundy, Santa Barbara Channel)"
            },
            "season": {
                "type": "string",
                "description": "The season to check (e.g., Summer 2024, Winter 2023)",
                "default": "current"
            }
        },
        "required": ["region"]
    }
}

check_routes_def = {
    "name": "check_routes",
    "description": "Show list of vessels and their routes through a specific region. Use this tool when a user asks a question that is related to vessel routes through a specific region. Example: 'What upcoming routes are impacted by whale protection measures in the Gulf of St. Lawrence?'",
    "parameters": {
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "The region/area to check for vessel routes"
            },
            "date_range": {
                "type": "string",
                "description": "Date range to check (e.g., 'next 7 days', 'next 30 days')",
                "default": "next 7 days"
            }
        },
        "required": ["region"]
    }
}

send_notification_def = {
    "name": "send_notification",
    "description": "Send notifications to vessels. Make sure to confirm the message contents with the user before actually calling this tool.",
    "parameters": {
        "type": "object",
        "properties": {
            "vessel_ids": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of vessel IMO numbers (unique identifiers)"
            },
            "message": {
                "type": "string",
                "description": "The notification message to send"
            },
            "priority": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "default": "medium",
                "description": "Priority level of the notification"
            }
        },
        "required": ["vessel_ids", "message"]
    }
}

create_ticket_def = {
    "name": "create_ticket",
    "description": "Create a support ticket in Bridge for customer impact outreach. Use this tool when a user requests to create a ticket for handling customer communications or impact notifications.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the ticket"
            },
            "vessel_imos": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of impacted vessel IMO numbers"
            },
            "description": {
                "type": "string",
                "description": "Detailed description of the impact and required outreach"
            }
        },
        "required": ["title", "vessel_imos", "description"]
    }
}

async def show_whale_routes_handler(region, season="current"):
    try:
        # Configuration
        PDF_FILENAME = "wsc-whale-migration-patterns-latest.pdf"  # The actual filename in data folder
        BASE_PDF_URL = "https://static1.squarespace.com/static/5ff6c5336c885a268148bdcc/t/672e33f771bca527f4adda11/1731081219615/WSC+Whale+Chart_+A+global+voyage+planning+aid+to+protect+whales+%28Oct+2024%29.pdf"
        PDF_PAGE = 5
        PDF_URL = f"{BASE_PDF_URL}#page={PDF_PAGE}"
        
        # Simulated whale protection zones and speed restrictions
        whale_zones = {
            "Gulf of St. Lawrence": {
                "image_path": "data/whale_routes_gulf_of_st_lawrence.png",
                "static_zones": {
                    "description": "Mandatory Static Zones",
                    "speed_limit": "≤10 knots",
                    "zones": [
                        {
                            "name": "Northern Static Zone",
                            "bounds": "50°20′N to 47°58.1′N, 65°00′W to 61°00′W"
                        },
                        {
                            "name": "Southern Static Zone",
                            "bounds": "48°40′N to 47°10′N, 65°00′W to 61°03.5′W"
                        }
                    ]
                },
                "dynamic_zones": {
                    "description": "Mandatory Dynamic Shipping Zones",
                    "speed_limit": "≤10 knots when whales present",
                    "activation": "NAVWARN (15-day minimum)",
                    "zones": [
                        {
                            "name": "Zone A",
                            "bounds": "49°41′N to 49°11′N, 65°00′W to 64°00′W"
                        },
                        {
                            "name": "Zone B",
                            "bounds": "49°22′N to 48°48′N, 64°00′W to 63°00′W"
                        },
                        {
                            "name": "Zone C",
                            "bounds": "49°00′N to 48°24′N, 63°00′W to 62°00′W"
                        },
                        {
                            "name": "Zone D",
                            "bounds": "50°16′N to 49°56′N, 64°00′W to 63°00′W"
                        },
                        {
                            "name": "Zone E",
                            "bounds": "48°35′N to 47°58.1′N, 62°00′W to 61°00′W"
                        }
                    ]
                },
                "seasonal_areas": {
                    "description": "Seasonal Management Areas",
                    "speed_limit": "≤10 knots",
                    "conditions": "Mandatory early season, whale-dependent late season",
                    "areas": [
                        {
                            "name": "Area 1",
                            "bounds": "49°04′N to 48°10.5′N, 62°00′W to 61°00′W"
                        },
                        {
                            "name": "Area 2",
                            "bounds": "48°24′N to 47°26.69′N, 62°00′W to 61°03.5′W"
                        }
                    ]
                },
                "voluntary": {
                    "description": "Cabot Strait Voluntary Slowdown",
                    "speed_limit": "≤10 knots",
                    "bounds": "48°10.5′N to 47°02′N, 61°00′W to 59°18.5′W"
                }
            },
            "Santa Barbara Channel": {
                "mandatory_zones": [
                    {"zone": "Traffic Separation Scheme", "speed_limit": "10 knots", "period": "May 1 - Dec 15"}
                ],
                "voluntary_zones": [
                    {"zone": "Western Approach", "speed_limit": "10 knots", "period": "May 1 - Dec 15"},
                    {"zone": "Santa Barbara Coast", "speed_limit": "10 knots", "period": "Year-round"}
                ]
            }
        }

        if region not in whale_zones:
            result = f"No whale protection measures found for region: {region}"
            log_tool_call("show_whale_routes", {"region": region, "season": season}, result)
            return result

        # Create header content
        header_content = f"""
## Whale Protection Measures - {region}
### Season: {season}
"""

        # Create main content
        main_content = ""
        if region == "Gulf of St. Lawrence":
            # Static Zones
            main_content += """
### 1. Static Zones (Mandatory)
| Zone | Speed Limit | Bounds |
|------|-------------|--------|
"""
            for zone in whale_zones[region]["static_zones"]["zones"]:
                main_content += f"| {zone['name']} | {whale_zones[region]['static_zones']['speed_limit']} | {zone['bounds']} |\n"

            # Dynamic Zones
            main_content += f"""
### 2. Dynamic Shipping Zones
**Speed Limit:** {whale_zones[region]["dynamic_zones"]["speed_limit"]}
**Activation:** {whale_zones[region]["dynamic_zones"]["activation"]}

| Zone | Bounds |
|------|--------|
"""
            for zone in whale_zones[region]["dynamic_zones"]["zones"]:
                main_content += f"| {zone['name']} | {zone['bounds']} |\n"

            # Seasonal Areas
            main_content += f"""
### 3. Seasonal Management Areas
**Speed Limit:** {whale_zones[region]["seasonal_areas"]["speed_limit"]}
**Conditions:** {whale_zones[region]["seasonal_areas"]["conditions"]}

| Area | Bounds |
|------|--------|
"""
            for area in whale_zones[region]["seasonal_areas"]["areas"]:
                main_content += f"| {area['name']} | {area['bounds']} |\n"

            # Voluntary Zone
            main_content += f"""
### 4. Voluntary Measures
**Area:** Cabot Strait
**Speed Limit:** {whale_zones[region]["voluntary"]["speed_limit"]}
**Bounds:** {whale_zones[region]["voluntary"]["bounds"]}
"""

        else:
            # Default format for other regions
            main_content += """
#### Mandatory Speed Restriction Zones
| Zone | Speed Limit | Active Period |
|------|-------------|---------------|
"""
            for zone in whale_zones[region]["mandatory_zones"]:
                main_content += f"| {zone['zone']} | {zone['speed_limit']} | {zone['period']} |\n"

            main_content += """
#### Voluntary Speed Restriction Zones
| Zone | Recommended Speed | Active Period |
|------|------------------|---------------|
"""
            for zone in whale_zones[region]["voluntary_zones"]:
                main_content += f"| {zone['zone']} | {zone['speed_limit']} | {zone['period']} |\n"

        main_content += f"""

> ### 📊 Source Information
> | Category | Value |
> |----------|-------|
> | 📄 Document | <a href="{PDF_URL}" style="color: #4a90e2">`{PDF_FILENAME}`</a> (page {PDF_PAGE}) |
>
> ⏱️ **Last Updated:** {(datetime.now() - timedelta(minutes=15)).strftime("%d-%m-%y %I:%M %p")}"""

        # Create elements list for the image
        elements = []
        if "image_path" in whale_zones[region]:
            elements.append(
                cl.Image(
                    name=f"whale_routes_{region.lower().replace(' ', '_')}", 
                    path=whale_zones[region]["image_path"],
                    display="inline"
                )
            )

        # Send message with header, image, and main content in the desired order
        await cl.Message(
            content=header_content,
            elements=elements
        ).send()
        
        # Send the main content as a separate message
        await cl.Message(content=main_content).send()
        
        # Return both status and full details
        result = {
            "status": f"Whale protection measures displayed for {region}",
            "details": header_content + main_content
        }
        log_tool_call("show_whale_routes", {"region": region, "season": season}, result)
        return result
    except Exception as e:
        error_msg = f"Error in show_whale_routes: {str(e)}"
        log_tool_call("show_whale_routes", {"region": region, "season": season}, error_msg)
        raise

async def check_routes_handler(region, date_range="next 7 days"):
    try:
        # Use global cosmos_db instance instead of creating new one
        global cosmos_db

        # Query based on region
        if region.lower() == "gulf of st. lawrence":
            query = """
            SELECT * FROM c 
            WHERE c.partitionKey = 'vessel_route' 
            AND (c.origin = 'Montreal' OR c.destination = 'Montreal')
            """
            vessels = cosmos_db.query_items(query)
        elif region.lower() == "santa barbara channel":
            query = """
            SELECT * FROM c 
            WHERE c.partitionKey = 'vessel_route' 
            AND (
                (c.origin = 'Los Angeles' OR c.destination = 'Los Angeles')
                OR (c.origin = 'Oakland' OR c.destination = 'Oakland')
            )
            """
            vessels = cosmos_db.query_items(query)
        else:
            result = f"No vessel routes found for region: {region}"
            log_tool_call("check_routes", {"region": region, "date_range": date_range}, result)
            return result

        if not vessels:
            result = f"No active vessel routes found for region: {region}"
            log_tool_call("check_routes", {"region": region, "date_range": date_range}, result)
            return result

        # Create message content with markdown table
        message_content = f"""
# Vessel Routes Through {region}
*Period: {date_range}*

| Vessel Name | IMO Number | ETA | Origin | Destination | Status |
|-------------|------------|-----|--------|-------------|---------|
"""
        
        for vessel in vessels:
            message_content += f"| {vessel['vessel_name']} | {vessel['imo']} | {vessel['eta']} | {vessel['origin']} | {vessel['destination']} | {vessel['route_status']} |\n"

        # Update the reference format to include database details
        if region.lower() == "gulf of st. lawrence":
            ref_query = "SELECT * FROM c WHERE c.partitionKey = 'vessel_route' AND (c.origin = 'Montreal' OR c.destination = 'Montreal')"
        else:
            ref_query = "SELECT * FROM c WHERE c.partitionKey = 'vessel_route' AND ((c.origin = 'Los Angeles' OR c.destination = 'Los Angeles') OR (c.origin = 'Oakland' OR c.destination = 'Oakland'))"

        message_content += f"""

> ### 📊 Source Information
> | Category | Value |
> |----------|-------|
> | 🗄️ Database | `MSC_DB_2` |
> | 📑 Schema | `routes` |
>
> **🔍 Query:**
> ```sql
> {ref_query}
> ```
> ⏱️ **Last Updated:** {(datetime.now() - timedelta(minutes=15)).strftime("%d-%m-%y %I:%M %p")}"""

        # Send single message with complete table
        await cl.Message(content=message_content).send()
        
        # Return both status and full details
        result = {
            "status": f"Vessel routes displayed for {region}",
            "details": message_content
        }
        log_tool_call("check_routes", {"region": region, "date_range": date_range}, result)
        return result
    except Exception as e:
        error_msg = f"Error in check_routes: {str(e)}"
        log_tool_call("check_routes", {"region": region, "date_range": date_range}, error_msg)
        raise

async def send_notification_handler(vessel_ids, message, priority="medium"):
    try:
        timestamp = datetime.now().isoformat()
        
        # Get priority color
        priority_colors = {
            "high": "#DC3545",
            "medium": "#FFC107",
            "low": "#28A745"
        }
        priority_color = priority_colors.get(priority.lower(), "#6C757D")
        
        # Send single email for all vessels
        email_message = {
            "senderAddress": SENDER_EMAIL,
            "recipients": {
                "to": [{"address": RECIPIENT_EMAIL}]
            },
            "content": {
                "subject": f"[EXTERNAL] Vessel Notification - {priority.upper()} Priority",
                "plainText": message,
                "html": f"""
                <html>
                    <head>
                        <style>
                            body {{
                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                                line-height: 1.6;
                                margin: 0;
                                padding: 0;
                                background-color: #f8f9fa;
                            }}
                            .container {{
                                max-width: 600px;
                                margin: 20px auto;
                                background: #ffffff;
                                border-radius: 8px;
                                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                            }}
                            .header {{
                                background-color: {priority_color};
                                color: #ffffff;
                                padding: 20px;
                                border-radius: 8px 8px 0 0;
                            }}
                            .header h1 {{
                                margin: 0;
                                font-size: 24px;
                                font-weight: 600;
                            }}
                            .priority-badge {{
                                display: inline-block;
                                background: rgba(255, 255, 255, 0.2);
                                padding: 4px 12px;
                                border-radius: 16px;
                                font-size: 14px;
                                margin-top: 8px;
                            }}
                            .content {{
                                padding: 30px;
                                color: #343a40;
                            }}
                            .message {{
                                background-color: #f8f9fa;
                                border-left: 4px solid {priority_color};
                                padding: 15px;
                                margin: 20px 0;
                            }}
                            .vessel-info {{
                                background-color: #e9ecef;
                                padding: 15px;
                                border-radius: 4px;
                                margin-top: 20px;
                            }}
                            .footer {{
                                padding: 20px;
                                color: #6c757d;
                                font-size: 14px;
                                border-top: 1px solid #dee2e6;
                                text-align: center;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>🚢 Vessel Notification</h1>
                                <div class="priority-badge">
                                    {priority.upper()} PRIORITY
                                </div>
                            </div>
                            <div class="content">
                                <div class="message">
                                    {message}
                                </div>
                                <div class="vessel-info">
                                    <strong>Vessels Affected:</strong> {len(vessel_ids)}<br>
                                    <strong>IMO Numbers:</strong> {", ".join(vessel_ids)}<br>
                                    <strong>Time:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
                                </div>
                            </div>
                            <div class="footer">
                                This is an automated message from the Vessel Notification System.<br>
                                Please do not reply to this email.
                            </div>
                        </div>
                    </body>
                </html>
                """
            }
        }
        
        # Send the email
        poller = email_client.begin_send(email_message)
        result = poller.result()
        
        # Create message content for chat
        message_content = f"""
## 🔔 Notification Sent
**Priority Level:** {priority.upper()}
**Status:** Delivered
**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}

### 🚢 Vessels Notified
Total vessels: {len(vessel_ids)}
{"".join(f"- IMO: {imo}\n" for imo in vessel_ids)}

### 📝 Message Content
> {message}
"""

        await cl.Message(content=message_content).send()
        
        # Return both status and full details
        result = {
            "status": f"Notification sent to {len(vessel_ids)} vessels",
            "details": message_content
        }
        log_tool_call("send_notification", {
            "vessel_ids": vessel_ids,
            "message": message,
            "priority": priority
        }, result)
        return result
    except Exception as e:
        error_msg = f"Error in send_notification: {str(e)}"
        log_tool_call("send_notification", {
            "vessel_ids": vessel_ids,
            "message": message,
            "priority": priority
        }, error_msg)
        raise

async def create_ticket_handler(title, vessel_imos, description):
    try:
        # Create timestamp for the ticket
        timestamp = datetime.now().isoformat()
        
        # Demo: Map of example major customers that would be impacted
        example_customers = ["Walmart", "Apple", "Mercedes-Benz", "Adidas"]
        
        # Format ticket data
        ticket_data = {
            "id": str(uuid4()),
            "title": title,
            "description": description,
            "created_at": timestamp,
            "vessel_imos": vessel_imos,
            "impacted_customers": example_customers,
            "status": "open"
        }
        
        # Store ticket in Cosmos DB
        cosmos_db.create_item(ticket_data)
        
        # Create message content with ticket details
        message_content = f"""
## 🎫 Support Ticket Created
**Title:** {title}
**Ticket ID:** {ticket_data['id']}

### 📝 Description
{description}

### 🚢 Impacted Vessels
Total vessels affected: {len(vessel_imos)}
{"".join(f"- IMO: {imo}\n" for imo in vessel_imos)}

### 👥 Major Customers Impacted
{"".join(f"- {customer}\n" for customer in example_customers)}
"""

        await cl.Message(content=message_content).send()
        
        # Return both status and full details
        result = {
            "status": f"Support ticket created: {ticket_data['id']}",
            "details": message_content
        }
        log_tool_call("create_ticket", {
            "title": title,
            "vessel_imos": vessel_imos,
            "description": description
        }, result)
        return result
    except Exception as e:
        error_msg = f"Error in create_ticket: {str(e)}"
        log_tool_call("create_ticket", {
            "title": title,
            "vessel_imos": vessel_imos,
            "description": description
        }, error_msg)
        raise

# Tools list
tools = [
    (show_whale_routes_def, show_whale_routes_handler),
    (check_routes_def, check_routes_handler),
    (send_notification_def, send_notification_handler),
    (create_ticket_def, create_ticket_handler),
]