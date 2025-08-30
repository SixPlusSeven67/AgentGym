# SciWorld 2D Visualization Environment

A 2D top-down game-style visualization for the ScienceWorld environment, inspired by classic adventure games.

## 🎮 Features

### 🗺️ **2D Game-Style World Map**
- **Grid-based Layout**: Organized room layout similar to classic RPG games
- **Multiple Rooms**: 11 predefined rooms including:
  - 🏠 Outside
  - ⚒️ Foundry  
  - 🌱 Greenhouse
  - 🔧 Workshop
  - 🎨 Art Room
  - 🛋️ Living Room
  - 🍳 Kitchen
  - 🚿 Bathroom
  - 🛏️ Bedroom
  - 🧪 Laboratory
  - 📦 Storage

### 🤖 **Agent Tracking**
- **Real-time Position**: Agent position updates based on ScienceWorld observations
- **Visual Feedback**: Current room highlighted with yellow border
- **Movement Animation**: Smooth agent repositioning with pulse animation

### 📍 **Interactive Elements**
- **Room Interaction**: Click on rooms for selection
- **Object Visualization**: Interactive objects displayed within rooms
- **Dynamic Rooms**: Automatically adds new rooms detected from environment

### 🎯 **Smart Data Parsing**
- **Text Analysis**: Extracts location from observation text using multiple patterns
- **Room Mapping**: Maps variations (lab → laboratory, kitchen → kitchen, etc.)
- **Object Detection**: Parses object tree data (JSON or text format)

## 🔧 Technical Implementation

### **Event-Driven Updates**
No polling! Updates only when:
- Environment resets
- Agent takes actions  
- State changes detected

### **ScienceWorld API Integration**
Supports all ScienceWorld methods:
- `getObjectTree()` - Room and object structure
- `look()` - Current observation (location parsing)
- `inventory()` - Agent inventory
- `step()` - Action results
- `get_task_description()` - Task info

### **Responsive Design**
- SVG-based rendering (scalable)
- Grid layout (720x450 viewBox)
- Mobile-friendly interface

## 📋 Usage

```vue
<SciWorldViewer 
  :environment-id="envId"
  :client="sciworldClient"
  :env-state="currentState"
  @state-updated="onStateUpdate"
  @agent-moved="onAgentMove"
  @room-selected="onRoomClick"
/>
```

### **Events**
- `state-updated`: Emitted when environment state changes
- `agent-moved`: Emitted when agent moves between rooms
- `room-selected`: Emitted when user clicks a room

### **Props**
- `environment-id`: Current environment ID
- `client`: SciWorldClient instance  
- `env-state`: Current environment state

## 🎨 Visual Design

### **Room Layout**
```
[Outside]  [Art]     [Workshop] [Living]
[Foundry]  [Hallway] [Greenhouse] [Bathroom]
[Storage]  [Laboratory] [Kitchen] [Bedroom]
```

**Hallway** is the central hub connecting to all other rooms, matching ScienceWorld's design.

### **Color Coding**
- 🟫 Workshop/Storage: Brown tones
- 🟢 Greenhouse: Green
- 🔴 Kitchen: Warm orange  
- 🔵 Bathroom: Light blue
- 🟣 Bedroom: Purple
- 🟡 Living: Yellow
- 🎨 Art: Pink
- ⚫ Outside: Dark green

### **Agent Representation**
- 🤖 Robot emoji
- Red circle with white border
- Pulse animation
- Positioned in current room center (with random offset)

## 🔄 State Updates

The component automatically handles:

1. **Location Detection**: Parses observation text for room names
2. **Room Validation**: Checks against known rooms
3. **Dynamic Addition**: Creates new rooms if detected
4. **Agent Positioning**: Updates robot position in current room
5. **Object Display**: Shows interactive objects within rooms

## 🎯 Smart Location Parsing

Recognizes patterns like:
- "You are in the laboratory"
- "Looking around, you see: kitchen"  
- "Current location: workshop"
- "moved to bathroom"
- Room names at line start

## 📱 Responsive Features

- Hover effects on rooms and objects
- Click interactions
- Smooth animations
- Grid-based organization
- Walkable paths between rooms

This creates an immersive, game-like experience for navigating ScienceWorld environments! 