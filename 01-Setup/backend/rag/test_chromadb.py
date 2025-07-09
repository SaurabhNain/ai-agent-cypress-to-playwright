import chromadb
 
def test_chromadb():
    try:
        # Initialize the client
        client = chromadb.Client()
        # Create a test collection
        collection = client.create_collection(name="test_collection")
        # Add a simple document
        collection.add(
            documents=["This is a test document"],
            metadatas=[{"source": "test"}],
            ids=["id1"]
        )
        # Query the collection
        results = collection.query(
            query_texts=["test document"],
            n_results=1
        )
        # Print the results
        print("Query results:", results)
        # Delete the test collection
        client.delete_collection("test_collection")
        print("ChromaDB is working correctly!")
        return True
    except Exception as e:
        print(f"Error testing ChromaDB: {str(e)}")
        return False
 
if __name__ == "__main__":
    test_chromadb()