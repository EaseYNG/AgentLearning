import chromadb
from typing import List

class DBManager:
    document_id = 0
    
    def __init__(self):
        self.client = chromadb.PersistentClient(path="/db/memory")

    def create_collection(self, name, metadata=None):
        return self.client.create_collection(name, metadata)
    
    def get_collection(self, name):
        return self.client.get_collection(name)
    
    @classmethod
    def add(cls, self, collection_name, documents, metadatas=None):
        collection = self.client.get_collection(collection_name)
        # 根据类属性添加doc_id
        ids = [f"id_{cls.document_id + i}" for i in range(len(documents))]
        cls.document_id += len(documents)
        collection.add(documents=documents, ids=ids, metadatas=metadatas)

    @classmethod
    def reset(cls):
        cls.document_id = 0
    
    def display_collections(self):
        print("collections: ")
        for c in self.client.list_collections():
            print(c)

    def display_documents(self, collection_name):
        collection = self.client.get_collection(collection_name)
        print(f"documents in {collection_name}: ")
        
        for d in collection.get():
            print(d)

    def query(self, collection_name, text: List):
        collection = self.client.get_collection(collection_name)

        return collection.query(query_texts=text)
    
