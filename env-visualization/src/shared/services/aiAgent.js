/**
 * AI Agent Service - 改进版本
 * 
 * 改进了连接处理、action提取逻辑和错误处理
 */

class AIAgentService {
  constructor() {
    this.baseUrl = 'https://dashscope.aliyuncs.com/compatible-mode'
    this.apiKey = 'sk-e846b9e69c9c4e9d8f2364640fa00d0d'
    this.model = "qwen-plus-2025-07-28"
    this.availableModels = []
    this.initialized = false
    this.isAvailable = false
    
    // Conversation management per environment
    this.conversations = new Map()
    this.environmentStates = new Map()
    this.environmentTypes = new Map()  // 新增：跟踪每个环境的类型
    
    // Connection retry configuration
    this.maxRetries = 3
    this.retryDelay = 1000
    this.lastAvailabilityCheck = 0
    this.availabilityCheckInterval = 30000 // 30 seconds
    
    // 防重复调用机制
    this.activeGenerations = new Map() // 跟踪正在进行的生成请求
  }

  /**
   * Initialize the AI service with retry logic
   */
  async initialize() {
    if (this.initialized) return true
    
    // Check if we recently failed
    const now = Date.now()
    if (now - this.lastAvailabilityCheck < this.availabilityCheckInterval && !this.isAvailable) {
      console.log('🔄 Skipping AI initialization - recent failure detected')
      return false
    }
    
    try {
      console.log('🔧 Initializing AI service...')
      
      // First check availability
      this.isAvailable = await this.checkAvailability()
      if (!this.isAvailable) {
        console.warn('⚠️ AI service not available, will use fallback actions')
        this.lastAvailabilityCheck = now
        return false
      }
      
      // const models = await this.getModels()
      // this.availableModels = models
      const models = [{id: "qwen-flash-2025-07-28"}]
      this.availableModels = models
      
      if (models.length > 0) {
        this.model = models[0].id
        console.log(`✅ AI Service initialized with model: ${this.model}`)
        this.initialized = true
        this.isAvailable = true
        return true
      } else {
        console.warn('⚠️ No models available from AI service')
        this.isAvailable = false
        this.lastAvailabilityCheck = now
        return false
      }
    } catch (error) {
      console.error('❌ Failed to initialize AI service:', error)
      this.isAvailable = false
      this.lastAvailabilityCheck = now
      return false
    }
  }

  /**
   * Initialize a new conversation for an environment
   */
  initializeConversation(environmentId, envType, initialObservation, maxRounds = 50) {
    // Ensure we have a valid environment type
    if (!envType || typeof envType !== 'string') {
      // Default to textcraft if no valid environment type is provided
      console.warn(`⚠️ No valid environment type provided, using provided type: ${envType}`)
      envType = envType || 'textcraft'
    }
    
    // 检查该环境ID是否已经有一个对话，如果有，先清除它
    if (this.conversations.has(environmentId)) {
      console.log(`⚠️ Detected existing conversation for environment ${environmentId}, clearing it first`)
      this.clearConversation(environmentId)
    }
    
    // Log the environment type being used
    console.log(`🌟 Initializing AI conversation for environment type: ${envType}`)
    
    const conversation = [
      {
        from: "system",
        loss: null,
        value: this.getSystemPrompt(envType)
      }
    ]
    
    // 检查initialObservation是否有效，并且不要重复添加任务描述和观察结果
    if (initialObservation && initialObservation.trim()) {
      // 处理可能的重复内容（例如，当任务描述和初始观察同时存在时）
      const cleanedObservation = this.removePossibleDuplicateContent(initialObservation);
      
      conversation.push({
        from: "human", 
        loss: null,
        value: cleanedObservation
      })
    }
    
    const envState = {
      reward: 0.0,
      done: false,
      rounds: 0,
      maxRounds: maxRounds,
      maxLength: 4096,
      fallbackMode: false
    }
    
    this.conversations.set(environmentId, conversation)
    this.environmentStates.set(environmentId, envState)
    this.environmentTypes.set(environmentId, envType) // 记录环境类型
    
    console.log(`🎯 Initialized conversation for environment ${environmentId} (${envType})`)
    return { conversation, envState }
  }
  
  /**
   * 处理可能的重复内容，移除重复的任务描述等
   */
  removePossibleDuplicateContent(text) {
    if (!text) return '';
    
    // // 如果文本中有多个任务描述（例如SciWorld中的"Your task is to..."），只保留一个
    // const taskPattern = /Your task is to [^\.]+\./gi;
    // const taskMatches = text.match(taskPattern) || [];
    
    // if (taskMatches.length > 1) {
    //   console.log(`⚠️ Detected ${taskMatches.length} task descriptions, keeping only one`);
    //   let cleanedText = text;
      
    //   // 保留第一个任务描述，移除其余的
    //   for (let i = 1; i < taskMatches.length; i++) {
    //     cleanedText = cleanedText.replace(taskMatches[i], '');
    //   }
      
    //   return cleanedText.replace(/\n\s*\n\s*\n/g, '\n\n').trim();
    // }
    
    return text;
  }

  /**
   * Generate next action using conversation-based approach - 改进版本
   */
  async generateNextAction(environmentId, currentObservation) {
    console.log(`🤖 Generating next action for environment ${environmentId}`)
    
    // 防重复调用机制 - 检查是否已有正在进行的生成请求
    if (this.activeGenerations.has(environmentId)) {
      console.log(`⚠️ Generation already in progress for environment ${environmentId}, skipping`)
      return {
        action: null,
        done: false,
        shouldStop: false,
        reason: 'Generation already in progress',
        source: 'duplicate_prevention'
      }
    }
    
    // 标记正在生成
    this.activeGenerations.set(environmentId, Date.now())
    
    try {
      // Ensure currentObservation is a string
      const observationStr = typeof currentObservation === 'string' 
        ? currentObservation 
        : JSON.stringify(currentObservation || {})
      
      console.log(`📝 Current observation:`, observationStr?.substring(0, 200) + '...')
      
      let conversation = this.conversations.get(environmentId)
      let envState = this.environmentStates.get(environmentId)
      let envType = this.environmentTypes.get(environmentId) // 获取环境类型
      
      if (!conversation || !envState) {
        console.warn(`⚠️ No conversation initialized for environment ${environmentId}, initializing now`)
        // Get the environment type from EnvViewer component context if possible
        const defaultEnvType = window?.currentEnvironmentType || 'sciworld'; // Default to sciworld if we can't determine type
        console.log(`🔍 Detected environment type for auto-initialization: ${defaultEnvType}`);
        const result = this.initializeConversation(environmentId, defaultEnvType, observationStr)
        conversation = result.conversation
        envState = result.envState
        // 重新获取环境类型，因为initializeConversation已经设置了环境类型
        envType = this.environmentTypes.get(environmentId)
      }

      console.log(`🔍 Environment type: ${envType}`)

      // Check if we should stop
      if (envState.done || envState.rounds >= envState.maxRounds) {
        return {
          action: null,
          done: true,
          shouldStop: true,
          reason: envState.done ? 'Task completed' : 'Max rounds reached'
        }
      }

      // Try AI generation first if available
      if (!envState.fallbackMode) {
        try {
          const success = await this.initialize()
          if (success && this.isAvailable) {
            return await this.generateActionWithAI(environmentId, currentObservation, conversation, envState, envType)
          } else {
            console.log('🔄 AI service unavailable, switching to fallback mode')
            envState.fallbackMode = true
          }
        } catch (error) {
          console.error('❌ AI generation failed, switching to fallback mode:', error)
          envState.fallbackMode = true
        }
      }

      // Use fallback logic
      return this.generateFallbackAction(environmentId, currentObservation, conversation, envState, envType)
    } finally {
      // 清除正在生成的标记
      this.activeGenerations.delete(environmentId)
    }
  }

  /**
   * Generate action using AI
   */
  async generateActionWithAI(environmentId, currentObservation, conversation, envState, envType) {
    try {
      // Add current observation to conversation if it's not the first round
      if (envState.rounds > 0) {
        conversation.push({
          from: "human",
          loss: null,
          value: currentObservation
        })
      }

      console.log(`🗣️ Sending conversation to AI API (${conversation.length} messages)`)
      
      // Generate action using conversation
      const generatedText = await this.generateFromConversation(conversation)
      console.log(`🎯 Raw AI response:`, generatedText?.substring(0, 200) + '...')
      
      // Extract action with improved logic - 跳过webarena环境的action提取
      let extractedAction
      console.log(`🔍 Environment type: ${envType}`)
      if (envType === 'webarena' || envType === 'searchqa' || envType === 'sciworld') {
        console.log(`🌐 WebArena environment detected - using raw response as action`)
        extractedAction = generatedText.trim()
      } else {
        extractedAction = this.extractActionImproved(generatedText)
        console.log(`⚡ Extracted action:`, extractedAction)
        
        if (!extractedAction || extractedAction.trim().length === 0) {
          console.warn(`⚠️ No valid action extracted from AI response`)
          throw new Error(`No valid action extracted from AI response`)
        }
      }
      
      // Add generated action to conversation
      conversation.push({
        from: "gpt",
        loss: true,
        value: generatedText
      })

      // Update round count
      envState.rounds += 1

      console.log(`✅ Generated AI action for env ${environmentId}, round ${envState.rounds}: "${extractedAction}"`)

      return {
        action: extractedAction,
        done: false,
        shouldStop: false,
        round: envState.rounds,
        rawResponse: generatedText,
        source: 'ai'
      }

    } catch (error) {
      console.error(`❌ AI action generation failed:`, error)
      // Don't switch to fallback immediately, let the caller decide
      throw error
    }
  }

  /**
   * Generate fallback action when AI is not available
   */
  generateFallbackAction(environmentId, currentObservation, conversation, envState, envType) {
    console.log(`🔄 Generating fallback action for env ${environmentId}, round ${envState.rounds}`)
    
    const fallbackAction = this.getFallbackActionImproved(currentObservation, envState.rounds, envType)
    
    console.log(`🔄 Using fallback action: "${fallbackAction}"`)
    
    // Add fallback action to conversation
    conversation.push({
      from: "human",
      loss: null,
      value: currentObservation
    })
    
    conversation.push({
      from: "gpt", 
      loss: true,
      value: `Fallback action: ${fallbackAction}`
    })
    
    envState.rounds += 1
    
    return {
      action: fallbackAction,
      done: false,
      shouldStop: false,
      round: envState.rounds,
      isFallback: true,
      source: 'fallback'
    }
  }

  /**
   * 改进的动作提取逻辑
   */
  extractActionImproved(text) {
    if (!text || typeof text !== 'string') {
      console.warn('⚠️ Invalid text for action extraction:', text)
      return null
    }

    console.log(`🔍 Extracting action from text: "${text.substring(0, 200)}..."`)

    // Remove potential EOS tokens
    let cleanText = text.trim()
    if (cleanText.endsWith("</s>")) {
      cleanText = cleanText.slice(0, -4).trim()
    }

    // 尝试多种提取模式，按优先级排序
    const patterns = [
      // 1. 标准的 "Action:" 格式
      {
        regex: /Action:\s*([^\n\r]+)/i,
        name: "Action: format"
      },
      // 2. 在代码块中的动作
      {
        regex: /```([^`\n\r]+)```/,
        name: "Code block format"
      },
      // 3. 引号包围的动作
      {
        regex: /"([^"\n\r]+)"/,
        name: "Quoted format"
      },
      // 4. 以动作词开始的行
      {
        regex: /^(get|craft|inventory|look|move|turn|pickup|open|go|search|click|type|examine|focus|wait|task)[^\n\r]*/im,
        name: "Command-like format"
      },
      // 5. 多行中寻找动作词
      {
        regex: /(?:^|\n)\s*((?:get|craft|inventory|look|move|turn|pickup|open|go|search|click|type|examine|focus|wait|task)[^\n\r]*)/im,
        name: "Multi-line command format"
      },
      // 6. 简单的第一行提取
      {
        regex: /^([^\n\r]+)/,
        name: "First line fallback"
      }
    ]

    for (const pattern of patterns) {
      const match = cleanText.match(pattern.regex)
      if (match && match[1]) {
        let action = match[1].trim()
        
        // 清理提取的动作
        action = action
          .replace(/^(Command:|Next:|I suggest:|Try:|You should:|I will|Let me|The action is:)\s*/i, '')
          .replace(/^["'`]/, '')
          .replace(/["'`]$/, '')
          .replace(/\.$/, '')
          .trim()

        // 验证动作的有效性
        if (this.isValidAction(action)) {
          console.log(`✅ Action extracted using ${pattern.name}: "${action}"`)
          return action
        } else {
          console.log(`⚠️ Invalid action from ${pattern.name}: "${action}"`)
        }
      }
    }

    console.warn(`❌ No valid action found in text: "${cleanText}"`)
    return null
  }

  /**
   * 验证动作的有效性
   */
  isValidAction(action) {
    if (!action || typeof action !== 'string') return false
    
    const trimmed = action.trim()
    if (trimmed.length < 2) return false
    if (trimmed.length > 200) return false
    
    // 检查是否包含明显的非动作内容
    const invalidPatterns = [
      /^(thought|thinking|i think|let me think)/i,
      /^(the|this|that|it|there)/i,
      /^(based on|according to|given)/i,
      /\?\s*$/,  // 以问号结尾
    ]
    
    for (const pattern of invalidPatterns) {
      if (pattern.test(trimmed)) {
        return false
      }
    }
    
    return true
  }

  /**
   * 改进的fallback动作生成
   */
  getFallbackActionImproved(observation, rounds, envType) {
    const obsLower = observation ? observation.toLowerCase() : ''
    
    console.log(`🔄 Generating fallback action for round ${rounds} in environment type: ${envType}`)
    
    // TextCraft specific fallbacks based on observation content
    if (envType === 'textcraft') {
      if (obsLower.includes('craft') || obsLower.includes('minecraft')) {
        // Check if we need ingredients
        if (obsLower.includes('goal:')) {
          const goalMatch = obsLower.match(/goal:\s*(.+?)(?:\n|$)/i)
          if (goalMatch) {
            const goal = goalMatch[1].trim()
            if (goal.includes('beacon')) {
              const beaconActions = ['get 1 nether star', 'get 5 glass', 'get 3 obsidian', 'craft 1 beacon using 1 nether star, 5 glass, 3 obsidian']
              return beaconActions[rounds % beaconActions.length]
            }
            if (goal.includes('planks')) {
              const planksActions = ['get 1 acacia logs', 'craft 4 acacia planks using 1 acacia logs']
              return planksActions[rounds % planksActions.length]
            }
          }
        }
        
        // Generic TextCraft actions
        const textcraftActions = ['inventory', 'get 1 wood', 'get 1 stone', 'look around']
        return textcraftActions[rounds % textcraftActions.length]
      }
    }
    
    // BabyAI specific fallbacks
    if (envType === 'babyai') {
      if (obsLower.includes('door') && obsLower.includes('closed')) {
        return 'toggle'
      }
      if (obsLower.includes('key')) {
        return 'pickup key'
      }
      if (obsLower.includes('ball')) {
        return 'go to ball'
      }
    }
    
    // SciWorld specific fallbacks
    if (envType === 'sciworld') {
      if (obsLower.includes('task')) {
        return 'task'
      }
    }
    
    // Generic fallbacks based on round number
    const genericActions = [
      'inventory',
      'look around', 
      'examine room',
      'wait1',
      'move forward'
    ]
    
    return genericActions[rounds % genericActions.length]
  }

  /**
   * Generate action from conversation using AI API
   */
  async generateFromConversation(conversation) {
    const messages = conversation.map(msg => {
      if (msg.from === "system") {
        return { role: "system", content: msg.value }
      } else if (msg.from === "human") {
        return { role: "user", content: msg.value }
      } else if (msg.from === "gpt") {
        return { role: "assistant", content: msg.value }
      }
      return { role: "user", content: msg.value }
    })
    
    // 简化日志输出，避免在页面上显示消息对象
    console.log('🤖 AI Agent API request:', {
      model: this.model,
      messages: messages
    })
    
    try {
      const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model: this.model,
          messages: messages,
          max_tokens: 1024,
          temperature: 0.6,
          chat_template_kwargs: {"enable_thinking": false}
        })
      })

      if (!response.ok) {
        throw new Error(`AI API request failed: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      
      if (!data.choices || !data.choices[0] || !data.choices[0].message) {
        throw new Error('Invalid response from AI API')
      }

      const generatedText = data.choices[0].message.content.trim()
      console.log('🎯 AI API response received:', generatedText.substring(0, 100) + '...')
      
      return generatedText
    } catch (error) {
      console.error('❌ Error in generateFromConversation:', error)
      throw error
    }
  }

  /**
   * Update environment state after step execution
   */
  updateEnvironmentState(environmentId, stepResponse, reward = 0, done = false) {
    const envState = this.environmentStates.get(environmentId)
    
    if (!envState) {
      console.warn(`⚠️ No state found for environment ${environmentId}`)
      return
    }

    envState.reward += reward
    envState.done = done

    console.log(`📊 Updated env ${environmentId}: rounds=${envState.rounds}, reward=${envState.reward}, done=${done}`)
  }

  /**
   * Reset conversation for an environment
   */
  resetConversation(environmentId, envType, newObservation) {
    return this.initializeConversation(environmentId, envType, newObservation)
  }

  /**
   * Get environment-specific system prompt
   */
  getSystemPrompt(envType) {
    switch (envType) {
      case 'textcraft':
        return 'You are given few useful crafting recipes to craft items in Minecraft. Crafting commands are of the format "craft [target object] using [input ingredients]".\nEvery round I will give you an observation, you have to respond an action based on the state and instruction. You can "get" an object (ingredients) from the inventory or the environment, look-up the game inventory by "inventory", or "craft" (target) using any of the crafting commands.\nYour output must strictly follow this format:"Thought:\nyour thoughts.\n\nAction:\nyour next action"\n\nReminder: \n1. Always specify the quantity when using "get" and "craft" commands. - Example of get: get 1 lapis lazuli - Example1 of craft: craft 1 blue dye using 1 lapis lazuli - Example2 of craft: craft 1 golden carrot using 8 gold nugget, 1 carrot\n2. When using "get" command, do not specify whether the item comes from the inventory or the environment.\n3. You can use ONLY crafting commands provided, do not use your own crafting commands. However, if the crafting command uses a generic ingredient like "planks", you can use special types of the same ingredient e.g. "dark oak planks" in the command instead.\n\n';

      case 'babyai':
        return 'You are an exploration master that wants to finish every goal you are given. Every round I will give you an observation, and you have to respond an action and your thought based on the observation to finish the given task. You are placed in a room and you need to accomplish the given goal with actions.\n\nYou can use the following actions: \n\n- turn right \n\n- turn left \n\n- move forward \n\n- go to <obj> <id> \n\n- pick up <obj> <id> \n\n- go through <door> <id>: <door> must be an open door. \n\n- toggle and go through <door> <id>: <door> can be a closed door or a locked door. If you want to open a locked door, you need to carry a key that is of the same color as the locked door. \n\n- toggle: there is a closed or locked door right in front of you and you can toggle it.\nYour response should use the following format:\nThought:\n<Your Thought>\n\nAction:\n<Your Action>'

      case 'sciworld':
        return 'You are an agent for science world. Every round I will give you an observation, you have to respond an action based on the observation to finish the given task. Here are the actions you may take: [{"action": "open/close OBJ", "description": "open/close a container"}, {"action": "de/activate OBJ", "description": "activate/deactivate a device"}, {"action": "connect OBJ to OBJ", "description": "connect electrical components"}, {"action": "disconnect OBJ", "description": "disconnect electrical components"}, {"action": "use OBJ [on OBJ]", "description": "use a device/item"}, {"action": "look around", "description": "describe the current room"}, {"action": "look at OBJ", "description": "describe an object in detail"}, {"action": "look in OBJ", "description": "describe a container\'s contents"}, {"action": "read OBJ", "description": "read a note or book"}, {"action": "move OBJ to OBJ", "description": "move an object to a container"}, {"action": "pick up OBJ", "description": "move an object to the inventory"}, {"action": "put down OBJ", "description": "drop an inventory item"}, {"action": "pour OBJ into OBJ", "description": "pour a liquid into a container"}, {"action": "dunk OBJ into OBJ", "description": "dunk a container into a liquid"}, {"action": "mix OBJ", "description": "chemically mix a container"}, {"action": "go to LOC", "description": "move to a new location"}, {"action": "eat OBJ", "description": "eat a food"}, {"action": "flush OBJ", "description": "flush a toilet"}, {"action": "focus on OBJ", "description": "signal intent on a task object"}, {"action": "wait", "description": "take no action for 10 iterations"}, {"action": "wait1", "description": "take no action for 1 iteration"}, {"action":"examine OBJ","description":"provides a description of the objects present on or in a receptacle."}, {"action": "task", "description": "describe current task"}, {"action": "inventory", "description": "list your inventory"}]\nYour response should use the following format:\nThought:\nyour thoughts.\n\nAction:\nyour next action'

      case 'webarena':
        return `You are an autonomous intelligent agent tasked with navigating a web browser. You will be given web-based tasks. These tasks will be accomplished through the use of specific actions you can issue.

Here's the information you'll have:
The user's objective: This is the task you're trying to complete.
The current web page's accessibility tree: This is a simplified representation of the webpage, providing key information.
The current web page's URL: This is the page you're currently navigating.
The open tabs: These are the tabs you have open.
The previous action: This is the action you just performed. It may be helpful to track your progress.

The actions you can perform fall into several categories:

Page Operation Actions:
\`\`\`click [id]\`\`\`: This action clicks on an element with a specific id on the webpage.
\`\`\`type [id] [content] [0|1]\`\`\`: Use this to type the content into the field with id. By default, the "Enter" key is pressed after typing unless the last parameter is set to 0.
\`\`\`hover [id]\`\`\`: Hover over an element with id.
\`press [key_comb]\`:  Simulates the pressing of a key combination on the keyboard (e.g., Ctrl+v).
\`\`\`scroll [down|up]\`\`\`: Scroll the page up or down to reveal content below or above the current view.

Tab Management Actions:
\`\`\`new_tab\`\`\`: Open a new, empty browser tab.
\`\`\`tab_focus [tab_index]\`\`\`: Switch the browser's focus to a specific tab using its index.
\`\`\`close_tab\`\`\`: Close the currently active tab.

URL Navigation Actions:
\`\`\`goto [url]\`\`\`: Navigate to a specific URL.
\`\`\`go_back\`\`\`: Navigate to the previously viewed page.
\`\`\`go_forward\`\`\`: Navigate to the next page (if a previous 'go_back' action was performed).

Completion Action:
\`\`\`stop [answer]\`\`\`: Issue this action when you believe the task is complete. If the objective is to find a text-based answer, provide the answer in the bracket. If you believe the task is impossible to complete, provide the answer as "N/A" in the bracket.

Homepage:
If you want to visit other websites, check out the homepage at http://homepage.com. It has a list of websites you can visit.

To be successful, it is very important to follow the following rules:
1. You should only issue an action that is valid given the current observation
2. You should only issue one action at a time.
3. You should follow the examples to reason step by step and then issue the next action.
4. For ALL actions that take parameters, you MUST enclose each parameter in square brackets [].
5. Generate the action in the correct format. Start with a "Let's think step-by-step...In summary, the next action I will perform is" phrase, followed by action inside triple backticks (\`\`\`).
   For example, "Let's think step-by-step. This page has a search box whose ID is [164]. According to the nominatim rule of openstreetmap, I can search for the restaurants near a location by 'restaurants near'. I can submit my typing by pressing the Enter afterwards. In summary, the next action I will perform is \`\`\`type [164] [restaurants near CMU] [1]\`\`\`".
6. Issue stop action when you think you have achieved the objective. Don't generate anything after stop.`;
      case 'searchqa':
        return `You must always reason inside <think>...</think> first; if you lack knowledge, issue a <search>...</search> and then stop; do not generate <information> or <answer> yet; wait for external input between <information>...</information> before continuing; resume only when new <information> is given; do not skip steps or anticipate answers early.`;
      default:
        return 'You are an AI agent. Analyze the current situation and suggest the next best action. Your output must strictly follow this format:"Thought:\nyour thoughts.\n\nAction:\nyour next action"'
    }
  }

  /**
   * Check if AI service is available with timeout
   */
  async checkAvailability() {
    console.log('🔍 Checking AI service availability...')
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
      
      const response = await fetch(`${this.baseUrl}/v1/models`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      const isAvailable = response.ok
      console.log('✅ AI service availability:', isAvailable)
      return isAvailable
    } catch (error) {
      if (error.name === 'AbortError') {
        console.warn('❌ AI service check timed out')
      } else {
        console.warn('❌ AI service not available:', error.message)
      }
      return false
    }
  }

  async getModels() {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout
      
      const response = await fetch(`${this.baseUrl}/v1/models`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`Failed to get models: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      return data.data || []
    } catch (error) {
      console.error('Error getting models:', error)
      throw error
    }
  }

  clearConversation(environmentId) {
    this.conversations.delete(environmentId)
    this.environmentStates.delete(environmentId)
    this.environmentTypes.delete(environmentId) // 清除环境类型
    this.activeGenerations.delete(environmentId) // 清除正在生成的标记
    console.log(`🧹 Cleared conversation for environment ${environmentId}`)
  }

  /**
   * Get current status
   */
  getStatus() {
    return {
      initialized: this.initialized,
      isAvailable: this.isAvailable,
      model: this.model,
      availableModels: this.availableModels,
      activeConversations: this.conversations.size,
      activeGenerations: this.activeGenerations.size,
      environmentTypes: Array.from(this.environmentTypes.entries()),
      lastAvailabilityCheck: this.lastAvailabilityCheck
    }
  }
}

// Export singleton instance
export default new AIAgentService()