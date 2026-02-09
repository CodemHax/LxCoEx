from app.core.config import settings
from app.db.mongo import MONGODatabase
from app.models.snippet_model import SnippetCreate, SnippetDB

class SnippetOps:
    @staticmethod
    async def create(mongo_client, snippet_in: SnippetCreate) -> SnippetDB:
        snippet = SnippetDB(**snippet_in.dict())
        await MONGODatabase.insert_one(
            mongo_client, 
            settings.MONGODB_DB_NAME, 
            "snippets", 
            snippet.dict()
        )
        return snippet

    @staticmethod
    async def get(mongo_client, snippet_id: str) -> SnippetDB:
        snippet_data = await MONGODatabase.find_one(
            mongo_client,
            settings.MONGODB_DB_NAME,
            "snippets",
            {"id": snippet_id}
        )
        
        if not snippet_data:
            return None
            
        return SnippetDB(**snippet_data)
