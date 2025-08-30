# SearchQA Environment Visualization

A comprehensive frontend visualization for the SearchQA environment that provides real-time monitoring of question-answering sessions with search capabilities.

## Features

### 📊 Status Panel
- **Rounds Tracking**: Shows current round (1-5) with visual warnings as rounds approach the limit
- **State Indicator**: Displays current environment state (Ready, Active, Completed, Max Rounds)
- **Score Display**: Real-time reward tracking with success highlighting

### ❓ Question Panel
- Clear display of the current question extracted from server observations
- Formatted for easy reading with highlighted styling
- Automatically updates when environment resets or new questions are loaded

### 🔍 Search History Panel
- **Complete Action History**: Tracks all searches, answers, and invalid actions
- **Timestamped Entries**: Each action shows when it was performed
- **Search Results**: Displays formatted search results with HTML rendering
- **Answer Feedback**: Shows whether answers were correct or incorrect with visual indicators
- **Invalid Action Warnings**: Highlights invalid actions with error messages
- **Clear History**: Button to reset the history when needed

### ℹ️ Current Information Panel
- Shows the most recent search results from `<information>` tags
- Formatted for easy reading with HTML markup support
- Only appears when search results are available

## Server Integration

### API Format Compatibility
The client is fully compatible with the actual SearchQA server API:

```python
# Create Environment
POST /create
Body: {"id": int}  # Item ID (0-221327)
Response: int      # Environment ID

# Step Action
POST /step
Body: {"env_idx": int, "action": str}
Response: {"observation": str, "reward": float, "done": bool, "info": None}

# Get Observation  
GET /observation?env_idx=int
Response: str      # Formatted prompt with question

# Reset Environment
POST /reset
Body: {"env_idx": int, "id": Optional[int]}
Response: str      # New observation
```

### Data Processing
- **Question Extraction**: Intelligent parsing of server observation format
- **Action Tracking**: Automatic tracking of user actions via client
- **Search Results**: Proper handling of `<information>` tagged content
- **Feedback Recognition**: Detection of success/failure messages

## Usage

### Environment Configuration
- **Max Rounds**: 5 (tracked automatically based on search actions)
- **Supported Actions**: `<search>`, `<answer>`, `<think>`
- **Port**: 36005 (default SearchQA server port)
- **Item Range**: 0-221327 (test: 0-51712, train: 51713-221327)

### Dataset Support
- **Test Datasets**: nq, triviaqa, popqa, hotpotqa, 2wikimultihopqa, musique, bamboogle
- **Train Datasets**: nq, hotpotqa
- **Total Items**: 221,328 (51,713 test + 169,615 train)

### Action Format
The environment expects actions in XML-like tags:
- **Search**: `<search>your search query here</search>`
- **Answer**: `<answer>your answer here</answer>`
- **Think**: `<think>your reasoning here</think>`

### Response Handling
- **Search Response**: `\n\n<information>formatted_results</information>\n\n`
- **Correct Answer**: "Congratulations! You have answered the question correctly."
- **Incorrect Answer**: "Sorry, your answer is incorrect. Please try again."
- **Invalid Action**: Error message with proper format instructions

### Visual Indicators
- **Round Warning**: Rounds 4-5 show warning colors (yellow/red)
- **Success States**: Correct answers highlighted in green
- **Error States**: Incorrect answers and invalid actions highlighted in red
- **Loading States**: Smooth loading animations during processing

## Technical Implementation

### Components
- **SearchQAViewer.vue**: Main visualization component with enhanced state management
- **SearchQAClient.js**: Robust client with automatic action tracking and event system

### Enhanced Features
- **Automatic Action Tracking**: Client tracks last action per environment
- **Intelligent Observation Parsing**: Extracts questions, search results, and feedback
- **Event-Driven Architecture**: Real-time updates via client event system
- **Fallback Parsing**: Robust handling when client methods aren't available
- **State Persistence**: Environment state maintained across interactions

### Data Flow
1. User executes action via ActionInput component
2. Client automatically tracks action and stores it
3. Server processes action and returns observation
4. Viewer receives observation and retrieves last action from client
5. Viewer correlates action with response and updates history
6. Visual state updates reflect current progress and status

## Integration

The SearchQA environment is fully integrated into the AgentGym demo system:

1. Listed in the environment selector with proper metadata
2. Accessible via direct URL: `/environment/searchqa`
3. Compatible with the shared ActionInput component
4. Supports all standard environment operations
5. Includes comprehensive error handling and logging

## Getting Started

1. Start the SearchQA server: `searchqa --host 0.0.0.0 --port 36005`
2. Ensure retrieval data is properly configured (index, corpus, model)
3. Navigate to the environment in the demo application
4. Create a new environment instance (optionally specify item ID)
5. Begin interacting with questions and searches

The visualization will automatically track all interactions, provide comprehensive feedback, and monitor progress within the 5-round search limit while maintaining full compatibility with the actual SearchQA server implementation. 