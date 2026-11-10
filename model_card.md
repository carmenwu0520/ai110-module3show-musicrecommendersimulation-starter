# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

**Goal / task:** Given one listener's stated taste (favorite genre, mood, how energetic they want the music, and a few optional preferences), VibeFinder suggests the 5 songs from a small catalog that fit best, and says *why* each one was picked.

- **What it generates:** a ranked top-5 list with a score and a list of reasons for each song.
- **Assumptions about the user:** they can describe their taste in a few words ("pop, happy, high energy"), and their taste is the same all the time (no "workout mode" vs "sleep mode").
- **Intended use:** classroom exploration of how recommenders turn data into rankings, and where bias comes from.
- **Not intended for:** real users or a real product. It has no listening history, no real audio analysis, 22 made-up songs, and it should not be used to decide what music gets promoted to people or which artists get exposure.

---

## 3. How the Model Works

Think of it like a judge scoring every song on a checklist, then lining them up from highest to lowest.

For each song, the judge gives points:

- **Same genre as you like?** 2 points. A *related* genre (like "indie pop" when you said "pop") gets 1 point.
- **Same mood?** 1 point.
- **Energy close to what you want?** Up to 1.5 points. A perfect match gets all 1.5; the further away the song's energy is, the fewer points. This is important: it rewards being *close*, not just being loud or quiet.
- **Small bonuses (up to about 0.5–0.75 each)** if you said you like (or don't like) acoustic songs, want instrumental music or a live feel, prefer mainstream or underground songs, a certain decade, or a detailed mood like "nostalgic."

Every time a song earns points, the judge writes down a reason ("genre match: pop (+2.00)"), so the final list can explain itself.

Then the songs are sorted by total points and the top 5 are shown.

**Changes from the starter:** I implemented `load_songs`, `score_song`, and `recommend_songs` from scratch; added 12 songs and 5 new attributes; added "related genre" partial credit; added three switchable ranking modes (Genre-First, Mood-First, Energy-Focused) and an optional **diversity penalty** that takes 1 point off a song if its artist is already in the list and 0.5 off for the 3rd+ song of the same genre.

---

## 4. Data

- **Size:** 22 songs (10 from the starter + 12 added).
- **Attributes (15 columns):** id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness, and the 5 I added: **popularity** (0–100), **release_decade**, **mood_tag** (detailed mood, e.g. *euphoric*, *nostalgic*, *melancholic*), **instrumentalness**, **liveness**.
- **Genres (16):** lofi (4 songs), pop (3), synthwave (2), and one song each for indie pop, rock, ambient, jazz, r&b, hip-hop, edm, classical, country, metal, folk, reggae, blues.
- **Moods:** happy, chill, sad, intense, relaxed, moody, focused, romantic, confident, euphoric, melancholy, nostalgic, angry.
- **What I added:** genres and moods that were missing (sad, angry, romantic, nostalgic; hip-hop, classical, country, metal, folk, reggae, blues…), plus a few deliberate repeats (a 3rd Neon Echo song, a 2nd Max Pulse song, a 3rd LoRoom song) so I could test the diversity penalty.
- **Limits:** all values are hand-made, not measured from real audio. Half the catalog is from the 2020s. There's nothing for non-English music, Latin, K-pop, Afrobeats, etc. Most genres have exactly one song.

---

## 5. Strengths

- **Clear, "normal" profiles work well.** High-Energy Pop gets *Glitter Bomb*, *Sunrise City*, *Rooftop Lights*; Chill Lofi gets *Library Rain* and *Midnight Coding* — exactly what I'd pick by hand.
- **Energy closeness behaves correctly.** For Chill Lofi (energy 0.35), the calm ambient track *Spacewalk Thoughts* (0.28) appears, and loud tracks never do.
- **Explanations are honest.** Each reason is generated from the exact points that were added, so you can always see why a song ranked where it did (including penalties).
- **Related-genre credit helps.** *Rooftop Lights* (indie pop) shows up for pop fans instead of being treated as a total mismatch.

---

## 6. Limitations and Bias

**Main weakness I found: genre is treated as an exact text label, and it dominates the score.** For the *Deep Intense Rock* profile, there is only one rock song, so after *Storm Runner* the next pick is *Gym Hero* — a **pop** workout song — because it matches the "intense" mood and has high energy. Meanwhile *Iron Tide* (metal), which most rock fans would like more, comes in 5th, because the system has no idea metal and rock are related; "metal" ≠ "rock" as strings, so it gets 0 genre points. Combined with the dataset imbalance (4 lofi songs vs 1 rock song), this means **lofi fans get a full list of good matches while rock, metal, folk and blues fans get one good match and then filler.** The weights also create a filter bubble: with genre worth +2.0, a pop fan's top 4 is always pop or indie pop, and they'd rarely discover anything else unless you lower the genre weight or turn on the diversity penalty.

Other issues:

- **Conflicting tastes aren't handled.** A user who wants *sad* music at *energy 0.9* gets happy pop in Genre-First mode and slow sad songs in Mood-First mode. The system never says "nothing fits both."
- **Missing genres fail silently.** "k-pop" earns zero genre points, and the user isn't told; they just get happy/medium-energy songs.
- **Small preferences barely matter.** The "likes acoustic" flag is worth at most 0.5, so the *Acoustic Headbanger* profile (metal + likes acoustic) still gets the least acoustic song in the catalog at #1.
- **Popularity bias (optional):** the "mainstream" preference pushes already-popular songs higher, which in a real app would make popular artists even more popular.

---

## 7. Evaluation

### Profiles tested

| Profile | Prefs | Type |
|---|---|---|
| High-Energy Pop | pop, happy, energy 0.85, not acoustic, mainstream | normal |
| Chill Lofi | lofi, chill, energy 0.35, likes acoustic, instrumental | normal |
| Deep Intense Rock | rock, intense, energy 0.9, not acoustic | normal |
| Sad but Hyped | pop, sad, energy 0.9 | adversarial (conflicting) |
| Genre Not In Catalog | k-pop, happy, energy 0.7 | adversarial (missing genre) |
| Acoustic Headbanger | metal, angry, energy 0.95, likes acoustic | adversarial (conflicting) |

Full terminal outputs are in the README under **Experiments You Tried**. Short version (Genre-First, top 5):

```
High-Energy Pop     Glitter Bomb 5.37 | Sunrise City 5.31 | Gym Hero 4.28 | Rooftop Lights 4.04 | Neon Heartbeat 3.19
Chill Lofi          Library Rain 5.38 | Midnight Coding 5.17 | Late Bus Home 4.27 | Focus Flow 4.25 | Spacewalk Thoughts 3.33
Deep Intense Rock   Storm Runner 4.93 | Gym Hero 2.93 | Glitter Bomb 1.93 | Pulse Cathedral 1.91 | Iron Tide 1.89
Sad but Hyped       Glitter Bomb 3.47 | Gym Hero 3.46 | Sunrise City 3.38 | Rooftop Lights 2.29 | Rainy Day Blues 1.81
Genre Not In Cat.   Rooftop Lights 2.41 | Neon Heartbeat 2.35 | Sunrise City 2.32 | Glitter Bomb 2.23 | Night Drive Loop 1.42
Acoustic Headbanger Iron Tide 4.48 | Pulse Cathedral 1.51 | Gym Hero 1.50 | Storm Runner 1.49 | Glitter Bomb 1.44
```

### Comparing pairs of profiles

- **High-Energy Pop vs Chill Lofi:** completely different lists with zero overlap. Pop gets loud, danceable, non-acoustic songs (energy ~0.8–0.9); Lofi gets quiet, acoustic, instrumental tracks (energy ~0.3–0.4). That makes sense: they disagree on genre, mood, energy *and* acousticness, so every part of the score pulls in opposite directions.
- **High-Energy Pop vs Deep Intense Rock:** both want high energy, so they share songs — *Gym Hero* is #3 for pop and #2 for rock, and *Glitter Bomb* shows up in both. Why does *Gym Hero* keep showing up for people who just want "Happy Pop"? Because it's pop (+2.0) and very high energy (+1.3), so even without the "happy" mood it beats most non-pop songs. For the rock fan it matches "intense" (+1.0) and energy. It's the catalog's "generic workout banger" — close enough to everyone who wants loud music.
- **Chill Lofi vs Deep Intense Rock:** opposite ends. Rock's top 5 has scores dropping off a cliff after #1 (4.93 → 2.93) because only one song is really rock; Lofi's top 4 are all above 4.2 because there are 4 lofi songs. Same algorithm, very different quality — that's the dataset imbalance.
- **Sad but Hyped vs High-Energy Pop:** almost the same list (*Glitter Bomb*, *Gym Hero*, *Sunrise City*) even though one user wants **sad** music. The pop genre bonus and high energy outweigh the mood. Only at #5 does a sad song (*Rainy Day Blues*) appear. Switching to Mood-First flips it: the top 3 become sad, slow songs. Neither is "right" because the catalog has no sad + energetic song.
- **Genre Not In Catalog vs High-Energy Pop:** without any genre points, the k-pop fan's list is decided by mood + energy, so it's a mix of pop, indie pop and synthwave — reasonable, but scores are low (≈2.4) and there's no warning that "k-pop" wasn't found.
- **Acoustic Headbanger vs Deep Intense Rock:** *Iron Tide* wins easily because metal + angry is a perfect genre+mood match (+3.0); the "likes acoustic" preference adds only +0.01. The rest of the list is the same high-energy songs the rock fan gets. The conflicting preference is basically ignored.

### Experiment: double energy, halve genre (`--mode energy`)

The top 2 for each normal profile didn't change. Further down, songs from other genres with the right energy moved up (e.g. ambient *Spacewalk Thoughts* rose for Chill Lofi; hip-hop and synthwave got closer for High-Energy Pop) and the score gap between "perfect match" and "right energy, wrong genre" shrank. The recommendations got **different and more varied, not clearly more accurate**.

### What surprised me

How *convincing* the output looks just because each song has a list of reasons. Even the bad results (pop for a sad listener) come with confident, precise-looking explanations. Also, the diversity penalty of −1.0 wasn't strong enough to remove *Gym Hero* from High-Energy Pop's top 4 — I found that because a unit test I wrote expecting 4 different artists failed.

### Tests

`pytest` runs 7 tests: the 2 starter tests, plus CSV loading/number conversion, the exact score for a perfect match (4.5), energy closeness, sorting for all 6 profiles × 3 modes, and the diversity penalty increasing the number of different artists.

---

## 8. Future Work

1. **Genre similarity instead of exact text match** — e.g. a small map (metal ↔ rock, lofi ↔ ambient ↔ jazz) or numeric "genre vectors," so a rock fan gets *Iron Tide* before a pop song.
2. **Say when nothing fits.** If the best score is below a threshold, or a genre isn't in the catalog, tell the user instead of quietly returning filler.
3. **Balance the dataset** so every genre has several songs, and add listening history (skips, replays) for a simple collaborative-filtering signal.
4. **Tune the diversity penalty** (or use a proper method like MMR) so variety is guaranteed when the user asks for it.

---

## 9. Personal Reflection

> ✏️ *Draft — Carmen, rewrite this in your own words / add your own details before submitting.*

**Biggest learning moment:** realizing that "how good is this one song?" (scoring) and "what order do I show them in?" (ranking) are separate problems. The diversity penalty only makes sense in the ranking step, because whether a song is a repeat depends on what's already been picked.

**How AI tools helped, and when I double-checked:** I used Claude as an agent to generate the expanded dataset, write the first version of the scoring/ranking code and tests, and run all the profiles. I still had to check the results against my own intuition: the AI's first diversity test assumed a −1.0 artist penalty would always remove repeat artists from the top 4, and it failed — the math showed *Gym Hero* was strong enough to survive. That was a good reminder that AI-written tests and assumptions need to be checked against the actual numbers.

**What surprised me:** a few lines of arithmetic already "feel" like a real recommender, especially with reasons printed next to each song. The explanations make the system look smarter and more trustworthy than it really is.

**What I'd try next:** genre similarity, a "no good match" warning, and a small collaborative-filtering layer using fake listening histories, to see how the two approaches disagree.
