import inspect
from qdrant_client import QdrantClient
import qdrant_client

print(f"Qdrant Client Version: {qdrant_client.__version__}")
print(f"Has search: {hasattr(QdrantClient, 'search')}")
print(f"Has query_points: {hasattr(QdrantClient, 'query_points')}")

if hasattr(QdrantClient, 'query_points'):
    sig = inspect.signature(QdrantClient.query_points)
    print(f"query_points signature: {sig}")
