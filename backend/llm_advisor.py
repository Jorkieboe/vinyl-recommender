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

    def get_album_insight(self, album_meta, track_scores, taste_centroid):
        """
        Takes raw similarity math and metadata to generate a human breakdown.
        """
        prompt = f"""
        You are a Vinyl Purchase Advisor. Your goal is to help a user decide if an album is "skip-free" based on their personal taste DNA.

        User's Taste Centroid (Average Audio Features of Loved Tracks):
        {json.dumps(taste_centroid, indent=2)}

        Target Album: {album_meta['title']} by {album_meta['artist']}

        Analyzed Tracks & Similarity Scores (0-1.0, where 1.0 is perfect match):
        {json.dumps(track_scores, indent=2)}

        Instructions:
        1. Evaluate if the album has "filler" tracks (scores below 0.6).
        2. Provide a "Sonic Breakdown" (2-3 sentences) explaining the verdict.
        3. Assign a final "Purchase Confidence Score" (0-100%).

        Response MUST be a valid JSON object with:
        "confidence_score": int,
        "sonic_breakdown": "string",
        "filler_tracks": ["track_title1", "track_title2"]
        """

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                messages=[
                    {"role": "system", "content": "You are a professional music critic and data analyst."},
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