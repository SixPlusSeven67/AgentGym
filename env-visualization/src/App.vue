<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
import { ref, nextTick, onMounted } from 'vue'
import EnvViewer from './shared/components/EnvViewer.vue'
import EnvironmentSelector from './shared/components/EnvironmentSelector.vue'
import InteractionPanel from './shared/components/InteractionPanel.vue'
import SplitPane from './shared/components/SplitPane.vue'
import { getEnvironment, DEFAULT_ENVIRONMENT } from './environments/index.js'

export default {
  name: 'App',
  components: {
    EnvViewer,
    EnvironmentSelector,
    InteractionPanel,
    SplitPane
  },
  setup() {
    // 核心状态
    const environmentId = ref(null)
    const currentEnvironment = ref(null)
    const showEnvironmentSelector = ref(true)
    const isConnected = ref(false)
    
    // 组件引用
    const envViewer = ref(null)
    const interactionPanel = ref(null)
    
    // 交互状态
    const suggestedAction = ref('')
    const currentEnvironmentState = ref(null)

    // 初始化默认环境
    onMounted(() => {
      currentEnvironment.value = getEnvironment(DEFAULT_ENVIRONMENT)
    })

    // 切换环境选择器
    const toggleEnvironmentSelector = () => {
      showEnvironmentSelector.value = !showEnvironmentSelector.value
    }

    // 环境选择处理
    const onEnvironmentSelected = (envConfig) => {
      console.log('Environment selected:', envConfig)
      
      // 重置所有相关状态
      resetSessionState()
      
      // 设置新环境
      currentEnvironment.value = envConfig
      showEnvironmentSelector.value = false
      
      // 清理交互历史
      nextTick(() => {
        clearInteractionHistory()
      })
    }

    // 重置会话状态
    const resetSessionState = () => {
      environmentId.value = null
      suggestedAction.value = ''
      currentEnvironmentState.value = null
      isConnected.value = false
    }

    // 清理交互历史
    const clearInteractionHistory = () => {
      if (interactionPanel.value?.clearHistory) {
        interactionPanel.value.clearHistory()
        console.log('Interaction history cleared')
      }
    }

    // 环境创建处理
    const onEnvironmentCreated = (id) => {
      console.log('🏗️ Environment creation event received:', id, typeof id)
      
      // 确保ID是数字类型
      let numericId
      if (typeof id === 'object') {
        console.error('❌ Received object as environment ID:', id)
        // 尝试从对象中提取ID
        if (id && id.id !== undefined) {
          numericId = parseInt(id.id)
        } else {
          console.error('❌ Cannot extract ID from object:', id)
          return
        }
      } else {
        numericId = parseInt(id)
      }
      
      if (isNaN(numericId)) {
        console.error('❌ Invalid environment ID:', id)
        return
      }
      
      console.log('✅ Setting environment ID to:', numericId)
      environmentId.value = numericId
      isConnected.value = true
      
      console.log('Environment created with ID:', numericId)
    }

    // 环境重置处理
    const onEnvironmentReset = (result) => {
      console.log('Environment reset:', result)
      
      // 清理交互历史
      nextTick(() => {
        clearInteractionHistory()
      })
    }

    // 状态更新处理
    const onStateUpdated = (state) => {
      console.log('State updated:', state)
      currentEnvironmentState.value = state
    }

    // 动作建议处理
    const onSuggestAction = (action) => {
      console.log('Action suggested:', action)
      suggestedAction.value = action
    }

    // 用户动作发送处理
    const onActionSent = (action) => {
      console.log('User action sent:', action)
      // InteractionPanel 会处理显示
    }

    // 响应接收处理
    const onResponseReceived = (response) => {
      console.log('Response received:', response)
      // 触发环境状态刷新
      if (envViewer.value?.refreshState) {
        envViewer.value.refreshState()
      }
    }

    // 自动动作发送处理
    const onAutoActionSent = (action) => {
      console.log('Auto action sent:', action)
      // 转发到交互面板
      if (interactionPanel.value?.addInteraction) {
        interactionPanel.value.addInteraction('action', `[Auto] ${action.action || action}`)
      }
    }

    // 自动响应接收处理
    const onAutoResponseReceived = (response) => {
      console.log('Auto response received:', response)
      
      // 检查是否是完成消息
      const isCompletion = response?.result && 
        typeof response.result === 'string' && (
          response.result.includes('Auto run finished') || 
          response.result.includes('Goal completed') ||
          response.result.includes('Task Completed')
        )
      
      // 转发到交互面板
      if (interactionPanel.value?.addInteraction) {
        interactionPanel.value.addInteraction('response', response, isCompletion)
      }
      
      // 触发状态刷新
      if (envViewer.value?.refreshState) {
        envViewer.value.refreshState()
      }
    }

    // 暴露的方法和状态
    return {
      // 状态
      environmentId,
      currentEnvironment,
      showEnvironmentSelector,
      isConnected,
      suggestedAction,
      currentEnvironmentState,
      
      // 组件引用
      envViewer,
      interactionPanel,
      
      // 方法
      toggleEnvironmentSelector,
      onEnvironmentSelected,
      onEnvironmentCreated,
      onEnvironmentReset,
      onStateUpdated,
      onSuggestAction,
      onActionSent,
      onResponseReceived,
      onAutoActionSent,
      onAutoResponseReceived
    }
  }
}
</script>

<style>
/* Global Styles */
:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  --success-color: #4CAF50;
  --warning-color: #ff9800;
  --danger-color: #f44336;
  --text-color: #333333;
  --background-color: #f5f7fa;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: var(--text-color);
  background-color: var(--background-color);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
}

a {
  text-decoration: none;
  color: var(--primary-color);
}

button {
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
}

/* Utility Classes */
.text-center {
  text-align: center;
}

.mb-1 {
  margin-bottom: 0.5rem;
}

.mb-2 {
  margin-bottom: 1rem;
}

.mb-3 {
  margin-bottom: 1.5rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .hide-mobile {
    display: none;
  }
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>