# 🎵 Music Recommender Simulation — VibeFinder 1.0

## Project Summary

VibeFinder is a small **content-based** music recommender written in Python. It reads a 22-song catalog from `data/songs.csv`, compares every song to a user's "taste profile" (favorite genre, mood, target energy, and a few optional preferences), gives each song a point score with a list of human-readable reasons, and returns the top 5. You can switch between three ranking strategies (Genre-First, Mood-First, Energy-Focused), turn on a diversity penalty so one artist can't take over the list, and see results in a formatted terminal table.

---

## How The System Works

### How real recommenders do it

Apps like Spotify and YouTube mix two big ideas:

- **Collaborative filtering** — "people who behave like you also liked X." It uses *behavior* data from millions of users: plays, skips, likes, saves, playlist adds, how long you listened. It doesn't need to know anything about the song itself.
- **Content-based filtering** — "this song *sounds like* the songs you like." It uses *attributes of the song*: genre, tempo, energy, mood, acousticness, and audio features extracted from the waveform.

Real systems combine both, plus context (time of day, device, what you just played). They also separate three things that are easy to blur together:

1. **Input data** — facts about songs (features) and logs of user behavior.
2. **User preferences** — a learned or stated representation of one person's taste.
3. **Ranking / selection** — the rule that turns "how well does each song fit?" into an ordered list (and often re-ranks for diversity, freshness, or business goals).

### What my version does

My simulation is **content-based only** — there are no other users, so there's nothing to "collaborate" on. It keeps the three layers separate:

- **Input data (`Song`)**: `genre`, `mood`, `energy`, `tempo_bpm`, `valence`, `danceability`, `acousticness`, plus five added attributes: `popularity` (0–100), `release_decade`, `mood_tag` (detailed mood like *nostalgic*, *euphoric*), `instrumentalness`, `liveness`.
- **User preferences (`UserProfile` / prefs dict)**: `genre`, `mood`, `energy` (target 0–1), and optional `likes_acoustic`, `valence`, `danceability`, `mood_tag`, `decade`, `popularity` ("mainstream" / "underground"), `wants_instrumental`, `likes_live`.
- **Scoring Rule** (one song) → `score_song()` returns `(score, reasons)`.
- **Ranking Rule** (whole catalog) → `recommend_songs()` scores *every* song, sorts high → low, and takes the top k (optionally re-ranking for diversity).

We need both rules: the scoring rule only knows how good *one* song is; the ranking rule is what compares songs to each other and decides the order and cut-off.

### Algorithm Recipe (Genre-First, the default)

| Signal | Points |
|---|---|
| Exact genre match | **+2.0** |
| Related genre (shares a word, e.g. *indie pop* vs *pop*) | +1.0 |
| Mood match | **+1.0** |
| Energy closeness | **+1.5 × (1 − \|song energy − target\|)** |
| Acoustic preference | +0.5 × acousticness (or × (1 − acousticness) if they *don't* like acoustic) |
| Valence / danceability closeness (if given) | +0.5 × closeness each |
| Detailed mood tag match | +0.75 |
| Preferred release decade | +0.5 |
| Mainstream / underground | +0.5 × popularity/100 (or the reverse) |
| Wants instrumental | +0.5 × instrumentalness |
| Likes live recordings | +0.5 × liveness |

Energy uses **closeness**, not "higher is better": a song at 0.45 beats a song at 0.95 for someone who wants 0.40.

Data flow:

```
User prefs ──► for every song in songs.csv: score_song(prefs, song) ──► (song, score, reasons)
                                                                            │
                                    sorted(..., reverse=True) ◄──────────────┘
                                                │
                         (optional) diversity re-rank: −1.0 repeat artist, −0.5 for 3rd+ same genre
                                                │
                                         Top K recommendations
```

**Biases I expected before testing:** genre is worth the most, so the system will probably over-prioritize genre and ignore a great mood match from a different genre; and because most genres only have 1–2 songs, fans of small genres will run out of real matches fast.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python -m src.main                                # default pop/happy profile
   python -m src.main --all                          # all 6 test profiles
   python -m src.main --all --mode mood              # Mood-First ranking
   python -m src.main --all --mode energy            # Energy-Focused ranking
   python -m src.main --profile "Chill Lofi" --diverse   # with diversity penalty
   ```

### Running Tests

```bash
pytest
```

7 tests cover CSV loading, the scoring math, sorting for every profile × every mode, and the diversity penalty.

---

## Sample Recommendation Output

Default profile (`genre=pop, mood=happy, energy=0.8`), Genre-First mode:

```
Loaded songs: 22

=== Default (pop / happy) ===
Profile: genre=pop, mood=happy, energy=0.8
Mode: Genre-First
┌─────┬────────────────┬───────────────┬───────────┬─────────┬──────────────────────────────────────────────────┐
│ #   │ Title          │ Artist        │ Genre     │ Score   │ Why                                              │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 1   │ Sunrise City   │ Neon Echo     │ pop       │ 4.47    │ genre match: pop (+2.00) | mood match: happy     │
│     │                │               │           │         │ (+1.00) | energy 0.82 vs target 0.80 (+1.47)     │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 2   │ Glitter Bomb   │ Max Pulse     │ pop       │ 4.38    │ genre match: pop (+2.00) | mood match: happy     │
│     │                │               │           │         │ (+1.00) | energy 0.88 vs target 0.80 (+1.38)     │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 3   │ Rooftop Lights │ Indigo Parade │ indie pop │ 3.44    │ related genre: indie pop (+1.00) | mood match:   │
│     │                │               │           │         │ happy (+1.00) | energy 0.76 vs target 0.80       │
│     │                │               │           │         │ (+1.44)                                          │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 4   │ Gym Hero       │ Max Pulse     │ pop       │ 3.30    │ genre match: pop (+2.00) | energy 0.93 vs target │
│     │                │               │           │         │ 0.80 (+1.30)                                     │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 5   │ Neon Heartbeat │ Neon Echo     │ synthwave │ 2.50    │ mood match: happy (+1.00) | energy 0.80 vs       │
│     │                │               │           │         │ target 0.80 (+1.50)                              │
└─────┴────────────────┴───────────────┴───────────┴─────────┴──────────────────────────────────────────────────┘
```

---

## Experiments You Tried

### 1. Six user profiles (3 normal + 3 adversarial)

All runs use Genre-First mode, top 5. Full commentary is in the [model card](model_card.md#7-evaluation).

```
Loaded songs: 22

=== High-Energy Pop ===
Profile: genre=pop, mood=happy, energy=0.85, likes_acoustic=False, popularity=mainstream
Mode: Genre-First
┌─────┬────────────────┬───────────────┬───────────┬─────────┬──────────────────────────────────────────────────┐
│ #   │ Title          │ Artist        │ Genre     │ Score   │ Why                                              │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 1   │ Glitter Bomb   │ Max Pulse     │ pop       │ 5.37    │ genre match: pop (+2.00) | mood match: happy     │
│     │                │               │           │         │ (+1.00) | energy 0.88 vs target 0.85 (+1.46) |   │
│     │                │               │           │         │ non-acoustic sound (+0.46) | mainstream pick,    │
│     │                │               │           │         │ popularity 90 (+0.45)                            │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 2   │ Sunrise City   │ Neon Echo     │ pop       │ 5.31    │ genre match: pop (+2.00) | mood match: happy     │
│     │                │               │           │         │ (+1.00) | energy 0.82 vs target 0.85 (+1.46) |   │
│     │                │               │           │         │ non-acoustic sound (+0.41) | mainstream pick,    │
│     │                │               │           │         │ popularity 88 (+0.44)                            │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 3   │ Gym Hero       │ Max Pulse     │ pop       │ 4.28    │ genre match: pop (+2.00) | energy 0.93 vs target │
│     │                │               │           │         │ 0.85 (+1.38) | non-acoustic sound (+0.47) |      │
│     │                │               │           │         │ mainstream pick, popularity 84 (+0.42)           │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 4   │ Rooftop Lights │ Indigo Parade │ indie pop │ 4.04    │ related genre: indie pop (+1.00) | mood match:   │
│     │                │               │           │         │ happy (+1.00) | energy 0.76 vs target 0.85       │
│     │                │               │           │         │ (+1.36) | non-acoustic sound (+0.33) |           │
│     │                │               │           │         │ mainstream pick, popularity 70 (+0.35)           │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 5   │ Neon Heartbeat │ Neon Echo     │ synthwave │ 3.19    │ mood match: happy (+1.00) | energy 0.80 vs       │
│     │                │               │           │         │ target 0.85 (+1.43) | non-acoustic sound (+0.42) │
│     │                │               │           │         │ | mainstream pick, popularity 69 (+0.34)         │
└─────┴────────────────┴───────────────┴───────────┴─────────┴──────────────────────────────────────────────────┘

=== Chill Lofi ===
Profile: genre=lofi, mood=chill, energy=0.35, likes_acoustic=True, wants_instrumental=True
Mode: Genre-First
┌─────┬────────────────────┬────────────────┬─────────┬─────────┬────────────────────────────────────────────────┐
│ #   │ Title              │ Artist         │ Genre   │ Score   │ Why                                            │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 1   │ Library Rain       │ Paper Lanterns │ lofi    │ 5.38    │ genre match: lofi (+2.00) | mood match: chill  │
│     │                    │                │         │         │ (+1.00) | energy 0.35 vs target 0.35 (+1.50) | │
│     │                    │                │         │         │ acoustic sound (+0.43) | instrumental (+0.45)  │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 2   │ Midnight Coding    │ LoRoom         │ lofi    │ 5.17    │ genre match: lofi (+2.00) | mood match: chill  │
│     │                    │                │         │         │ (+1.00) | energy 0.42 vs target 0.35 (+1.40) | │
│     │                    │                │         │         │ acoustic sound (+0.35) | instrumental (+0.42)  │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 3   │ Late Bus Home      │ LoRoom         │ lofi    │ 4.27    │ genre match: lofi (+2.00) | energy 0.33 vs     │
│     │                    │                │         │         │ target 0.35 (+1.47) | acoustic sound (+0.40) | │
│     │                    │                │         │         │ instrumental (+0.40)                           │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 4   │ Focus Flow         │ LoRoom         │ lofi    │ 4.25    │ genre match: lofi (+2.00) | energy 0.40 vs     │
│     │                    │                │         │         │ target 0.35 (+1.42) | acoustic sound (+0.39) | │
│     │                    │                │         │         │ instrumental (+0.44)                           │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 5   │ Spacewalk Thoughts │ Orbit Bloom    │ ambient │ 3.33    │ mood match: chill (+1.00) | energy 0.28 vs     │
│     │                    │                │         │         │ target 0.35 (+1.40) | acoustic sound (+0.46) | │
│     │                    │                │         │         │ instrumental (+0.47)                           │
└─────┴────────────────────┴────────────────┴─────────┴─────────┴────────────────────────────────────────────────┘

=== Deep Intense Rock ===
Profile: genre=rock, mood=intense, energy=0.9, likes_acoustic=False
Mode: Genre-First
┌─────┬─────────────────┬──────────────┬─────────┬─────────┬──────────────────────────────────────────────────┐
│ #   │ Title           │ Artist       │ Genre   │ Score   │ Why                                              │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 1   │ Storm Runner    │ Voltline     │ rock    │ 4.93    │ genre match: rock (+2.00) | mood match: intense  │
│     │                 │              │         │         │ (+1.00) | energy 0.91 vs target 0.90 (+1.48) |   │
│     │                 │              │         │         │ non-acoustic sound (+0.45)                       │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 2   │ Gym Hero        │ Max Pulse    │ pop     │ 2.93    │ mood match: intense (+1.00) | energy 0.93 vs     │
│     │                 │              │         │         │ target 0.90 (+1.46) | non-acoustic sound (+0.47) │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 3   │ Glitter Bomb    │ Max Pulse    │ pop     │ 1.93    │ energy 0.88 vs target 0.90 (+1.47) | non-        │
│     │                 │              │         │         │ acoustic sound (+0.46)                           │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 4   │ Pulse Cathedral │ Dyna Lux     │ edm     │ 1.91    │ energy 0.95 vs target 0.90 (+1.43) | non-        │
│     │                 │              │         │         │ acoustic sound (+0.48)                           │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 5   │ Iron Tide       │ Grave Signal │ metal   │ 1.89    │ energy 0.97 vs target 0.90 (+1.40) | non-        │
│     │                 │              │         │         │ acoustic sound (+0.49)                           │
└─────┴─────────────────┴──────────────┴─────────┴─────────┴──────────────────────────────────────────────────┘

=== Sad but Hyped (conflict) ===
Profile: genre=pop, mood=sad, energy=0.9
Mode: Genre-First
┌─────┬─────────────────┬───────────────┬───────────┬─────────┬──────────────────────────────────────────────────┐
│ #   │ Title           │ Artist        │ Genre     │ Score   │ Why                                              │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 1   │ Glitter Bomb    │ Max Pulse     │ pop       │ 3.47    │ genre match: pop (+2.00) | energy 0.88 vs target │
│     │                 │               │           │         │ 0.90 (+1.47)                                     │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 2   │ Gym Hero        │ Max Pulse     │ pop       │ 3.46    │ genre match: pop (+2.00) | energy 0.93 vs target │
│     │                 │               │           │         │ 0.90 (+1.46)                                     │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 3   │ Sunrise City    │ Neon Echo     │ pop       │ 3.38    │ genre match: pop (+2.00) | energy 0.82 vs target │
│     │                 │               │           │         │ 0.90 (+1.38)                                     │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 4   │ Rooftop Lights  │ Indigo Parade │ indie pop │ 2.29    │ related genre: indie pop (+1.00) | energy 0.76   │
│     │                 │               │           │         │ vs target 0.90 (+1.29)                           │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 5   │ Rainy Day Blues │ Delta Moss    │ blues     │ 1.81    │ mood match: sad (+1.00) | energy 0.44 vs target  │
│     │                 │               │           │         │ 0.90 (+0.81)                                     │
└─────┴─────────────────┴───────────────┴───────────┴─────────┴──────────────────────────────────────────────────┘

=== Genre Not In Catalog ===
Profile: genre=k-pop, mood=happy, energy=0.7
Mode: Genre-First
┌─────┬──────────────────┬───────────────┬───────────┬─────────┬────────────────────────────────────────────┐
│ #   │ Title            │ Artist        │ Genre     │ Score   │ Why                                        │
├─────┼──────────────────┼───────────────┼───────────┼─────────┼────────────────────────────────────────────┤
│ 1   │ Rooftop Lights   │ Indigo Parade │ indie pop │ 2.41    │ mood match: happy (+1.00) | energy 0.76 vs │
│     │                  │               │           │         │ target 0.70 (+1.41)                        │
├─────┼──────────────────┼───────────────┼───────────┼─────────┼────────────────────────────────────────────┤
│ 2   │ Neon Heartbeat   │ Neon Echo     │ synthwave │ 2.35    │ mood match: happy (+1.00) | energy 0.80 vs │
│     │                  │               │           │         │ target 0.70 (+1.35)                        │
├─────┼──────────────────┼───────────────┼───────────┼─────────┼────────────────────────────────────────────┤
│ 3   │ Sunrise City     │ Neon Echo     │ pop       │ 2.32    │ mood match: happy (+1.00) | energy 0.82 vs │
│     │                  │               │           │         │ target 0.70 (+1.32)                        │
├─────┼──────────────────┼───────────────┼───────────┼─────────┼────────────────────────────────────────────┤
│ 4   │ Glitter Bomb     │ Max Pulse     │ pop       │ 2.23    │ mood match: happy (+1.00) | energy 0.88 vs │
│     │                  │               │           │         │ target 0.70 (+1.23)                        │
├─────┼──────────────────┼───────────────┼───────────┼─────────┼────────────────────────────────────────────┤
│ 5   │ Night Drive Loop │ Neon Echo     │ synthwave │ 1.42    │ energy 0.75 vs target 0.70 (+1.42)         │
└─────┴──────────────────┴───────────────┴───────────┴─────────┴────────────────────────────────────────────┘

=== Acoustic Headbanger (conflict) ===
Profile: genre=metal, mood=angry, energy=0.95, likes_acoustic=True
Mode: Genre-First
┌─────┬─────────────────┬──────────────┬─────────┬─────────┬────────────────────────────────────────────────┐
│ #   │ Title           │ Artist       │ Genre   │ Score   │ Why                                            │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 1   │ Iron Tide       │ Grave Signal │ metal   │ 4.48    │ genre match: metal (+2.00) | mood match: angry │
│     │                 │              │         │         │ (+1.00) | energy 0.97 vs target 0.95 (+1.47) | │
│     │                 │              │         │         │ acoustic sound (+0.01)                         │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 2   │ Pulse Cathedral │ Dyna Lux     │ edm     │ 1.51    │ energy 0.95 vs target 0.95 (+1.50) | acoustic  │
│     │                 │              │         │         │ sound (+0.01)                                  │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 3   │ Gym Hero        │ Max Pulse    │ pop     │ 1.50    │ energy 0.93 vs target 0.95 (+1.47) | acoustic  │
│     │                 │              │         │         │ sound (+0.03)                                  │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 4   │ Storm Runner    │ Voltline     │ rock    │ 1.49    │ energy 0.91 vs target 0.95 (+1.44) | acoustic  │
│     │                 │              │         │         │ sound (+0.05)                                  │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 5   │ Glitter Bomb    │ Max Pulse    │ pop     │ 1.44    │ energy 0.88 vs target 0.95 (+1.40) | acoustic  │
│     │                 │              │         │         │ sound (+0.04)                                  │
└─────┴─────────────────┴──────────────┴─────────┴─────────┴────────────────────────────────────────────────┘
```

### 2. Weight shift: double energy, halve genre (`--mode energy`)

Energy weight 1.5 → 3.0, genre weight 2.0 → 1.0.

```
Loaded songs: 22

=== High-Energy Pop ===
Profile: genre=pop, mood=happy, energy=0.85, likes_acoustic=False, popularity=mainstream
Mode: Energy-Focused
┌─────┬────────────────┬───────────────┬───────────┬─────────┬──────────────────────────────────────────────────┐
│ #   │ Title          │ Artist        │ Genre     │ Score   │ Why                                              │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 1   │ Glitter Bomb   │ Max Pulse     │ pop       │ 5.82    │ genre match: pop (+1.00) | mood match: happy     │
│     │                │               │           │         │ (+1.00) | energy 0.88 vs target 0.85 (+2.91) |   │
│     │                │               │           │         │ non-acoustic sound (+0.46) | mainstream pick,    │
│     │                │               │           │         │ popularity 90 (+0.45)                            │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 2   │ Sunrise City   │ Neon Echo     │ pop       │ 5.76    │ genre match: pop (+1.00) | mood match: happy     │
│     │                │               │           │         │ (+1.00) | energy 0.82 vs target 0.85 (+2.91) |   │
│     │                │               │           │         │ non-acoustic sound (+0.41) | mainstream pick,    │
│     │                │               │           │         │ popularity 88 (+0.44)                            │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 3   │ Rooftop Lights │ Indigo Parade │ indie pop │ 4.91    │ related genre: indie pop (+0.50) | mood match:   │
│     │                │               │           │         │ happy (+1.00) | energy 0.76 vs target 0.85       │
│     │                │               │           │         │ (+2.73) | non-acoustic sound (+0.33) |           │
│     │                │               │           │         │ mainstream pick, popularity 70 (+0.35)           │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 4   │ Gym Hero       │ Max Pulse     │ pop       │ 4.65    │ genre match: pop (+1.00) | energy 0.93 vs target │
│     │                │               │           │         │ 0.85 (+2.76) | non-acoustic sound (+0.47) |      │
│     │                │               │           │         │ mainstream pick, popularity 84 (+0.42)           │
├─────┼────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 5   │ Neon Heartbeat │ Neon Echo     │ synthwave │ 4.62    │ mood match: happy (+1.00) | energy 0.80 vs       │
│     │                │               │           │         │ target 0.85 (+2.85) | non-acoustic sound (+0.42) │
│     │                │               │           │         │ | mainstream pick, popularity 69 (+0.34)         │
└─────┴────────────────┴───────────────┴───────────┴─────────┴──────────────────────────────────────────────────┘
```

```
Loaded songs: 22

=== Chill Lofi ===
Profile: genre=lofi, mood=chill, energy=0.35, likes_acoustic=True, wants_instrumental=True
Mode: Energy-Focused
┌─────┬────────────────────┬────────────────┬─────────┬─────────┬────────────────────────────────────────────────┐
│ #   │ Title              │ Artist         │ Genre   │ Score   │ Why                                            │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 1   │ Library Rain       │ Paper Lanterns │ lofi    │ 5.88    │ genre match: lofi (+1.00) | mood match: chill  │
│     │                    │                │         │         │ (+1.00) | energy 0.35 vs target 0.35 (+3.00) | │
│     │                    │                │         │         │ acoustic sound (+0.43) | instrumental (+0.45)  │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 2   │ Midnight Coding    │ LoRoom         │ lofi    │ 5.57    │ genre match: lofi (+1.00) | mood match: chill  │
│     │                    │                │         │         │ (+1.00) | energy 0.42 vs target 0.35 (+2.79) | │
│     │                    │                │         │         │ acoustic sound (+0.35) | instrumental (+0.42)  │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 3   │ Late Bus Home      │ LoRoom         │ lofi    │ 4.74    │ genre match: lofi (+1.00) | energy 0.33 vs     │
│     │                    │                │         │         │ target 0.35 (+2.94) | acoustic sound (+0.40) | │
│     │                    │                │         │         │ instrumental (+0.40)                           │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 4   │ Spacewalk Thoughts │ Orbit Bloom    │ ambient │ 4.72    │ mood match: chill (+1.00) | energy 0.28 vs     │
│     │                    │                │         │         │ target 0.35 (+2.79) | acoustic sound (+0.46) | │
│     │                    │                │         │         │ instrumental (+0.47)                           │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 5   │ Focus Flow         │ LoRoom         │ lofi    │ 4.68    │ genre match: lofi (+1.00) | energy 0.40 vs     │
│     │                    │                │         │         │ target 0.35 (+2.85) | acoustic sound (+0.39) | │
│     │                    │                │         │         │ instrumental (+0.44)                           │
└─────┴────────────────────┴────────────────┴─────────┴─────────┴────────────────────────────────────────────────┘
```

**What changed:** the top 2 for both profiles stayed the same (they match genre, mood *and* energy, so they win under any weights). Below that, songs from *other* genres with the right energy moved up: for Chill Lofi, the ambient track *Spacewalk Thoughts* climbs, and the gap between "perfect match" and "just right energy" shrinks a lot. It made the list **different and a bit more varied, not clearly more accurate** — a pop fan now gets a hip-hop or synthwave song sooner, which some people would like and others wouldn't.

### 3. Mood-First mode on the conflicting "Sad but Hyped" profile

```
Loaded songs: 22

=== Sad but Hyped (conflict) ===
Profile: genre=pop, mood=sad, energy=0.9
Mode: Mood-First
┌─────┬─────────────────┬──────────────┬─────────┬─────────┬──────────────────────────────────────────────────┐
│ #   │ Title           │ Artist       │ Genre   │ Score   │ Why                                              │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 1   │ Rainy Day Blues │ Delta Moss   │ blues   │ 2.81    │ mood match: sad (+2.00) | energy 0.44 vs target  │
│     │                 │              │         │         │ 0.90 (+0.81)                                     │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 2   │ Late Bus Home   │ LoRoom       │ lofi    │ 2.65    │ mood match: sad (+2.00) | energy 0.33 vs target  │
│     │                 │              │         │         │ 0.90 (+0.64)                                     │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 3   │ Paper Boats     │ Willow & Ash │ folk    │ 2.60    │ mood match: sad (+2.00) | energy 0.30 vs target  │
│     │                 │              │         │         │ 0.90 (+0.60)                                     │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 4   │ Glitter Bomb    │ Max Pulse    │ pop     │ 2.47    │ genre match: pop (+1.00) | energy 0.88 vs target │
│     │                 │              │         │         │ 0.90 (+1.47)                                     │
├─────┼─────────────────┼──────────────┼─────────┼─────────┼──────────────────────────────────────────────────┤
│ 5   │ Gym Hero        │ Max Pulse    │ pop     │ 2.46    │ genre match: pop (+1.00) | energy 0.93 vs target │
│     │                 │              │         │         │ 0.90 (+1.46)                                     │
└─────┴─────────────────┴──────────────┴─────────┴─────────┴──────────────────────────────────────────────────┘
```

In Genre-First mode this user got happy pop bangers (genre won). In Mood-First mode they get slow sad songs (mood won). **Neither one actually satisfies "sad + energy 0.9"** — there's no sad high-energy song in the catalog, so the system just follows whichever weight is bigger.

### 4. Diversity penalty (`--diverse`)

```
Loaded songs: 22

=== High-Energy Pop ===
Profile: genre=pop, mood=happy, energy=0.85, likes_acoustic=False, popularity=mainstream
Mode: Genre-First + diversity penalty
┌─────┬─────────────────┬───────────────┬───────────┬─────────┬──────────────────────────────────────────────────┐
│ #   │ Title           │ Artist        │ Genre     │ Score   │ Why                                              │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 1   │ Glitter Bomb    │ Max Pulse     │ pop       │ 5.37    │ genre match: pop (+2.00) | mood match: happy     │
│     │                 │               │           │         │ (+1.00) | energy 0.88 vs target 0.85 (+1.46) |   │
│     │                 │               │           │         │ non-acoustic sound (+0.46) | mainstream pick,    │
│     │                 │               │           │         │ popularity 90 (+0.45)                            │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 2   │ Sunrise City    │ Neon Echo     │ pop       │ 5.31    │ genre match: pop (+2.00) | mood match: happy     │
│     │                 │               │           │         │ (+1.00) | energy 0.82 vs target 0.85 (+1.46) |   │
│     │                 │               │           │         │ non-acoustic sound (+0.41) | mainstream pick,    │
│     │                 │               │           │         │ popularity 88 (+0.44)                            │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 3   │ Rooftop Lights  │ Indigo Parade │ indie pop │ 4.04    │ related genre: indie pop (+1.00) | mood match:   │
│     │                 │               │           │         │ happy (+1.00) | energy 0.76 vs target 0.85       │
│     │                 │               │           │         │ (+1.36) | non-acoustic sound (+0.33) |           │
│     │                 │               │           │         │ mainstream pick, popularity 70 (+0.35)           │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 4   │ Gym Hero        │ Max Pulse     │ pop       │ 2.78    │ genre match: pop (+2.00) | energy 0.93 vs target │
│     │                 │               │           │         │ 0.85 (+1.38) | non-acoustic sound (+0.47) |      │
│     │                 │               │           │         │ mainstream pick, popularity 84 (+0.42) | repeat  │
│     │                 │               │           │         │ artist (-1.00) | 3rd+ pop song (-0.50)           │
├─────┼─────────────────┼───────────────┼───────────┼─────────┼──────────────────────────────────────────────────┤
│ 5   │ Concrete Verses │ MC Kestrel    │ hip-hop   │ 2.24    │ energy 0.78 vs target 0.85 (+1.40) | non-        │
│     │                 │               │           │         │ acoustic sound (+0.44) | mainstream pick,        │
│     │                 │               │           │         │ popularity 81 (+0.41)                            │
└─────┴─────────────────┴───────────────┴───────────┴─────────┴──────────────────────────────────────────────────┘
```

```
Loaded songs: 22

=== Chill Lofi ===
Profile: genre=lofi, mood=chill, energy=0.35, likes_acoustic=True, wants_instrumental=True
Mode: Genre-First + diversity penalty
┌─────┬────────────────────┬────────────────┬─────────┬─────────┬────────────────────────────────────────────────┐
│ #   │ Title              │ Artist         │ Genre   │ Score   │ Why                                            │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 1   │ Library Rain       │ Paper Lanterns │ lofi    │ 5.38    │ genre match: lofi (+2.00) | mood match: chill  │
│     │                    │                │         │         │ (+1.00) | energy 0.35 vs target 0.35 (+1.50) | │
│     │                    │                │         │         │ acoustic sound (+0.43) | instrumental (+0.45)  │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 2   │ Midnight Coding    │ LoRoom         │ lofi    │ 5.17    │ genre match: lofi (+2.00) | mood match: chill  │
│     │                    │                │         │         │ (+1.00) | energy 0.42 vs target 0.35 (+1.40) | │
│     │                    │                │         │         │ acoustic sound (+0.35) | instrumental (+0.42)  │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 3   │ Spacewalk Thoughts │ Orbit Bloom    │ ambient │ 3.33    │ mood match: chill (+1.00) | energy 0.28 vs     │
│     │                    │                │         │         │ target 0.35 (+1.40) | acoustic sound (+0.46) | │
│     │                    │                │         │         │ instrumental (+0.47)                           │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 4   │ Late Bus Home      │ LoRoom         │ lofi    │ 2.77    │ genre match: lofi (+2.00) | energy 0.33 vs     │
│     │                    │                │         │         │ target 0.35 (+1.47) | acoustic sound (+0.40) | │
│     │                    │                │         │         │ instrumental (+0.40) | repeat artist (-1.00) | │
│     │                    │                │         │         │ 3rd+ lofi song (-0.50)                         │
├─────┼────────────────────┼────────────────┼─────────┼─────────┼────────────────────────────────────────────────┤
│ 5   │ Focus Flow         │ LoRoom         │ lofi    │ 2.75    │ genre match: lofi (+2.00) | energy 0.40 vs     │
│     │                    │                │         │         │ target 0.35 (+1.42) | acoustic sound (+0.39) | │
│     │                    │                │         │         │ instrumental (+0.44) | repeat artist (-1.00) | │
│     │                    │                │         │         │ 3rd+ lofi song (-0.50)                         │
└─────┴────────────────────┴────────────────┴─────────┴─────────┴────────────────────────────────────────────────┘
```

Without the penalty, High-Energy Pop had 2 Max Pulse songs and 2 Neon Echo songs in the top 5. With it, the hip-hop track *Concrete Verses* gets in. For Chill Lofi, LoRoom had 3 of the top 5; with the penalty, the ambient track takes one of those spots. A −1.0 artist penalty was **not** enough to push *Gym Hero* out of the top 4, though — it's a strong enough match to survive.

---

## Limitations and Risks

- Tiny catalog (22 songs) and most genres have only 1 song, so "rock fan" really means "the one rock song, then random high-energy stuff."
- Genres are matched as **text**: the system doesn't know metal is close to rock, so *Iron Tide* ranks below *Gym Hero* (pop) for a rock fan.
- It can't handle conflicting tastes (sad + high energy); it just obeys the largest weight.
- No lyrics, language, listening history, or context (time of day, activity).
- Feature values are hand-made, not measured from real audio.

More detail in the [model card](model_card.md).

---

## Reflection

Read the full write-up in [**model_card.md**](model_card.md).

The biggest thing I learned is how little it takes for something to *feel* like a recommendation. Three rules — match genre, match mood, be close on energy — already produce lists that look reasonable, and printing the "reasons" next to each song makes them look even smarter than they are. But the moment I tried an unusual profile (sad + high energy, or a genre that isn't in the catalog), the system didn't say "I don't have a good match"; it confidently returned whatever scored highest. Real apps have the same problem at a much bigger scale.

Bias shows up in two places: the **weights** (genre at +2.0 means a pop fan basically only sees pop) and the **data** (lofi has 4 songs while rock, metal, folk and blues have 1 each, so lofi fans get great lists and rock fans don't). Neither is visible to the user unless you print the reasons — which is a good argument for explainable recommendations.
