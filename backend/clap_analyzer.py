import torch
import librosa
from transformers import ClapModel, ClapProcessor

class ClapAnalyzer:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load_model(self):
        if self.model is None:
            print(f"Loading CLAP model to {self.device}... this might take a minute.")
            self.model = ClapModel.from_pretrained("laion/clap-htsat-unfused").to(self.device)
            self.processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
            print("CLAP model loaded successfully.")

    def analyze(self, audio_path):
        self._load_model()

        layers = {
            "Layer 1: Sound Sources": [
                "piano music",
                "acoustic guitar music",
                "electric guitar music",
                "synthesizer-based music",
                "drum-heavy music",
                "orchestral music",
                "vocal-focused music"
            ],
            "Layer 2: Energy / Movement": [
                "slow calm music",
                "medium tempo groove",
                "fast energetic music",
                "aggressive intense music"
            ],
            "Layer 3: Texture / Production": [
                "clean studio recording",
                "lo-fi recording",
                "distorted noisy sound",
                "polished modern production",
                "acoustic natural sound"
            ],
            "Layer 4: Mood": [
                "melancholic sad music",
                "uplifting happy music",
                "dreamy atmospheric music",
                "dark moody music"
            ]
        }

        try:
            # CLAP models typically require 48kHz audio inputs
            y, sr = librosa.load(audio_path, sr=48000)

            results = {}

            for layer_name, texts in layers.items():
                inputs = self.processor(text=texts, audios=y, return_tensors="pt", sampling_rate=48000, padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # Compute softmax probabilities over the provided text labels for this layer
                    probs = outputs.logits_per_audio.softmax(dim=-1)[0]

                # Map text labels to their probability scores
                layer_results = {text: float(prob) for text, prob in zip(texts, probs)}
                # Sort the layer results in descending order of probability
                layer_results = dict(sorted(layer_results.items(), key=lambda item: item[1], reverse=True))

                results[layer_name] = layer_results

            return results
        except Exception as e:
            print(f"Error in CLAP analysis: {e}")
            return None