import json
from collections import defaultdict

class ProfileEngine:
    @staticmethod
    def calculate_rrf(all_clap_results, k=60):
        """
        Calculates a global profile using Reciprocal Rank Fusion.

        Args:
            all_clap_results: List of clap result dicts {layer_name: {label: prob, ...}}
            k: Smoothing constant for RRF (default 60)
        """
        if not all_clap_results:
            return {}

        # Aggregate RRF scores per layer
        # structure: { layer_name: { label: total_rrf_score } }
        layer_scores = defaultdict(lambda: defaultdict(float))

        for result in all_clap_results:
            for layer_name, labels_dict in result.items():
                # Get labels sorted by probability (rank)
                sorted_labels = sorted(labels_dict.items(), key=lambda item: item[1], reverse=True)

                for rank, (label, _) in enumerate(sorted_labels):
                    # RRF formula: 1 / (k + rank)
                    # rank starts at 0, so rank 1 is 0, rank 2 is 1, etc.
                    layer_scores[layer_name][label] += 1.0 / (k + rank)

        # Convert scores to Top 3 ranking per layer
        global_profile = {}
        for layer_name, label_scores in layer_scores.items():
            top_3 = sorted(label_scores.items(), key=lambda item: item[1], reverse=True)[:3]
            global_profile[layer_name] = [label for label, score in top_3]

        return global_profile