import torch
import librosa
import yaml
import os
from transformers import ClapModel, ClapProcessor

class ClapAnalyzer:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Determine prompts path relative to this script
        self.prompts_path = os.path.join(os.path.dirname(__file__), "clap_prompts.yaml")

    def _load_model(self):
        if self.model is None:
            print(f"Loading CLAP model to {self.device}... this might take a minute.")
            self.model = ClapModel.from_pretrained("laion/clap-htsat-unfused").to(self.device)
            self.processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
            print("CLAP model loaded successfully.")

    def _load_layers(self):
        """Loads categories and prompts from the YAML configuration file"""
        if not os.path.exists(self.prompts_path):
            print(f"Warning: Prompts file not found at {self.prompts_path}. Using minimal fallback.")
            return {"System": ["error loading prompts"]}

        try:
            with open(self.prompts_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error reading YAML file: {e}")
            return {"System": ["error parsing prompts"]}

    def analyze(self, audio_path):
        self._load_model()
        layers = self._load_layers()

        try:
            # CLAP models typically require 48kHz audio inputs
            print('Starting CLAP analysis...')
            y, sr = librosa.load(audio_path, sr=48000)

            results = {}

            for layer_name, texts in layers.items():
                if not texts:
                    continue

                inputs = self.processor(text=texts, audio=y, return_tensors="pt", sampling_rate=48000, padding=True)
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