## Problem & Audience

### The Problem: The Vinyl Uncertainty Tax
Vinyl is a high-commitment medium. Unlike streaming, buying a record involves a financial investment (often $30+) and a temporal commitment to **focused listening**. 

Modern streaming creates specific barriers for potential collectors:
1.  **The Uncertainty Tax:** Users hesitate to buy physical records because they aren't sure if they will like the *entire* album. One "hit" song isn't enough to justify a $30 purchase if the rest of the album contains tracks that fall outside their personal taste.
2.  **Streaming-to-Vinyl Mismatch:** Streaming discovery is often driven by playlists where songs are isolated. Vinyl requires a complete experience. Most streaming recommendations fail to identify which albums consist entirely of tracks that the user will actually enjoy throughout.
3.  **The Alignment Gap:** Users often discover a single track but lack the tools to verify if the remaining 30–40 minutes of an album align with their personal "Taste Profile."
4.  **The Acquisition Barrier:** Finding where a recommended album is currently in stock at a fair price across fragmented marketplaces is a significant hurdle once the decision to buy is made.

### The Audience
The **Vinyl Taste Agent** is designed for:
*   **Selective Collectors:** People who want to stop "guessing" which albums are worth physical space and hard-earned money.
*   **Taste-First Listeners:** Users who want a collection where every track on a record aligns with their specific aesthetic preferences, regardless of genre or tempo shifts.
*   **The Risk-Averse:** Individuals who love a single track but need AI-driven confidence that the unknown tracks on an album are matches for what they already enjoy.

## Core Principles

### Principle 1: The "No-Skip" Standard: Comprehensive Alignment
A vinyl record is an unbreakable sequence. Therefore, the system only recommends albums where the majority of tracks—ideally all—fall within the user's established taste profile. An album can be sonically diverse (e.g., shifting from fast to slow tracks), provided both styles align with the user's preferences. The system flags albums as risky if tracks deviate into sonic territories the user historically dislikes.

### Principle 2: Quantified Recommendation Score
The system does not make the final purchase decision; the user does. The agent's role is to provide a granular **Confidence Score** based on how closely an album's total tracklist aligns with the user's music preferences. This transparency empowers the user to manage their own financial risk.

### Principle 3: Financial Risk Mitigation
Every recommendation is treated as a $30+ decision. The system must provide "Purchase Confidence" by proving that the unknown tracks on an album share the same sonic DNA (rhythm, timbre, and mood) as the user's favorite "anchor" tracks and historical preferences.

### Principle 4: Discovery to Acquisition
A recommendation is only actionable if the record is actually obtainable. The agent facilitates the transition from "liking" to "owning" by identifying active purchase locations and pricing for recommended albums.

## Key Features

### Feature A: The "Filler" Detection Engine
- Analyzes the audio previews of every track on an album.
- Compares the "unknown" tracks against the user's "Taste Centroid" using audio embedding similarity.
- Identifies "outliers" that fall outside the user's taste profile to inform the final score, ensuring the album doesn't contain "skips" for that specific user.

### Feature B: Purchase Confidence Score
- Generates a **0–100% score** representing the likelihood that the user will enjoy the entire album.
- Provides a "Sonic Breakdown" explaining why the score was given (e.g., "All tracks align with your preference for both high-energy beats and mellow acoustics").
- Acts as the primary data point for the user’s final purchase decision.

### Feature C: Marketplace Availability Scraper
- Uses **Playwright** to actively search for "Buy it Now" listings across dutch sites like Velvet, Bol.com, and other indie retail sites.
- Automatically finds and presents active purchase links once an album scored higher than 65%.

### [FUTURE FEATURE] Adaptive Similarity Learner
- Future iterations will track user feedback on recommendations to refine the "Sonic DNA" profile.
- Planned to narrow the margin of error between predicted similarity and actual user preference over time.

## User Actions & Flows

### User Onboarding & Profiling
1.  **Sync:** Connect Deezer to ingest behavioral data and identify existing favorites.
2.  **Initial Mapping:** The system identifies the user's "Sonic DNA," establishing a baseline of audio characteristics they currently enjoy.

### The "Buy-Ready" Loop
1.  **Selection:** User identifies a favorite song from their most liked songs via the Deezer API.
2.  **Full-Album Scan:** The agent fetches the entire album metadata and audio previews.
3.  **Comprehensive Taste Audit:** The system checks if every track on the album aligns with the user's taste profile, identifying if the album is a cohesive match for the user or contains "filler" that they would likely skip.
4.  **The Verdict:** The agent displays a **Purchase Confidence Score** (e.g., *"This album is an 85% match for your collection"*). 
5.  **User Decision:** The user reviews the score and the sonic analysis. If they choose to proceed, they view the acquisition links.
6.  **Acquisition:** If the score is high enough (70%) the agent presents 2-3 direct links found via **Playwright** to buy the vinyl record.

### Collection Logging
1.  **Log Purchase:** User confirms they bought the record to add it to their digital "Physical Shelf."

## Data & Tech Constraints

### Data Strategy
- **Behavioral Input:** Uses streaming history to define the initial "Taste Centroid."
- **Audio Scoping:** Analysis focuses on **track-to-user similarity** across the entire album to ensure the "no-skip" principle is met.
- **Acquisition Data:** Uses live web scraping via Playwright to identify current stock and pricing.

### Technical Stack
- **Audio Math:** `librosa` for spectral analysis and extracting audio features.
- **Automation Layer:** `Playwright` for navigating e-commerce sites to find "places to buy."
- **Decision Layer:** A Python-based logic gate that translates the aggregate `UserFit` of all tracks into a percentage-based confidence score.

### Constraints & Considerations
- **User Agency:** The system must clearly present the data but never "force" a buy; the final "click to buy" is always user-initiated.
- **Scraper Maintenance:** Using Playwright for marketplace discovery requires regular updates to handle changes in retail site structures.
- **Static V1:** The recommendation score is based on the initial onboarding sync; it does not yet learn from purchase history.