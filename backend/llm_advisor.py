import os
import json
from openai import OpenAI

class LLMAdvisor:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def get_album_insight(self, album_meta, track_scores, cohesion_score):
        """
        Takes raw similarity math to generate a human breakdown.
        Similarity scores are calculated against the user's nearest taste cluster.
        Cohesion score (0-1) represents how consistent the album is internally.
        """
        prompt = f"""
        You are a Vinyl Purchase Advisor. Your goal is to identify "Skip-Free" albums that offer a high-value physical listening experience.

        CONTEXT:
        Vinyl is for deep, intentional listening. We value "Sonic Cohesion" (an album that stays in its lane) even if it's slightly different from what the user usually hears.
        We also value "Slow Burns"—albums that might not be an instant 100% match but are consistent enough to grow on the listener.

        INPUT DATA:
        - Target Album: {album_meta['title']} by {album_meta['artist']}
        - Cluster Similarity Scores (0-1.0): {json.dumps(track_scores, indent=2)}
        - Album Cohesion Score: {cohesion_score:.2f} (1.0 is perfectly consistent, <0.4 is a disjointed mess)

        INSTRUCTIONS:
        1. Evaluate if the album has "filler" (tracks below 0.5).
        2. If the Cohesion Score is HIGH (>0.7), treat the album as a "Strong Artistic Statement." Even if similarity scores are in the 0.6 range, these are HIGH-POTENTIAL GROWERS.
        3. Provide a "Sonic Breakdown" (2-3 sentences). Be honest about the risk, but highlight if the album is a cohesive experience worth buying for the "Slow Burn."
        4. Final "Purchase Confidence Score" (0-100%).

        Response MUST be a valid JSON object with:
        "confidence_score": int,
        "sonic_breakdown": "string",
        "filler_tracks": ["track_title1", "track_title2"]
        """

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                messages=[
                    {"role": "system", "content": "You are a professional music critic and data analyst specializing in high-commitment physical media."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "confidence_score": 0,
                "sonic_breakdown": "Failed to generate analysis.",
                "filler_tracks": []
            }

    def parse_scraper_results(self, artist, album, raw_results):
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
        3. Extract the price (in Euros if possible) and the direct product URL.
        4. If no clear match is found, return an empty list.

        Response MUST be a valid JSON object with:
        "links": [
            {{"site": "string", "price": "string", "url": "string", "status": "In Stock/Out of Stock"}}
        ]
        """

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                messages=[
                    {"role": "system", "content": "You are a data extraction specialist focused on e-commerce."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get('links', [])
        except Exception as e:
            print(f"LLM Scraper Parsing Error: {e}")
            return []