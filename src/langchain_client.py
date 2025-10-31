# src/langchain_client.py
"""
LangChain client for LLM operations and embeddings.
Handles all interactions with OpenAI via LangChain abstractions.
"""

from typing import List, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain.messages import HumanMessage
from config.config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    EMBEDDING_MODEL,
    LLM_TEMPERATURE,
    ROLE_EXTRACTION_PROMPT
)


class LangChainClient:
    """
    Client for interacting with OpenAI models via LangChain.

    Provides methods for:
    - Text generation (role extraction)
    - Text embeddings (for vector storage)
    """

    def __init__(self):
        """
        Initialize LangChain client with OpenAI models.
        """
        # Initialize Chat LLM for text generation
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_completion_tokens=1000,  # Sufficient for role extraction
            timeout=60  # 60 second timeout
        )

        # Initialize embeddings model
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,

        )

        # Create prompt template for role extraction
        self.role_extraction_template = PromptTemplate(
            input_variables=["document_content"],
            template=ROLE_EXTRACTION_PROMPT
        )

        print(f"✅ LangChain client initialized with model: {LLM_MODEL}")

    def extract_roles_from_text(self, document_text: str) -> str:
        """
        Extracts job roles from document text using LLM.

        Args:
            document_text (str): The document content to analyze

        Returns:
            str: Comma-separated list of roles or 'None' if no roles found
        """
        if not document_text or not document_text.strip():
            print("⚠️  No document text provided for role extraction")
            return "None"

        try:
            # Format the prompt with document content
            prompt = self.role_extraction_template.format(
                document_content=document_text
            )

            # Create message and invoke LLM
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])

            # Extract content from response
            roles_text = str(response.content).strip()

            print(f"📝 LLM extracted roles: {roles_text[:100]}...")

            return roles_text

        except Exception as e:
            print(f"❌ Error during LLM role extraction: {e}")
            return "None"

    def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """
        Generates embeddings for a given text using OpenAI embeddings.

        Args:
            text (str): Text to embed

        Returns:
            Optional[List[float]]: Embedding vector or None if failed
        """
        if not text or not text.strip():
            print("⚠️  No text provided for embedding")
            return None

        try:
            # Generate embedding using LangChain's OpenAI embeddings
            embedding = self.embeddings.embed_query(text)

            return embedding

        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return None

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for multiple texts in a batch.

        More efficient than calling generate_embeddings() multiple times.

        Args:
            texts (List[str]): List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not texts:
            return []

        try:
            # Use batch embedding for efficiency
            embeddings = self.embeddings.embed_documents(texts)

            print(f"✅ Generated {len(embeddings)} embeddings in batch")

            return embeddings

        except Exception as e:
            print(f"❌ Error generating batch embeddings: {e}")
            return []

    def query_with_context(self, query: str, context: str) -> str:
        """
        Generates a response to a query given contextual information.

        This is used for RAG-based queries where we retrieve relevant
        document chunks and ask the LLM to answer based on that context.

        Args:
            query (str): The user's question
            context (str): Retrieved context from vector store

        Returns:
            str: LLM's answer based on the context
        """
        if not context or not context.strip():
            return "No relevant context found to answer the query."

        try:
            # Create a prompt for context-based Q&A
            qa_prompt = f"""Based on the following document excerpts, answer the question.
            If the answer cannot be found in the context, say "I cannot find this information in the provided documents."

            Context:
            {context}

            Question: {query}

            Answer:"""

            message = HumanMessage(content=qa_prompt)
            response = self.llm.invoke([message])

            return str(response.content).strip()

        except Exception as e:
            print(f"❌ Error during context-based query: {e}")
            return f"Error generating response: {str(e)}"

    def get_embedding_dimension(self) -> int:
        """
        Returns the dimension of the embedding vectors.

        For text-embedding-3-small: 1536 dimensions

        Returns:
            int: Embedding vector dimension
        """
        # text-embedding-3-small produces 1536-dimensional vectors
        # text-embedding-3-large produces 3072-dimensional vectors
        if "large" in EMBEDDING_MODEL:
            return 3072
        else:
            return 1536
