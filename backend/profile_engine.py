import json
from collections import defaultdict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib
# Use the 'Agg' backend to allow plot generation in background threads
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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

class ClusterEngine:
    def __init__(self, n_clusters=5):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        self.cluster_centers = None
        self.library_vectors = None
        # Weights for different audio groups
        self.weights = {
            "timbre": 0.50,   # MFCCs
            "harmony": 0.30,  # Chroma
            "energy": 0.20    # Brightness + Tempo
        }

    def _flatten(self, feat):
        """Converts feature dict to a single flat vector for clustering"""
        return feat['mfcc'] + feat['chroma'] + [feat['spectral_brightness'], feat['tempo']]

    def fit_clusters(self, feature_list):
        """Trains K-Means on the user's entire library of liked tracks"""
        if not feature_list:
            return None

        self.library_vectors = np.array([self._flatten(f) for f in feature_list])

        # Adjust cluster count if library is smaller than requested K
        actual_clusters = min(len(self.library_vectors), self.n_clusters)
        if actual_clusters < self.n_clusters:
            self.kmeans = KMeans(n_clusters=actual_clusters, n_init=10, random_state=42)

        scaled_vectors = self.scaler.fit_transform(self.library_vectors)
        self.kmeans.fit(scaled_vectors)
        self.cluster_centers = self.kmeans.cluster_centers_
        return self.cluster_centers

    def get_best_similarity(self, track_features):
        """
        Calculates similarity score (0-1) using Weighted Gaussian Decay.
        Tuned for higher leniency to match visual intuition in PCA plots.
        """
        if self.cluster_centers is None:
            return 0.0

        feat_vec = np.array([self._flatten(track_features)])
        scaled_feat = self.scaler.transform(feat_vec)[0]

        best_weighted_score = 0.0

        for center in self.cluster_centers:
            # 1. Calculate squared distances per group
            # We divide by the number of features in each group to normalize the 'bloat'
            # of high-dimensional vectors.
            dist_timbre = np.sum((scaled_feat[0:13] - center[0:13])**2) / 13.0
            dist_harmony = np.sum((scaled_feat[13:25] - center[13:25])**2) / 12.0
            dist_energy = np.sum((scaled_feat[25:27] - center[25:27])**2) / 2.0

            # 2. Gaussian Scoring: Score = exp(-dist / sigma)
            # Increased Sigmas significantly to make the 'acceptance' plateau much wider.
            # 0.0 distance = 1.0 score. 2.0 distance (avg 1.4 std-dev per dim) = ~80-90% score.
            score_timbre = np.exp(-dist_timbre / 2.5)
            score_harmony = np.exp(-dist_harmony / 2.0)
            score_energy = np.exp(-dist_energy / 1.5)

            # 3. Apply weights
            total_score = (
                (score_timbre * self.weights["timbre"]) +
                (score_harmony * self.weights["harmony"]) +
                (score_energy * self.weights["energy"])
            )

            if total_score > best_weighted_score:
                best_weighted_score = total_score

        return float(best_weighted_score)

    def generate_taste_map(self, album_features, album_title):
        """Generates a PCA plot of the library, clusters, and the new album tracks"""
        if self.library_vectors is None or self.cluster_centers is None:
            return

        album_vecs = np.array([self._flatten(f) for f in album_features])

        # Scale and project all data using the library's coordinate space
        lib_scaled = self.scaler.transform(self.library_vectors)
        album_scaled = self.scaler.transform(album_vecs)

        # Project to 2D
        all_coords = self.pca.fit_transform(np.vstack([lib_scaled, self.cluster_centers, album_scaled]))

        n_lib = len(lib_scaled)
        n_clusters = len(self.cluster_centers)

        lib_coords = all_coords[:n_lib]
        cluster_coords = all_coords[n_lib:n_lib+n_clusters]
        alb_coords = all_coords[n_lib+n_clusters:]

        # Plotting
        plt.figure(figsize=(10, 7))
        plt.style.use('dark_background')

        plt.scatter(lib_coords[:, 0], lib_coords[:, 1], c='#4F46E5', alpha=0.3, label='Your Library', s=30)
        plt.scatter(cluster_coords[:, 0], cluster_coords[:, 1], c='#EC4899', marker='X', s=200, label='Taste Centers', edgecolors='white')
        plt.scatter(alb_coords[:, 0], alb_coords[:, 1], c='#10B981', s=100, label=f'Album: {album_title}', edgecolors='white')

        plt.title(f"Sonic DNA Map: {album_title}", fontsize=14, pad=20)
        plt.legend()
        plt.grid(color='#374151', linestyle='--', alpha=0.5)

        # Save to file
        plt.savefig('taste_map.png', bbox_inches='tight', dpi=150)
        plt.close()
        print(f"Visualization saved to taste_map.png")