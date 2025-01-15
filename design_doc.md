




# MSC Customer Service Bot Technical Walkthrough

## Core Architecture

### Components
1. **Frontend Interface**: Chainlit web application
2. **Backend Processing**: Azure OpenAI GPT-4 with realtime capabilities
3. **Audio Processing**: WebSocket-based streaming audio handler
4. **Business Logic**: Collection of shipping-related tools and handlers
5. **Response Templates**: HTML templates for formatted outputs

### Key Files
```
app.py                           # Main application
realtime/
  ├── __init__.py               # Realtime client implementation
  └── tools.py                  # Business logic and tools
templates/
  ├── order_status.html
  ├── container_status.html
  ├── callback_schedule.html
  └── order_cancellation.html
```

## Detailed Flow Walkthrough

### 1. Initial Setup
When the application starts:
```python
@cl.on_chat_start
async def start():
    # Display welcome message
    await cl.Message(content="Hi, Welcome to MSC...").send()
    
    # Initialize realtime client with system prompt
    await setup_openai_realtime(system_prompt)
```

### 2. Voice Interaction Flow

#### A. Starting Voice Input
When user clicks microphone icon:
1. Triggers `on_audio_start` handler:
```python
@cl.on_audio_start
async def on_audio_start():
    openai_realtime = cl.user_session.get("openai_realtime")
    await openai_realtime.connect()
```

#### B. Processing Speech
As user speaks:
1. Audio chunks are captured and streamed:
```python
@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    openai_realtime = cl.user_session.get("openai_realtime")
    if openai_realtime.is_connected():
        await openai_realtime.append_input_audio(chunk.data)
```

2. Each chunk is:
   - Converted to appropriate format (PCM16)
   - Base64 encoded
   - Sent to OpenAI via WebSocket

3. Speech-to-text processing:
```python
async def handle_input_audio_transcription_completed(event):
    if 'transcript' in delta:
        transcript = delta['transcript']
        if transcript != "":
            # Display user's speech as text in UI
            await cl.Message(
                author="You", 
                type="user_message", 
                content=transcript
            ).send()
```

### 3. AI Processing Flow

#### A. Two-Step AI Interaction
The AI interaction for tool usage happens in two distinct steps:

1. **First AI Interaction**:
   - AI receives user input
   - Determines a tool call is needed
   - Outputs tool name and arguments

2. **Tool Execution**:
   - Application executes the tool
   - Result is added to conversation history
   - New AI response is requested

3. **Second AI Interaction**:
   - AI sees complete conversation including tool result
   - Generates informed response based on tool output

This process is handled through the following code flow:

```python
# Step 1: AI makes tool call
async def _process_function_call_arguments_delta(self, event):
    item_id = event['item_id']
    delta = event['delta']
    item = self.item_lookup.get(item_id)
    if item:
        # Accumulate function arguments
        item['arguments'] += delta
        item['formatted']['tool']['arguments'] += delta
        return item, {'arguments': delta}

# Step 2: Execute tool and add result
async def _call_tool(self, tool):
    try:
        # Execute tool handler
        result = await tool_config["handler"](**json_arguments)
        
        # Add result to conversation
        await self.realtime.send("conversation.item.create", {
            "item": {
                "type": "function_call_output",
                "call_id": tool["call_id"],
                "output": json.dumps(result)
            }
        })
        
        # Request new AI response
        await self.create_response()
    except Exception as e:
        # Error handling...

# Step 3: Trigger new AI response
async def create_response(self):
    if self.get_turn_detection_type() is None and len(self.input_audio_buffer) > 0:
        await self.realtime.send("input_audio_buffer.commit")
        self.conversation.queue_input_audio(self.input_audio_buffer)
        self.input_audio_buffer = bytearray()
    
    await self.realtime.send("response.create")
```

#### B. Tool Call Detection and Processing
Tool calls are detected through event handlers:

```python
async def _on_output_item_done(self, event):
    item, delta = self._process_event(event)
    if item and item["status"] == "completed":
        self.dispatch("conversation.item.completed", {"item": item})
    if item and item.get("formatted", {}).get("tool"):
        await self._call_tool(item["formatted"]["tool"])
```

### 4. Response Processing

#### A. Real-time Processing Optimizations
Several optimizations make the tool execution feel instantaneous:

1. **Streaming Arguments**:
   - Tool arguments arrive as deltas (chunks)
   - Processing begins before receiving complete arguments
   - Parallel execution of different components

2. **Async Processing**:
```python
# Event dispatch happens immediately
def dispatch(self, event_name, event):
    for handler in self.event_handlers[event_name]:
        if inspect.iscoroutinefunction(handler):
            asyncio.create_task(handler(event))
        else:
            handler(event)
```

3. **WebSocket Management**:
```python
class RealtimeAPI(RealtimeEventHandler):
    async def connect(self):
        self.ws = await websockets.connect(f"{self.url}/openai/realtime?...")
        asyncio.create_task(self._receive_messages())

    async def _receive_messages(self):
        async for message in self.ws:
            event = json.loads(message)
            self.dispatch(f"server.{event['type']}", event)
```

#### B. Response Generation
1. Text responses stream to UI while processing
2. Speech synthesis occurs in parallel
3. Formatted HTML responses display immediately

```python
async def handle_conversation_updated(event):
    if delta:
        if 'audio' in delta:
            # Stream audio
            await cl.context.emitter.send_audio_chunk(
                cl.OutputAudioChunk(
                    mimeType="pcm16",
                    data=delta['audio'],
                    track=cl.user_session.get("track_id")
                )
            )
        if 'text' in delta:
            # Stream text
            item['formatted']['text'] += delta['text']
```

## Data Flow Summary

1. **Voice Input Flow**
   - User activates microphone
   - Speech streams to OpenAI
   - Transcription appears in UI
   - AI processes input

2. **Tool Execution Flow**
   - AI determines tool needed (First interaction)
   - Tool executes asynchronously
   - Result added to conversation
   - AI generates response (Second interaction)

3. **Response Flow**
   - Text streams to UI
   - Speech synthesizes in parallel
   - Formatted responses display
   - Conversation continues

## Key Technical Details

1. **Audio Format**: PCM16 (16-bit Pulse Code Modulation)
2. **Communication**: WebSocket for real-time streaming
3. **Async Processing**: Non-blocking operations throughout
4. **Error Handling**: Comprehensive try-catch blocks
5. **Session Management**: Chainlit sessions maintain state

## Configuration

Key configuration in session setup:
```python
session_config = {
    "modalities": ["text", "audio"],
    "voice": "shimmer",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "input_audio_transcription": {"model": "whisper-1"},
    "turn_detection": {"type": "server_vad"},
    "temperature": 0.8,
    "max_response_output_tokens": 4096
}
```

## Example Interaction Flow

Here's a complete example of a shipping quote request:

1. **User Input**:
   "I need a shipping quote from Shanghai to Rotterdam"

2. **First AI Interaction**:
   - AI determines need for shipping quote tool
   - Makes tool call with parameters:
     - origin: "Shanghai"
     - destination: "Rotterdam"

3. **Tool Execution**:
   - `get_shipping_quote_handler` executes
   - Calculates quote details
   - Formats response with HTML template
   - Adds result to conversation

4. **Second AI Interaction**:
   - AI sees tool result in conversation
   - Generates natural response incorporating quote details
   - "Based on the quote, shipping from Shanghai to Rotterdam will cost..."

5. **Response Delivery**:
   - Text streams to UI
   - Speech synthesizes simultaneously
   - Formatted quote displays in UI
   - Ready for next user input