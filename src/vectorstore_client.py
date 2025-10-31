# src/vectorstore_client.py
"""
Vector store client using ChromaDB with LangChain integration.
Handles document storage, retrieval, and similarity search.
"""

import os
from typing import List, Dict, Optional, Tuple, Any
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from config.config import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    TOP_K_RETRIEVAL
)


class VectorStoreClient:
    """
    Client for managing ChromaDB vector store operations.

    Provides methods for:
    - Storing document chunks with embeddings
    - Retrieving similar documents
    - Managing collections
    """

    def __init__(self, embeddings_function: Any):
        """
        Initialize ChromaDB vector store with LangChain integration.

        Args:
            embeddings_function: LangChain embeddings function (from langchain_client)
        """
        self.embeddings = embeddings_function
        self.persist_directory = CHROMA_PERSIST_DIR
        self.collection_name = CHROMA_COLLECTION_NAME

        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize or load existing Chroma vector store
        self.vectorstore: Optional[Chroma] = None
        self._initialize_vectorstore()

        print(f"✅ ChromaDB initialized at: {self.persist_directory}")
        print(f"📦 Collection name: {self.collection_name}")

    def _initialize_vectorstore(self) -> None:
        """
        Initializes the Chroma vector store.
        Creates a new collection or loads existing one.
        """
        try:
            # Initialize Chroma with persistence
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )

            print("✅ Vector store initialized successfully")

        except Exception as e:
            print(f"❌ Error initializing vector store: {e}")
            raise

    def _ensure_vectorstore(self) -> Chroma:
        """
        Ensures vectorstore is initialized and returns it.

        Returns:
            Chroma: The initialized vector store

        Raises:
            RuntimeError: If vectorstore is not initialized
        """
        if self.vectorstore is None:
            raise RuntimeError("Vector store is not initialized")
        return self.vectorstore

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Adds documents to the vector store.

        Args:
            texts (List[str]): List of text chunks to add
            metadatas (Optional[List[Dict]]): Metadata for each chunk
            ids (Optional[List[str]]): Unique IDs for each chunk

        Returns:
            List[str]: List of IDs for added documents
        """
        if not texts:
            print("⚠️  No texts provided to add to vector store")
            return []

        try:
            vectorstore = self._ensure_vectorstore()

            # Create Document objects
            documents = [
                Document(
                    page_content=text,
                    metadata=metadatas[i] if metadatas else {}
                )
                for i, text in enumerate(texts)
            ]

            # Add documents to vector store
            added_ids = vectorstore.add_documents(
                documents=documents,
                ids=ids
            )

            print(f"✅ Added {len(added_ids)} documents to vector store")

            return added_ids

        except Exception as e:
            print(f"❌ Error adding documents to vector store: {e}")
            return []

    def similarity_search(
        self,
        query: str,
        k: int = TOP_K_RETRIEVAL,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Performs similarity search for a query.

        Args:
            query (str): Search query
            k (int): Number of results to return
            filter (Optional[Dict]): Metadata filter

        Returns:
            List[Document]: List of similar documents
        """
        if not query or not query.strip():
            print("⚠️  No query provided for similarity search")
            return []

        try:
            vectorstore = self._ensure_vectorstore()

            # Perform similarity search
            results = vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter
            )

            print(f"🔍 Found {len(results)} similar documents")

            return results

        except Exception as e:
            print(f"❌ Error during similarity search: {e}")
            return []

    def similarity_search_with_score(
        self,
        query: str,
        k: int = TOP_K_RETRIEVAL,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Performs similarity search with relevance scores.

        Args:
            query (str): Search query
            k (int): Number of results to return
            filter (Optional[Dict]): Metadata filter

        Returns:
            List[Tuple[Document, float]]: List of (document, score) tuples
        """
        if not query or not query.strip():
            print("⚠️  No query provided for similarity search")
            return []

        try:
            vectorstore = self._ensure_vectorstore()

            # Perform similarity search with scores
            results = vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )

            print(f"🔍 Found {len(results)} similar documents with scores")

            return results

        except Exception as e:
            print(f"❌ Error during similarity search with scores: {e}")
            return []

    def delete_by_filter(self, filter: Dict[str, Any]) -> bool:
        """
        Deletes documents matching a filter.

        Args:
            filter (Dict): Metadata filter for deletion

        Returns:
            bool: Success status
        """
        try:
            vectorstore = self._ensure_vectorstore()

            # Get documents matching filter
            docs_to_delete = vectorstore.get(where=filter)

            if not docs_to_delete or not docs_to_delete.get('ids'):
                print(f"⚠️  No documents found matching filter: {filter}")
                return True

            # Delete by IDs
            vectorstore.delete(ids=docs_to_delete['ids'])

            print(
                f"🗑️  Deleted {len(docs_to_delete['ids'])} documents matching filter")

            return True

        except Exception as e:
            print(f"❌ Error deleting documents: {e}")
            return False

    def clear_collection(self) -> bool:
        """
        Clears all documents from the collection.

        Returns:
            bool: Success status
        """
        try:
            vectorstore = self._ensure_vectorstore()

            # Delete the entire collection
            vectorstore.delete_collection()

            # Reinitialize the vector store
            self._initialize_vectorstore()

            print("🗑️  Collection cleared successfully")

            return True

        except Exception as e:
            print(f"❌ Error clearing collection: {e}")
            return False

    def get_collection_count(self) -> int:
        """
        Returns the number of documents in the collection.

        Returns:
            int: Number of documents
        """
        try:
            vectorstore = self._ensure_vectorstore()

            # Get collection - using protected attribute with type ignore for library internals
            collection = vectorstore._collection  # type: ignore
            count = collection.count()

            print(f"📊 Collection contains {count} documents")

            return count

        except Exception as e:
            print(f"❌ Error getting collection count: {e}")
            return 0

    def get_documents_by_pdf_id(self, pdf_id: str) -> List[Document]:
        """
        Retrieves all documents associated with a specific PDF ID.

        Args:
            pdf_id (str): The PDF identifier

        Returns:
            List[Document]: List of documents with matching PDF ID
        """
        try:
            vectorstore = self._ensure_vectorstore()

            results = vectorstore.get(where={"pdf_id": pdf_id})

            if not results or not results.get('documents'):
                print(f"⚠️  No documents found for PDF ID: {pdf_id}")
                return []

            # Convert to Document objects
            documents = [
                Document(
                    page_content=doc,
                    metadata=results['metadatas'][i] if results.get(
                        'metadatas') else {}
                )
                for i, doc in enumerate(results['documents'])
            ]

            print(f"📄 Found {len(documents)} documents for PDF ID: {pdf_id}")

            return documents

        except Exception as e:
            print(f"❌ Error retrieving documents by PDF ID: {e}")
            return []

    def as_retriever(self, **kwargs: Any) -> VectorStoreRetriever:
        """
        Returns a LangChain retriever for the vector store.

        This allows integration with LangChain chains and agents.

        Args:
            **kwargs: Arguments to pass to the retriever

        Returns:
            VectorStoreRetriever: LangChain retriever object
        """
        vectorstore = self._ensure_vectorstore()
        return vectorstore.as_retriever(**kwargs)
