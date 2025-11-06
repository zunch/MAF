"""Configuration management for MAF examples."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AzureOpenAIConfig(BaseSettings):
    """Azure OpenAI configuration."""

    endpoint: str = ""
    api_key: str = ""
    deployment: str = "gpt-4"
    api_version: str = "2024-02-15-preview"
    embedding_deployment: str = "text-embedding-ada-002"

    model_config = SettingsConfigDict(env_prefix='AZURE_OPENAI_')


class OpenAIConfig(BaseSettings):
    """OpenAI configuration."""

    api_key: str = ""
    model: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"

    model_config = SettingsConfigDict(env_prefix='OPENAI_')


class VectorDBConfig(BaseSettings):
    """Vector database configuration."""

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    chroma_path: str = "./chroma_db"
    chroma_persist: bool = True

    model_config = SettingsConfigDict(env_prefix='')


class AgentConfig(BaseSettings):
    """Agent configuration."""

    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 60

    model_config = SettingsConfigDict(env_prefix='AGENT_')


class MemoryConfig(BaseSettings):
    """Memory configuration."""

    short_term_memory_size: int = 10
    long_term_memory_enabled: bool = True
    memory_relevance_threshold: float = 0.7

    model_config = SettingsConfigDict(env_prefix='')


class RAGConfig(BaseSettings):
    """RAG configuration."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 3
    similarity_threshold: float = 0.75

    model_config = SettingsConfigDict(env_prefix='RAG_')


class AppConfig:
    """Main application configuration."""

    def __init__(self):
        self.azure_openai = AzureOpenAIConfig()
        self.openai = OpenAIConfig()
        self.vector_db = VectorDBConfig()
        self.agent = AgentConfig()
        self.memory = MemoryConfig()
        self.rag = RAGConfig()

        # Determine which AI provider to use
        self.use_azure = bool(self.azure_openai.endpoint and self.azure_openai.api_key)

    def get_llm_config(self) -> dict:
        """Get LLM configuration based on available credentials."""
        if self.use_azure:
            return {
                "provider": "azure",
                "endpoint": self.azure_openai.endpoint,
                "api_key": self.azure_openai.api_key,
                "deployment": self.azure_openai.deployment,
                "api_version": self.azure_openai.api_version,
                "max_tokens": self.agent.max_tokens,
                "temperature": self.agent.temperature,
            }
        else:
            return {
                "provider": "openai",
                "api_key": self.openai.api_key,
                "model": self.openai.model,
                "max_tokens": self.agent.max_tokens,
                "temperature": self.agent.temperature,
            }

    def get_embedding_config(self) -> dict:
        """Get embedding configuration based on available credentials."""
        if self.use_azure:
            return {
                "provider": "azure",
                "endpoint": self.azure_openai.endpoint,
                "api_key": self.azure_openai.api_key,
                "deployment": self.azure_openai.embedding_deployment,
                "api_version": self.azure_openai.api_version,
            }
        else:
            return {
                "provider": "openai",
                "api_key": self.openai.api_key,
                "model": self.openai.embedding_model,
            }


# Global config instance
config = AppConfig()
