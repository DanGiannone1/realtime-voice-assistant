import json
import random
from datetime import datetime, timedelta
import chainlit as cl
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation history
conversation_history: List[Dict[str, Any]] = []

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
    "description": "Show mandatory and voluntary slowdown guidance for whale protection in a specific region",
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
    "description": "Show list of vessels and their routes through a specific region",
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
    "description": "Send notifications to vessels about whale protection measures",
    "parameters": {
        "type": "object",
        "properties": {
            "vessel_ids": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of vessel IMO numbers or identifiers"
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

async def show_whale_routes_handler(region, season="current"):
    try:
        # Simulated whale protection zones and speed restrictions
        whale_zones = {
            "Gulf of St. Lawrence": {
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

        message_content = f"""
## Whale Protection Measures - {region}
### Season: {season}
"""

        if region == "Gulf of St. Lawrence":
            # Static Zones
            message_content += """
### 1. Static Zones (Mandatory)
| Zone | Speed Limit | Bounds |
|------|-------------|--------|
"""
            for zone in whale_zones[region]["static_zones"]["zones"]:
                message_content += f"| {zone['name']} | {whale_zones[region]['static_zones']['speed_limit']} | {zone['bounds']} |\n"

            # Dynamic Zones
            message_content += f"""
### 2. Dynamic Shipping Zones
**Speed Limit:** {whale_zones[region]["dynamic_zones"]["speed_limit"]}
**Activation:** {whale_zones[region]["dynamic_zones"]["activation"]}

| Zone | Bounds |
|------|--------|
"""
            for zone in whale_zones[region]["dynamic_zones"]["zones"]:
                message_content += f"| {zone['name']} | {zone['bounds']} |\n"

            # Seasonal Areas
            message_content += f"""
### 3. Seasonal Management Areas
**Speed Limit:** {whale_zones[region]["seasonal_areas"]["speed_limit"]}
**Conditions:** {whale_zones[region]["seasonal_areas"]["conditions"]}

| Area | Bounds |
|------|--------|
"""
            for area in whale_zones[region]["seasonal_areas"]["areas"]:
                message_content += f"| {area['name']} | {area['bounds']} |\n"

            # Voluntary Zone
            message_content += f"""
### 4. Voluntary Measures
**Area:** Cabot Strait
**Speed Limit:** {whale_zones[region]["voluntary"]["speed_limit"]}
**Bounds:** {whale_zones[region]["voluntary"]["bounds"]}
"""

        else:
            # Default format for other regions
            message_content += """
#### Mandatory Speed Restriction Zones
| Zone | Speed Limit | Active Period |
|------|-------------|---------------|
"""
            for zone in whale_zones[region]["mandatory_zones"]:
                message_content += f"| {zone['zone']} | {zone['speed_limit']} | {zone['period']} |\n"

            message_content += """
#### Voluntary Speed Restriction Zones
| Zone | Recommended Speed | Active Period |
|------|------------------|---------------|
"""
            for zone in whale_zones[region]["voluntary_zones"]:
                message_content += f"| {zone['zone']} | {zone['speed_limit']} | {zone['period']} |\n"

        message_content += """
[REF: TC-NAV-2024-03 | RESTR-CLASS: INT | DIST: OPS-MAR-ROUTES]
"""

        await cl.Message(content=message_content).send()
        result = f"Whale protection measures displayed for {region}"
        log_tool_call("show_whale_routes", {"region": region, "season": season}, result, message_content)
        return result
    except Exception as e:
        error_msg = f"Error in show_whale_routes: {str(e)}"
        log_tool_call("show_whale_routes", {"region": region, "season": season}, error_msg)
        raise

async def check_routes_handler(region, date_range="next 7 days"):
    try:
        # Simulated vessel routes
        vessel_routes = {
            "Gulf of St. Lawrence": [
                {"vessel_name": "MSC ANNA", "imo": "9839272", "eta": "2024-03-25", "route": "Montreal → Rotterdam"},
                {"vessel_name": "CMA CGM MARCO POLO", "imo": "9454436", "eta": "2024-03-26", "route": "Halifax → Hamburg"},
                {"vessel_name": "OOCL HAMBURG", "imo": "9776171", "eta": "2024-03-28", "route": "New York → Montreal"}
            ],
            "Santa Barbara Channel": [
                {"vessel_name": "COSCO SHIPPING ROSE", "imo": "9783615", "eta": "2024-03-24", "route": "Los Angeles → Oakland"},
                {"vessel_name": "EVER GIVEN", "imo": "9811000", "eta": "2024-03-27", "route": "Seattle → Los Angeles"},
                {"vessel_name": "ONE BLUE JAY", "imo": "9806079", "eta": "2024-03-29", "route": "Oakland → Los Angeles"}
            ]
        }

        if region not in vessel_routes:
            result = f"No vessel routes found for region: {region}"
            log_tool_call("check_routes", {"region": region, "date_range": date_range}, result)
            return result

        message_content = f"""
## Vessel Routes Through {region}
### Period: {date_range}

| Vessel Name | IMO Number | ETA | Route |
|-------------|------------|-----|-------|
"""
        for vessel in vessel_routes[region]:
            message_content += f"| {vessel['vessel_name']} | {vessel['imo']} | {vessel['eta']} | {vessel['route']} |\n"

        message_content += """
[REF: VTS-ROUTE-LOG | UPD-FREQ: 4H | SOURCE: AIS-TRACK-001]
"""

        await cl.Message(content=message_content).send()
        result = f"Vessel routes displayed for {region}"
        log_tool_call("check_routes", {"region": region, "date_range": date_range}, result, message_content)
        return result
    except Exception as e:
        error_msg = f"Error in check_routes: {str(e)}"
        log_tool_call("check_routes", {"region": region, "date_range": date_range}, error_msg)
        raise

async def send_notification_handler(vessel_ids, message, priority="medium"):
    try:
        notification_status = []
        for vessel_id in vessel_ids:
            status = {
                "vessel_id": vessel_id,
                "status": "delivered",
                "timestamp": datetime.now().isoformat(),
                "priority": priority
            }
            notification_status.append(status)

        message_content = f"""
## Notification Status
Priority Level: {priority.upper()}

| Vessel ID | Status | Timestamp |
|-----------|---------|-----------|
"""
        for status in notification_status:
            message_content += f"| {status['vessel_id']} | {status['status']} | {status['timestamp']} |\n"

        message_content += f"""
### Message Content:
{message}

[DIST: VESSEL-OPS | ACK-REQ: {priority.upper()} | PROTO: NAVTEX-{priority.upper()}]
"""

        await cl.Message(content=message_content).send()
        result = f"Notifications sent to {len(vessel_ids)} vessels"
        log_tool_call("send_notification", {
            "vessel_ids": vessel_ids,
            "message": message,
            "priority": priority
        }, result, message_content)
        return result
    except Exception as e:
        error_msg = f"Error in send_notification: {str(e)}"
        log_tool_call("send_notification", {
            "vessel_ids": vessel_ids,
            "message": message,
            "priority": priority
        }, error_msg)
        raise

# Tools list
tools = [
    (show_whale_routes_def, show_whale_routes_handler),
    (check_routes_def, check_routes_handler),
    (send_notification_def, send_notification_handler),
]