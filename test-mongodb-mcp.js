// Test MongoDB connection using MCP tools
const { MongoClient } = require('mongodb');

// Connection URL
const MONGODB_HOST = '192.168.7.10';
const MONGODB_PORT = '27017';
const MONGODB_URL = `mongodb://${MONGODB_HOST}:${MONGODB_PORT}`;
const DB_NAME = 'myresumo';

// Function to test MongoDB connection
async function testMongoDBConnection() {
  console.log(`Testing MongoDB connection to ${MONGODB_URL}`);
  
  try {
    // Connect to MongoDB
    const client = new MongoClient(MONGODB_URL);
    await client.connect();
    console.log('✅ Successfully connected to MongoDB');
    
    // Get server info
    const admin = client.db('admin').admin();
    const serverInfo = await admin.serverInfo();
    console.log(`MongoDB server version: ${serverInfo.version}`);
    
    // Close the connection
    await client.close();
    console.log('Connection closed');
    
    return {
      success: true,
      version: serverInfo.version,
      message: 'Successfully connected to MongoDB server'
    };
  } catch (error) {
    console.error('❌ Failed to connect to MongoDB:', error.message);
    
    return {
      success: false,
      message: `Failed to connect to MongoDB server: ${error.message}`,
      error: error.message
    };
  }
}

// Run the test
testMongoDBConnection()
  .then(result => {
    console.log('Test result:', result);
    if (!result.success) {
      process.exit(1);
    }
  })
  .catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });