// Simple script to test MongoDB connection
const { MongoClient } = require('mongodb');

// Connection URL
const url = 'mongodb://192.168.7.10:27017';
const dbName = 'myresumo';

async function main() {
  console.log(`Attempting to connect to MongoDB at ${url}`);
  
  try {
    // Create a new MongoClient
    const client = new MongoClient(url);
    
    // Connect to the MongoDB server
    await client.connect();
    console.log('Successfully connected to MongoDB server');
    
    // Get server info
    const admin = client.db('admin').admin();
    const serverInfo = await admin.serverInfo();
    console.log(`MongoDB server version: ${serverInfo.version}`);
    
    // List databases
    const dbs = await admin.listDatabases();
    console.log('Available databases:');
    dbs.databases.forEach(db => {
      console.log(`- ${db.name}`);
    });
    
    // Check if myresumo database exists
    const dbExists = dbs.databases.some(db => db.name === dbName);
    if (dbExists) {
      console.log(`Database '${dbName}' exists`);
      
      // List collections in the myresumo database
      const db = client.db(dbName);
      const collections = await db.listCollections().toArray();
      console.log(`Collections in '${dbName}' database:`);
      collections.forEach(collection => {
        console.log(`- ${collection.name}`);
      });
      
      // Check if resumes collection exists and get a sample document
      if (collections.some(col => col.name === 'resumes')) {
        const resumesCollection = db.collection('resumes');
        const sampleResume = await resumesCollection.findOne({});
        if (sampleResume) {
          console.log('Sample resume document fields:', Object.keys(sampleResume));
        } else {
          console.log('No resume documents found');
        }
      }
      
      // Check if prompts collection exists and get a sample document
      if (collections.some(col => col.name === 'prompts')) {
        const promptsCollection = db.collection('prompts');
        const samplePrompt = await promptsCollection.findOne({});
        if (samplePrompt) {
          console.log('Sample prompt document fields:', Object.keys(samplePrompt));
        } else {
          console.log('No prompt documents found');
        }
      }
    } else {
      console.log(`Database '${dbName}' does not exist`);
    }
    
    // Close the connection
    await client.close();
    console.log('Connection closed');
  } catch (error) {
    console.error('Error connecting to MongoDB:', error.message);
    console.error('Error details:', error);
  }
}

main().catch(console.error);