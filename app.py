import os
import asyncio
from openai import AsyncAzureOpenAI

import chainlit as cl
from uuid import uuid4
from chainlit.logger import logger

from realtime import RealtimeClient
from realtime.tools import tools, cosmos_db

client = AsyncAzureOpenAI(api_key=os.environ["AZURE_OPENAI_API_KEY"],
                          azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                          azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
                          api_version="2024-10-01-preview")    

async def setup_openai_realtime(system_prompt: str):
    """Instantiate and configure the OpenAI Realtime Client"""
    openai_realtime = RealtimeClient(system_prompt = system_prompt)
    cl.user_session.set("track_id", str(uuid4()))
    
    async def handle_conversation_updated(event):
        item = event.get("item")
        delta = event.get("delta")
        """Currently used to stream audio back to the client."""
        if delta:
            # Only one of the following will be populated for any given event
            if 'audio' in delta:
                audio = delta['audio']  # Int16Array, audio added
                await cl.context.emitter.send_audio_chunk(cl.OutputAudioChunk(mimeType="pcm16", data=audio, track=cl.user_session.get("track_id")))
                
            if 'arguments' in delta:
                arguments = delta['arguments']  # string, function arguments added
                pass
            
    async def handle_item_completed(item):
        """Generate the transcript once an item is completed and populate the chat context."""
        try:
            transcript = item['item']['formatted']['transcript']
            if transcript != "":
                await cl.Message(content=transcript).send()
        except:
            pass
    
    async def handle_conversation_interrupt(event):
        """Used to cancel the client previous audio playback."""
        cl.user_session.set("track_id", str(uuid4()))
        await cl.context.emitter.send_audio_interrupt()
        
    async def handle_input_audio_transcription_completed(event):
        item = event.get("item")
        delta = event.get("delta")
        if 'transcript' in delta:
            transcript = delta['transcript']
            if transcript != "":
                await cl.Message(author="You", type="user_message", content=transcript).send()
        
    async def handle_error(event):
        logger.error(event)
        
    
    openai_realtime.on('conversation.updated', handle_conversation_updated)
    openai_realtime.on('conversation.item.completed', handle_item_completed)
    openai_realtime.on('conversation.interrupted', handle_conversation_interrupt)
    openai_realtime.on('conversation.item.input_audio_transcription.completed', handle_input_audio_transcription_completed)
    openai_realtime.on('error', handle_error)

    cl.user_session.set("openai_realtime", openai_realtime)
    coros = [openai_realtime.add_tool(tool_def, tool_handler) for tool_def, tool_handler in tools]
    await asyncio.gather(*coros)
    

system_prompt = """You are an internal agent for MSC. You help employees do their jobs by leveraging tools to answer questions and provide information.


# Steps

1. **Identify the question:** Carefully read the employee's inquiry to understand the problem or question they are presenting.
2. **Gather Relevant Information:** Consider what tools you have available. Check for any additional data needed, which will be the inputs to the tools. 
3. **Formulate a Response:** Use the tools to answer the question. Consider the conversation history when deciding the inputs to the tools. For example, if the user asks for whale migration patterns 
in the Gulf of St. Lawrence, and then you provided the info, if the user then asks for "which of our routesare impacted by this", you can assume they are asking about routes through the Gulf of St. Lawrence.


# Output Format

Be very brief and concise. Generally the tool will provide the core information. You just need to quickly summarize in 1-2 sentences or less. Do not include notes or disclaimers. 
If the query is answered via a tool call, just simply state that you have provided the information and ask "whats next?" (we want to be goal-oriented and work quickly). If the user asks for clarification or insights, feel free to share your thoughts.

# Tools

 1. `show_whale_routes`
   - Shows mandatory and voluntary slowdown guidance for whale protection in specific regions
   - Displays speed limits, zone boundaries, and activation conditions
   - Supports regions like Gulf of St. Lawrence and Santa Barbara Channel
   - Parameters:
     - region (required): The region/area to check (e.g., "Gulf of St. Lawrence")
     - season (optional): The season to check (defaults to "current")

2. `check_routes`
   - Shows list of vessels and their routes through specific regions
   - Displays vessel names, IMO numbers, ETAs, and routes
   - Parameters:
     - region (required): The region/area to check
     - date_range (optional): Date range to check (defaults to "next 7 days")

3. `send_notification`
   - Sends notifications to vessels about whale protection measures. Make sure to confirm the message contents with the user before actually calling this tool.
   - Parameters:
     - vessel_ids (required): List of vessel IMO numbers
     - message (required): The notification message
     - priority (optional): "high", "medium", or "low" (defaults to "medium")

4. `create_ticket`
   - Creates support tickets in Bridge for customer impact outreach
   - Automatically identifies major customers impacted by vessel disruptions
   - Parameters:
     - title (required): Title of the ticket
     - vessel_imos (required): List of impacted vessel IMO numbers
     - description (required): Detailed description of the impact and required outreach

 
# """

@cl.on_chat_start
async def start():
    # Verify Cosmos DB connection is ready
    try:
        # Test query to verify connection
        cosmos_db.query_items("SELECT TOP 1 * FROM c")
        logger.info("Cosmos DB connection verified")
    except Exception as e:
        logger.error(f"Failed to connect to Cosmos DB: {e}")
        await cl.Message(content="⚠️ Warning: Database connection is not available. Some features may be limited.").send()

    await cl.Message(
        content="Hi, how can I help you?. Press `P` to talk!"
    ).send()
    await setup_openai_realtime(system_prompt=system_prompt + "\n\n Customer ID: 12121")

@cl.on_message
async def on_message(message: cl.Message):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.send_user_message_content([{ "type": 'input_text', "text": message.content}])
    else:
        await cl.Message(content="Please activate voice mode before sending messages!").send()

@cl.on_audio_start
async def on_audio_start():
    try:
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        # TODO: might want to recreate items to restore context
        # openai_realtime.create_conversation_item(item)
        await openai_realtime.connect()
        logger.info("Connected to OpenAI realtime")
        return True
    except Exception as e:
        await cl.ErrorMessage(content=f"Failed to connect to OpenAI realtime: {e}").send()
        return False

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime:            
        if openai_realtime.is_connected():
            await openai_realtime.append_input_audio(chunk.data)
        else:
            logger.info("RealtimeClient is not connected")

@cl.on_audio_end
@cl.on_chat_end
@cl.on_stop
async def on_end():
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.disconnect()