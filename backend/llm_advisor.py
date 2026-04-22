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

    def get_album_insight(self, album_meta, track_scores, journey_data, user_profile):
        """
        Takes raw similarity math and CLAP semantic tags to generate a human breakdown.
        """
        prompt = f"""
        You are a music expert helping someone decide if a vinyl record is worth buying.
        Vinyl is expensive, so every track needs to be a "keeper."

        YOUR TASTE PROFILE (What you usually love):
        {json.dumps(user_profile, indent=2)}

        ALBUM TO EVALUATE: {album_meta['title']} by {album_meta['artist']}

        TRACK LIST DATA:
        {json.dumps(track_scores, indent=2)}

        OVERALL CONFIDENCE SCORE: {journey_data['calculated_score']}%

        CATEGORIES EXPLAINED:
        - "Instant Hit": Tracks that sound exactly like what you already love. Total comfort.
        - "Natural Grower": These feel fresh but familiar. You'll likely love them after 1 or 2 listens.
        - "Slow Burner": A bit different from your usual style. Might take some effort to appreciate.
        - "Risky": These sound very different from your usual taste. On a vinyl, these are the "skips."

        YOUR TASK:
        1. Write a "Sonic Breakdown" (2-3 sentences). Compare the tags of the album tracks to the user's taste profile.
        2. Explain why the score is high or low. (e.g., "This is a safe buy because it's packed with instant hits," or "This is risky because half the album consists of experimental tracks you might skip.")
        3. Identify any "Filler Tracks" (the ones labeled "Risky") by name.

        Response MUST be a valid JSON object with:
        "sonic_breakdown": "string",
        "filler_tracks": ["track_title1", "track_title2"]
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
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                messages=[
                    {"role": "system", "content": "You are a professional music critic. You provide the verbal explanation for a pre-calculated mathematical score."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "sonic_breakdown": "Analysis failed, but the mathematical score is calculated below.",
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