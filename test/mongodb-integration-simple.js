// Simple MongoDB Integration Tests
const { MongoClient } = require('mongodb');
const assert = require('assert');

// Connection URL
const MONGODB_HOST = process.env.MONGODB_HOST || '192.168.7.10';
const MONGODB_PORT = process.env.MONGODB_PORT || '27017';
const MONGODB_URL = `mongodb://${MONGODB_HOST}:${MONGODB_PORT}`;
const DB_NAME = process.env.DB_NAME || 'myresumo';

async function runTests() {
  console.log('=== MongoDB Integration Tests ===');
  console.log(`Connecting to MongoDB at ${MONGODB_URL}`);
  
  let client;
  try {
    // Connect to MongoDB
    client = new MongoClient(MONGODB_URL);
    await client.connect();
    console.log('✅ Connected to MongoDB');
    
    // Test 1: Connect to MongoDB server
    console.log('\nTest 1: Connect to MongoDB server');
    const admin = client.db('admin').admin();
    const serverInfo = await admin.serverInfo();
    console.log(`MongoDB server version: ${serverInfo.version}`);
    assert.ok(serverInfo.version, 'Server version should be available');
    console.log('✅ Test 1 passed');
    
    // Test 2: List available databases
    console.log('\nTest 2: List available databases');
    const dbs = await admin.listDatabases();
    const databases = dbs.databases.map(db => db.name);
    console.log('Available databases:', databases);
    assert.ok(databases.includes(DB_NAME), `Database '${DB_NAME}' should exist`);
    console.log('✅ Test 2 passed');
    
    // Test 3: List collections in the myresumo database
    console.log('\nTest 3: List collections in the myresumo database');
    const db = client.db(DB_NAME);
    const collections = await db.listCollections().toArray();
    const collectionNames = collections.map(col => col.name);
    console.log(`Collections in '${DB_NAME}' database:`, collectionNames);
    assert.ok(collectionNames.includes('resumes'), 'Resumes collection should exist');
    assert.ok(collectionNames.includes('prompts'), 'Prompts collection should exist');
    console.log('✅ Test 3 passed');
    
    // Test 4: Verify resume collection schema
    console.log('\nTest 4: Verify resume collection schema');
    const resumesCollection = db.collection('resumes');
    const sampleResume = await resumesCollection.findOne({});
    assert.ok(sampleResume, 'Should retrieve a sample resume document');
    const resumeFields = Object.keys(sampleResume);
    console.log('Resume document fields:', resumeFields);
    assert.ok(resumeFields.includes('_id'), 'Resume document should have _id field');
    assert.ok(resumeFields.includes('title'), 'Resume document should have title field');
    assert.ok(resumeFields.includes('original_content'), 'Resume document should have original_content field');
    console.log('✅ Test 4 passed');
    
    // Test 5: Verify prompts collection schema
    console.log('\nTest 5: Verify prompts collection schema');
    const promptsCollection = db.collection('prompts');
    const samplePrompt = await promptsCollection.findOne({});
    assert.ok(samplePrompt, 'Should retrieve a sample prompt document');
    const promptFields = Object.keys(samplePrompt);
    console.log('Prompt document fields:', promptFields);
    assert.ok(promptFields.includes('_id'), 'Prompt document should have _id field');
    assert.ok(promptFields.includes('name'), 'Prompt document should have name field');
    assert.ok(promptFields.includes('template'), 'Prompt document should have template field');
    console.log('✅ Test 5 passed');
    
    console.log('\n=== All tests passed ===');
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Error details:', error);
    process.exit(1);
  } finally {
    // Close the connection
    if (client) {
      await client.close();
      console.log('MongoDB connection closed');
    }
  }
}

// Run the tests
runTests().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
});