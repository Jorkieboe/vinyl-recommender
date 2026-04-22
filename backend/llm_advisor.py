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

    def get_album_insight(self, album_meta, track_scores, journey_data):
        """
        Takes raw similarity math to generate a human breakdown.
        journey_data categorizes tracks into Anchors, Bridges, and Horizon tiers.
        """
        prompt = f"""
        You are a Vinyl Purchase Advisor. Your goal is to identify "Skip-Free" albums that offer growth.

        SONIC JOURNEY THEORY:
        The best vinyl albums are not just clones of what we already like. They are a journey with distinct stages of challenge:
        - ANCHORS (>80%): Instant comfort. You already love this sound.
        - INNER BRIDGES (70-80%): Easy growth. Familiar but fresh; highly likely to be liked within 1-2 listens.
        - OUTER BRIDGES (60-70%): Challenging expansion. Significant departure from your centers; requires intentional "slow burn" listening.
        - THE HORIZON (<60%): Experimental risk. Very far from your current DNA; high potential for long-term reward but high risk of "skipping."

        IDEAL MIX: A perfect vinyl should bridge these gaps. If an album jumps straight from Anchors to Horizon without "Inner Bridges," it feels disjointed. If it has too many "Outer Bridges" and no "Inner Bridges," it might be too much of a struggle to get through.

        INPUT DATA:
        - Target Album: {album_meta['title']} by {album_meta['artist']}
        - Track Stats: {json.dumps(journey_data, indent=2)}
        - Detailed Scores: {json.dumps(track_scores, indent=2)}

        INSTRUCTIONS:
        1. REVIEW the "Calculated Score" ({journey_data['calculated_score']}%). This score uses an "Exploration-First" weight.
        2. DATA INTERPRETATION:
           - Anchors (>80%) provide maximum BUY momentum (4 votes).
           - Inner Bridges (70-80%) are pure BUY momentum (2 votes), signaling "Safe Exploration."
           - Outer Bridges (60-70%) provide 1 BUY / 2 NOT BUY (leaning towards risk).
           - Horizon tracks (<60%) provide 3 NOT BUY (high risk).
        3. EXPLAIN the "Exploration Potential". If the score is high due to many Inner Bridges, explain that the album is a perfect bridge between their current taste and new discoveries.
        4. Warn if the album is "Repetitive" (journey_data['is_repetitive'] = true).

        Response MUST be a valid JSON object with:
        "confidence_score": int (Matches or slightly adjusts the calculated_score),
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