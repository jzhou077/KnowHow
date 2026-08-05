from graphiti_core import Graphiti
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.driver.neo4j_driver import Neo4jDriver
from graphiti_core.embedder.voyage import VoyageAIEmbedder, VoyageAIEmbedderConfig
from graphiti_core.llm_client.anthropic_client import AnthropicClient
from graphiti_core.llm_client.config import LLMConfig

from brain.config import settings


def make_graphiti() -> Graphiti:
    """Makes a Graphiti instance. 
    
    Remember that caller must call .close() because Neo4j has a bunch of network connections that won't clean themselves up.
    """
    return Graphiti(
        graph_driver=Neo4jDriver(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        ),
        llm_client=AnthropicClient(
            config=LLMConfig(
                api_key=settings.anthropic_api_key,
                model="claude-sonnet-5",
                small_model="claude-haiku-4-5-20251001"
            )
        ),
        embedder=VoyageAIEmbedder(
            config=VoyageAIEmbedderConfig(
                api_key=settings.embedding_api_key,
                embedding_model="voyage-4",
            )
        ),
        cross_encoder=OpenAIRerankerClient(),
        max_coroutines=settings.graphiti_concurrency,
    )

async def ensure_schema(graph: Graphiti) -> None:
    """Creates Graphiti's Neo4j indicies and constraints initially.
    
    It is idempotent, meaning that running it multiple times has the same effect as running it once,
    so it's fine to call at the start of every ingest even if you already initialized the graph.
    """
    await graph.build_indices_and_constraints()