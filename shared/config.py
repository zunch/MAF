"""Configuration management for MAF examples."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AzureOpenAIConfig(BaseSettings):
    """Azure OpenAI configuration for Microsoft Agent Framework."""

    endpoint: str = ""
    api_key: str = ""
    deployment_name: str = "gpt-4o"
    api_version: str = "2024-10-21"

    model_config = SettingsConfigDict(env_prefix='AZURE_OPENAI_')


class AzureAIConfig(BaseSettings):
    """Azure AI Project configuration for Microsoft Agent Framework."""

    project_endpoint: str = ""
    model_deployment_name: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_prefix='AZURE_AI_')


class OpenAIConfig(BaseSettings):
    """OpenAI configuration for Microsoft Agent Framework."""

    api_key: str = ""
    model_id: str = "gpt-4o"

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
    """Main application configuration for Microsoft Agent Framework."""

    def __init__(self):
        self.azure_openai = AzureOpenAIConfig()
        self.azure_ai = AzureAIConfig()
        self.openai = OpenAIConfig()
        self.vector_db = VectorDBConfig()
        self.agent = AgentConfig()
        self.memory = MemoryConfig()
        self.rag = RAGConfig()

        # Determine which AI provider to use (priority order)
        self.use_azure_ai = bool(self.azure_ai.project_endpoint)
        self.use_azure_openai = bool(self.azure_openai.endpoint and self.azure_openai.api_key)
        self.use_openai = bool(self.openai.api_key)

    def create_chat_client(self):
        """
        Create appropriate ChatClient for Microsoft Agent Framework.

        Returns:
            ChatClient instance (AzureAIChatClient, AzureOpenAIChatClient, or OpenAIChatClient)
        """
        try:
            # Försök Azure AI först
            if self.use_azure_ai:
                from agent_framework.azure import AzureAIAgentClient
                from azure.identity.aio import DefaultAzureCredential

                return AzureAIAgentClient(async_credential=DefaultAzureCredential())

            # Sedan Azure OpenAI
            elif self.use_azure_openai:
                from agent_framework.azure import AzureOpenAIChatClient
                from azure.identity import AzureKeyCredential

                return AzureOpenAIChatClient(
                    endpoint=self.azure_openai.endpoint,
                    credential=AzureKeyCredential(self.azure_openai.api_key),
                    model_id=self.azure_openai.deployment_name,
                    api_version=self.azure_openai.api_version
                )

            # Slutligen OpenAI
            elif self.use_openai:
                from agent_framework.openai import OpenAIChatClient

                return OpenAIChatClient(
                    model_id=self.openai.model_id
                )

            else:
                # Fallback till simulering om ingen config finns
                print("⚠️  Ingen AI-konfiguration hittad. Använder simuleringsläge.")
                print("   Konfigurera .env-filen för att använda riktiga AI-modeller.")
                return None

        except ImportError as e:
            print(f"⚠️  Kunde inte importera agent_framework: {e}")
            print("   Installera med: pip install agent-framework --pre")
            return None

    def has_ai_config(self) -> bool:
        """Check if any AI configuration is available."""
        return self.use_azure_ai or self.use_azure_openai or self.use_openai


# Global config instance
config = AppConfig()
