# WebArena Environment

WebArena is a web-based environment that allows agents to navigate and interact with web pages.

## Special Handling

### Terminated vs Done

**Important:** WebArena differs from other AgentGym environments in its response format:

- **Other environments** use a `done` field to indicate environment completion
- **WebArena** uses a `terminated` field to indicate environment completion

The WebArenaClient automatically handles this difference by:
1. Mapping `terminated` → `done` for consistency with the AgentGym interface
2. Preserving both fields in the response object for compatibility

### Response Format

WebArena server returns step responses as a tuple:
```python
(prompt, reward, terminated, truncated, info)
```

The client processes this into a standardized format:
```javascript
{
  observation: prompt,
  reward: reward,
  done: terminated,        // Mapped for consistency
  terminated: terminated,  // Original field preserved
  truncated: truncated,
  info: info
}
```

## Usage

```javascript
import { createWebArenaClient } from './webarena/index.js';

const client = createWebArenaClient();

// Create environment
const result = await client.createEnvironment();
const envId = result.data.id;

// Execute action
const stepResult = await client.step(envId, "click[123]");

// Check if done (works consistently with other environments)
if (stepResult.data.done) {
  console.log('Task completed!');
}
```

## Testing

Run the test suite to verify the terminated → done mapping:

```javascript
import WebArenaClientTest from './test/webarenaClientTest.js';

const test = new WebArenaClientTest();
await test.runTests();
```

## Configuration

Default server URL: `http://localhost:36008`

The client connects to the WebArena server which should be running the `WebarenaEnvServer` class. 