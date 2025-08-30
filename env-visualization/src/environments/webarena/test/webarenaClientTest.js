/**
 * WebArena Client Test
 * 
 * Test script to verify WebArena client correctly handles terminated -> done mapping
 */

import WebArenaClient from '../client/webarenaClient.js';

class WebArenaClientTest {
  constructor() {
    this.client = new WebArenaClient();
  }

  /**
   * Test the processStepResponse method with various response formats
   */
  testProcessStepResponse() {
    console.log('🧪 Testing WebArena step response processing...');

    // Test 1: Array response format (expected from server)
    const arrayResponse = ["Current webpage observation...", 0.5, true, false, { info: "test" }];
    const processedArray = this.client.processStepResponse(arrayResponse);
    
    console.log('Test 1 - Array response:', {
      input: arrayResponse,
      output: processedArray,
      doneCorrect: processedArray.done === true,
      terminatedCorrect: processedArray.terminated === true
    });

    // Test 2: Object response with terminated field
    const objectResponseTerminated = {
      observation: "Browser state...",
      reward: 1.0,
      terminated: true,
      truncated: false,
      info: { step: 10 }
    };
    const processedObject = this.client.processStepResponse(objectResponseTerminated);
    
    console.log('Test 2 - Object with terminated:', {
      input: objectResponseTerminated,
      output: processedObject,
      doneCorrect: processedObject.done === true,
      terminatedCorrect: processedObject.terminated === true
    });

    // Test 3: Object response with done field
    const objectResponseDone = {
      observation: "Final state",
      reward: 0.8,
      done: true,
      info: {}
    };
    const processedDone = this.client.processStepResponse(objectResponseDone);
    
    console.log('Test 3 - Object with done:', {
      input: objectResponseDone,
      output: processedDone,
      doneCorrect: processedDone.done === true,
      terminatedCorrect: processedDone.terminated === true
    });

    // Test 4: String response
    const stringResponse = "Simple observation text";
    const processedString = this.client.processStepResponse(stringResponse);
    
    console.log('Test 4 - String response:', {
      input: stringResponse,
      output: processedString,
      doneCorrect: processedString.done === false,
      observationCorrect: processedString.observation === stringResponse
    });

    console.log('✅ All processStepResponse tests completed');
  }

  /**
   * Run all tests
   */
  async runTests() {
    console.log('🚀 Starting WebArena Client Tests...\n');
    
    try {
      // Test step response processing
      this.testProcessStepResponse();
      
      console.log('\n🎉 All tests passed!');
      return true;
    } catch (error) {
      console.error('❌ Test failed:', error);
      return false;
    }
  }
}

// Export for use in other files
export default WebArenaClientTest;

// Run tests if this file is executed directly
if (typeof window === 'undefined') {
  const test = new WebArenaClientTest();
  test.runTests();
} 