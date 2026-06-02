import json
import inspect
import random
from typing import Any, Callable, Dict, List, Optional, Type
from datetime import datetime
from pydantic import create_model, Field
import os
import pathspec
from enum import Enum

from backend.utils.logger import logger

class Tool:
    def __init__(self, fn: Callable, name: str, description: str, parameters_model: Type, requires_approval: bool = False):
        self.fn = fn
        self.name = name
        self.description = description
        self.parameters_model = parameters_model
        self.requires_approval = requires_approval

    def get_schema(self) -> Dict[str, Any]:
        """Returns the OpenAI-style tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_model.model_json_schema()
            }
        }

    async def execute(self, **kwargs) -> Any:
        try:
            validated_params = self.parameters_model(**kwargs)

            params_dict = validated_params.model_dump()

            if inspect.iscoroutinefunction(self.fn):
                return await self.fn(**params_dict)
            return self.fn(**params_dict)
        except Exception as e:
            return f"Error: {str(e)}"

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register_instance_tools(self, instance):
        """
        Looks through a class instance for methods marked with @tool
        and registers them as bound methods (with 'self' already included).
        """
        for name, method in inspect.getmembers(instance, predicate=inspect.ismethod):
            if hasattr(method, "_is_tool"):
                tool_name = method.__name__
                doc = inspect.getdoc(method) or "No description."

                # Extract parameters for Pydantic model
                sig = inspect.signature(method)
                fields = {}
                for p_name, param in sig.parameters.items():
                    # Note: 'inspect.ismethod' returns bound methods,
                    # so 'self' is ALREADY REMOVED from the signature.
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else Any
                    default = param.default if param.default != inspect.Parameter.empty else ...
                    fields[p_name] = (annotation, default)

                model = create_model(f"{tool_name}_params", **fields)
                self.tools[tool_name] = Tool(method, tool_name, doc, model)
                logger.db(f"Registered Agent Tool: {tool_name}")

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        return [tool.get_schema() for tool in self.tools.values()]

# Global registry instance
registry = ToolRegistry()

def tool(fn: Callable):
    """
    Decorator to mark a function as a tool.
    It doesn't register it yet; registration happens when an instance is created.
    """
    fn._is_tool = True
    return fn

def requires_approval(fn: Callable):
    """Decorator to mark a tool as requiring human approval before execution."""
    fn._requires_approval = True
    return fn

# --- Core Lab Tools ---

class MusicAgentTools:
    def __init__(self, bridge):
        self.bridge = bridge
        # Import inside to avoid circular imports if necessary
        from backend.lastfm_client import LastFMClient
        self.lastfm = LastFMClient()

    @tool
    def get_time(self):
        """Returns the current system time. Useful for temporal reasoning."""
        return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z%z")

    @tool
    def pick_artist_scope(self):
        """
        Randomly picks an artist from one of the user's taste clusters.
        Use this to narrow the search scope for an album discovery session.
        Returns the artist name as a string.
        """
        engine = self.bridge.cluster_engine

        # Check if engine has processed data yet
        if not engine.cluster_to_artists:
            logger.ai("Fitting taste clusters before picking artist scope...")
            all_prefs = self.bridge.db.get_all_features()
            if not all_prefs:
                return "Error: User profile is empty. Cannot pick an artist scope without synced history."
            engine.fit_clusters(all_prefs)

        if not engine.cluster_to_artists:
            return "Error: Clustering yielded no valid artist groups."

        # Pick a random cluster index
        cluster_ids = list(engine.cluster_to_artists.keys())
        chosen_id = random.choice(cluster_ids)

        # Pick a random artist from that specific cluster
        artists_in_cluster = list(engine.cluster_to_artists[chosen_id])
        chosen_artist = random.choice(artists_in_cluster)

        logger.ai(f"Selected Artist Scope: '{chosen_artist}' (from taste cluster #{chosen_id})")
        return chosen_artist

    @tool
    def inspect_album(self, artist):
        """Takes an artist and retrieves a sample album to analyze.
        Calculates a compatibility score (0-100) against the user's music taste.
        """
        logger.ai(f"Inspecting work by artist: {artist}")
        result = self.bridge.client.get_album_by_artist(artist)

        if result is None:
            return f"Could not find any new/unscanned albums for artist '{artist}' on Deezer."

        album_id, album_title = result

        logger.ai(f"Analyzing album: {album_title}")
        journey_data = self.bridge._run_album_numerical_analysis_logic(None, album_id)

        journey_data["album_title"] = album_title
        journey_data["album_id"] = album_id
        journey_data["artist"] = artist

        logger.ai(f"Final compatibility score for {album_title} by {artist}: {journey_data['calculated_score']}%")
        return json.dumps(journey_data)

    @tool
    def get_artist_knowledge(self, artist: str):
        """Checks the database to see what is already known about the given artist.
        Returns details of synced tracks in the library, previously scanned albums, and their average scores.
        """
        logger.ai(f"Checking system knowledge for artist: '{artist}'")
        db = self.bridge.db
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM user_preferences WHERE LOWER(artist) = LOWER(?)",
                (artist,)
            )
            library_count = cursor.fetchone()[0]
            cursor.execute(
                "SELECT title, confidence_score, is_recommended FROM scanned_albums WHERE LOWER(artist) = LOWER(?)",
                (artist,)
            )
            scanned_rows = cursor.fetchall()
        scanned_albums = []
        scores = []
        for row in scanned_rows:
            title, score, is_rec = row
            scanned_albums.append({
                "title": title,
                "confidence_score": score,
                "is_recommended": bool(is_rec)
            })
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else None
        result = {
            "artist": artist,
            "in_library": library_count > 0,
            "library_track_count": library_count,
            "previously_scanned": scanned_albums,
            "average_confidence_score": avg_score
        }
        logger.ai(f"Artist knowledge for '{artist}': {result}")
        return json.dumps(result)

    @tool
    def get_similar_artists(self, artist: str):
        """Returns list of three similar artists for a given artist name."""
        # Fix: Ensure the artist parameter is passed to the client
        sim_artists = self.bridge.lfmclient.get_similar_artists(artist)
        logger.ai(sim_artists)
        return sim_artists