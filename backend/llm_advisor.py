import os
import json
from openai import OpenAI, AsyncOpenAI
from backend.utils.logger import logger
from pydantic import BaseModel

class albumOutput(BaseModel):
    artist: str
    album: str
    sonic_breakdown: str
    filler_tracks: list[str]

class resultOutput(BaseModel):
    artist: str
    album: str
    album_id: float
    reasoning: str

class vinylOutput(BaseModel):
    store: str
    product: str
    link: str
    price: str


class LLMAdvisor:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "http://25.4.74.224:1234/v1")
        self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def get_album_insight(self, album_meta, track_scores, journey_data, user_profile):
        """
        Takes raw similarity math and CLAP semantic tags to generate a human breakdown.
        """
        prompt = f"""
        You are a Vinyl Purchase Advisor. Your goal is to identify "Skip-Free" albums.

        USER SONIC DNA (Top Labels from Loved Tracks):
        {json.dumps(user_profile, indent=2)}

        SONIC JOURNEY THEORY:
        - Instant Hit: Instant comfort. Semantic tags should match User DNA closely.
        - Grower: Easy growth. Some tags match, others introduce fresh but compatible textures.
        - Experimental: Experimental risk. Tags here are likely far from User DNA (e.g. User likes 'Techno', experimental is 'Classical').

        INPUT DATA:
        - Target Album: {album_meta['title']} by {album_meta['artist']}
        - Track Analysis (Math + CLAP Semantics): {json.dumps(track_scores, indent=2)}
        - Summary Stats: {json.dumps(journey_data, indent=2)}

        INSTRUCTIONS:
        1. EXPLAIN the tiering using the semantic tags. For "Risky" tracks, explain specifically why they are risky based on their tags compared to User Sonic DNA.
        2. REVIEW the "Calculated Score" ({journey_data['calculated_score']}%).
        3. DATA INTERPRETATION:
           - Anchors: High Buy momentum.
           - Inner Bridges: Perfect for growth.
           - Horizon: Risk of a "Skip" track which ruins the vinyl experience.
        4. Warn if the album is "Repetitive" or if the "Risky" tracks are too jarringly different.

        Response MUST be a valid JSON object with:
        "sonic_breakdown": "string (Focus on semantic comparisons between DNA and the album tags. Explain WHY the score is what it is)",
        "filler_tracks": ["track_title1", "track_title2"]
        """

        try:
            response = self.client.chat.completions.parse(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                messages=[
                    {"role": "system", "content": "You are a professional music critic. You provide the verbal explanation for a pre-calculated mathematical score."},
                    {"role": "user", "content": prompt}
                ],
                response_format=albumOutput
            )
            message = response.choices[0].message
            if hasattr(message, 'parsed') and message.parsed:
                return message.parsed.model_dump()

            # Fallback for unexpected formats
            return json.loads(message.content)
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return {
                "sonic_breakdown": "Analysis failed, but the mathematical score is calculated below.",
                "filler_tracks": []
            }

    async def parse_scraper_results(self, artist, album, raw_results):
        """
        Uses LLM to find the actual purchase link and price from raw HTML/text.
        """
        prompt = f"""
        Extract direct purchase links and prices for the vinyl record of '{album}' by '{artist}' from the following raw scraper data.

        Scraper Data:
        {json.dumps(raw_results, indent=2)}

        Instructions:
        1. Look for items that match the artist and album exactly.
        2. Ensure the item is a Vinyl/LP, not a CD or Digital download.
        3. Extract the name of the store, the product name, the direct URL, and the price.
        4. If no clear match is found, return an empty list.

        Response MUST be a valid JSON object with:
        "links": [
            {{"store": "string", "product": "string", "link": "string", "price": "string"}}
        ]
        """

        try:
            response = await self.async_client.chat.completions.parse(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),

                messages=[
                    {"role": "system", "content": "You are a data extraction specialist focused on e-commerce."},
                    {"role": "user", "content": prompt}
                ],
                response_format=vinylOutput
            )
            message = response.choices[0].message

            date = None

            if hasattr(message, 'parsed') and message.parsed:
                data = message.parsed.model_dump()
            
            return data.get('links', [])
        except Exception as e:
            logger.error(f"LLM Scraper Parsing Error: {e}")
            return []

    async def agent_call(self, messages, tools_schema=None):
        """Asynchronous call for the Agent loop"""
        try:
            # Prepare call arguments
            call_kwargs = {
                "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                "messages": messages
            }

            if tools_schema:
                call_kwargs["tools"] = tools_schema
                call_kwargs["tool_choice"] = "auto"

            response = await self.async_client.chat.completions.create(**call_kwargs)

            # The model might return tool calls or content
            message = response.choices[0].message
            # Return the full message object for the agent loop to process
            return message
        except Exception as e:
            logger.error(f"Agent LLM Error: {e}")
            return None

    async def final_decision (self, messages):
        """Asynchronous call for the Agent loop"""
        try:

            system_prompt =  {"role": "system", "content": """
                    You are a vinyl recommender and the final step on the agent.
                    I want you to respond into the following json format
                        {
                            artist: string
                            album: string
                            album_id: int
                            reasoning: string
                        }

                    """
            }

            combined_messages = [system_prompt] + messages
            # Prepare call arguments
            call_kwargs = {
                "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                "messages": combined_messages,
                "response_format": resultOutput
            }

            response = await self.async_client.chat.completions.parse(**call_kwargs)

            # The model might return tool calls or content
            message = response.choices[0].message

            # If using parse, the structured result is in .parsed
            if hasattr(message, 'parsed') and message.parsed:
                return message.parsed.model_dump()

            return message.content
        except Exception as e:
            logger.error(f"Agent LLM Error: {e}")
            return None