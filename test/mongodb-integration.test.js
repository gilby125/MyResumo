// MongoDB Integration Tests
const { MongoClient } = require('mongodb');
const assert = require('assert');

// Connection URL
const MONGODB_HOST = process.env.MONGODB_HOST || '192.168.7.10';
const MONGODB_PORT = process.env.MONGODB_PORT || '27017';
const MONGODB_URL = `mongodb://${MONGODB_HOST}:${MONGODB_PORT}`;
const DB_NAME = process.env.DB_NAME || 'myresumo';

describe('MongoDB Integration Tests', () => {
  let client;
  
  // Connect to MongoDB before running tests
  before(async () => {
    console.log(`Connecting to MongoDB at ${MONGODB_URL}`);
    client = new MongoClient(MONGODB_URL);
    await client.connect();
    console.log('Connected to MongoDB');
  });
  
  // Close the connection after tests
  after(async () => {
    if (client) {
      await client.close();
      console.log('MongoDB connection closed');
    }
  });
  
  it('should connect to MongoDB server', async () => {
    const admin = client.db('admin').admin();
    const serverInfo = await admin.serverInfo();
    console.log(`MongoDB server version: ${serverInfo.version}`);
    assert.ok(serverInfo.version, 'Server version should be available');
  });
  
  it('should list available databases', async () => {
    const admin = client.db('admin').admin();
    const dbs = await admin.listDatabases();
    const databases = dbs.databases.map(db => db.name);
    console.log('Available databases:', databases);
    assert.ok(databases.includes(DB_NAME), `Database '${DB_NAME}' should exist`);
  });
  
  it('should list collections in the myresumo database', async () => {
    const db = client.db(DB_NAME);
    const collections = await db.listCollections().toArray();
    const collectionNames = collections.map(col => col.name);
    console.log(`Collections in '${DB_NAME}' database:`, collectionNames);
    assert.ok(collectionNames.includes('resumes'), 'Resumes collection should exist');
    assert.ok(collectionNames.includes('prompts'), 'Prompts collection should exist');
  });
  
  it('should verify resume collection schema', async () => {
    const db = client.db(DB_NAME);
    const collection = db.collection('resumes');
    const sampleDoc = await collection.findOne({});
    assert.ok(sampleDoc, 'Should retrieve a sample resume document');
    const fields = Object.keys(sampleDoc);
    console.log('Resume document fields:', fields);
    assert.ok(fields.includes('_id'), 'Resume document should have _id field');
    assert.ok(fields.includes('title'), 'Resume document should have title field');
    assert.ok(fields.includes('original_content'), 'Resume document should have original_content field');
  });
  
  it('should verify prompts collection schema', async () => {
    const db = client.db(DB_NAME);
    const collection = db.collection('prompts');
    const sampleDoc = await collection.findOne({});
    assert.ok(sampleDoc, 'Should retrieve a sample prompt document');
    const fields = Object.keys(sampleDoc);
    console.log('Prompt document fields:', fields);
    assert.ok(fields.includes('_id'), 'Prompt document should have _id field');
    assert.ok(fields.includes('name'), 'Prompt document should have name field');
    assert.ok(fields.includes('template'), 'Prompt document should have template field');
  });
});