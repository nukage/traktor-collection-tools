# DJ Collection Manager

## Overview
AI-assisted system for curating, cleaning, and extending a Traktor DJ collection via natural language.

**Source of truth:** Traktor NML collection file (no Media Monkey bridge needed)

## Core Problem
- Researching new DJ music is time-consuming manual labor
- Metadata is unreliable or missing (no BPM, bad album info)
- Traktor + Media Monkey dual management creates sync friction
- No systematic way to discover "what's missing" based on existing collection

## Core Requirements

### 1. Collection Reader
- Parse Traktor NML XML file directly
- Extract: track title, artist, BPM (where available), file path, genre tags, playlist membership
- Understand what "electronic" vs "non-electronic" tracks look like in the collection
- Provide collection summary stats: total tracks, BPM distribution, genre spread, year distribution

### 2. Natural Language Playlist Builder
The user speaks to the system; it responds with curated playlists.

**Interface examples:**
- "Put together a drum & bass set for tonight, BPM 170-175, prefer recent releases"
- "Find me some jump-up drum & bass from 2019"
- "Create a playlist of tracks similar to what's in my \"Club Night\" playlist but faster"
- "What artists in my library released music in 2019 that I don't have yet?"

**Constraints:**
- BPM tolerance (e.g., ±5 BPM from seed tracks)
- Year range (specific year, decade, "older", "newer")
- Genre/subgenre tags
- Local-only vs local+internet mixed output
- Exclude tracks already in collection

### 3. Metadata Repair
- BPM extraction via audio analysis ( librosa or similar)
- Artist/album lookup via MusicBrainz/Discogs API
- Album art fetch
- Genre tagging (based on BPM range heuristics or MusicBrainz data)

### 4. Internet Discovery Agent
Given a seed playlist and constraints:
- Search Beatport, SoundCloud, YouTube for matching tracks
- Check against local collection (avoid dupes)
- Download new tracks to a "staging" location
- Return ranked recommendations (not auto-download by default)

### 5. Traktor Integration
- Detect watched folder or manual import directory
- Write new tracks to import location
- Alternatively: generate a new NML playlist that can be imported via drag-and-drop
- Track import status: which tracks are new vs already had

## Technical Stack
- **OpenCode** — coding agent for building/maintaining the system
- **NML parser** — Python xml.etree or similar for Traktor NML
- **BPM analysis** — librosa (Python)
- **Metadata APIs** — MusicBrainz, Discogs
- **Search** — SearXNG (already configured) for Beatport/SoundCloud/YouTube

## Phases

### Phase 1: Collection Audit ✅ DONE
- Locate Traktor NML file ✅ (confirmed example path)
- Parse and index existing collection ✅
- Output: searchable collection summary in Obsidian ✅

See `docs/STATUS.md` for current implementation status.

### Phase 2: Natural Language Interface ✅ DONE (CLI only)
- Read NML → build queryable structure ✅
- Allow user to ask playlist questions via CLI ✅
- Return track lists, not automatic imports ✅
- **Gap:** No natural language parsing (e.g., "put together a drum & bass set for tonight")

### Phase 3: Metadata Repair 🟡 PARTIAL
- Run BPM analysis on tracks missing BPM ✅ (librosa-based)
- Fill in artist/album/year from MusicBrainz ❌ (API not integrated)
- Album art fetch ❌
- Genre tagging (based on BPM range heuristics) ❌

### Phase 4: Discovery Agent
- Given seed tracks + constraints → search internet → recommend
- Add to collection pipeline

## NML File Location
Example file: `\\UNRAIDTOWER\Storage\Temp\collection.nml` (5,135 entries as of 2023/12/29)
Typical local path: `%APPDATA%\Native Instruments\Traktor\<version>\`


## Additional Requirements (2026-04-25)

### Duplicate Detection ✅ DONE
- Find near-identical files (same artist + title, different version/firmware)
- Identify which is newer/longer/better quality (scoring: file size, bitrate, playtime, plays, recency)
- Flag duplicates for manual review before deletion
- **Cue point rule:** Only merged when playtime matches within ±1 second
- **Merge behavior:** Best file wins, but metadata pulled from all variants (BPM, key, cues)
- **Output:** NML patch file for manual review before applying

### Own Tracks Discovery
- Locate production files (in Bitwig project folders or other music-making directories)
- Identify which tracks have been imported into Traktor vs which haven't
- Tag and organize releases/unfinished work separately from DJ source material
- Prevent "which version is this" confusion by establishing canonical naming/labeling

### Fresh Start Option
- Considering rebuilding collection from zero rather than migrating legacy mess
- If starting fresh: define what "DJ-ready" means (file format, tags present, BPM detected)
- Plan for clean import pipeline going forward


### Portable Collection
- All music on external USB drive (not local machine)
- Traktor configured to use relative paths so it works across computers
- Plug-and-play: plug drive into any machine with Traktor installed, collection works immediately
- Drive letter changes between computers break NML paths — system needs to handle this (rebase paths on scan, or use folder-relative locations)
- Note: Dropbox sync is storage-constrained, not a viable solution for full collection


## Traktor USB-First Setup (Rekordbox-style)

### Goal
All music lives on a single USB drive. Plug into any computer with Traktor installed, collection just works.

### Key Constraints
- **Cue points are in the NML file** — keep NML on USB with the audio files, cue points survive
- **Relative paths only** — no absolute Windows paths (`D:\Music\...`), all paths inside NML must be relative to where NML lives
- **Single source of truth** — no Dropbox, no network drives, no local AppData scattering. Everything on the USB
- **Flash drive size** — 256GB or 512GB flash drive available for fresh start; collection needs to fit
- **Migration problem** — existing collection is scattered across Dropbox, network drives, local folders. Need to consolidate onto USB without losing cue points on the tracks that have them

### Migration Steps
1. Export current NML (with cue points intact)
2. Copy all referenced audio files to USB folder structure
3. Update NML paths to be relative (not absolute)
4. Import new NML from USB on target machine
5. Verify cue points survived

### Open Question
- Traktor must be configured to use the USB NML as collection file, not the default AppData location. This is a settings change, not automatic.


### DJ-as-Pre-Recorded-Background + Live VJ Performance
- Pre-record a DJ mix (mixtape) once
- Perform the visual set live, synced to the pre-recorded audio
- Live element = VJ, not DJing
- Stepping stone toward simultaneous DJ+VJ; eventual goal: map one control to both audio and visuals simultaneously
- VJ exploration is a 2026 goal — mixtape + live VJ is the entry point

### Controller Mapping (Unified)
- Push + Launchpad used for both Traktor AND visual control
- Existing MIDI mappings from audio production template can be reused for visuals
- One button fires audio cue + visual cue together
- Semi-permanent keyboard stand mount for the setup


### Hardware Context Switching
- Jam setup reuses same gear as DJ + VJ setup — rewiring is the enemy
- Goal: software-layer switching without physical reconfiguration
- Bitwig as visual engine (no audio through Bitwig in this mode)
- Traktor as stable DJ audio ground
- Push + Launchpad as unified controller across both layers
- iPad as swappable top layer for Traktor-heavy moments, Push as anchor
- Minimizing cable swaps = reducing context-switch friction


### Unified Live Control (TouchOSC as the Bridge)
- TouchOSC as the unified MIDI/OSC layer across Bitwig AND Traktor simultaneously
- Same template controls both: Bitwig for visuals + live performance, Traktor for DJ audio
- Enables: own music performed live with synced visuals, plus DJ flexibility in same set
- TouchOSC template already exists from production work — reuse for live context
- iPad as TouchOSC host becomes the unified control surface for the whole rig


### Performance Template MVP (Minimum Viable Product)

**Two development tracks:**
1. **Audio-centric** — XY pad/crossfader transitions in Bitwig via TouchOSC (not clip-based). Crossfader and XY pad trigger both audio transitions AND visual changes simultaneously.
2. **Visual-centric** — Visuals react to transition engagement

**Control routing (MVP phase):**
- iPad (TouchOSC template) → controls Traktor directly
- Push pads inside Bitwig drum rack → mapped to Traktor cue points via MIDI
- Fader controller → feeds Bitwig AND Traktor simultaneously (MIDI passthrough)
- Result: full Bitwig control + full Traktor control + jam-setup-compatible hardware

**Master audio passthrough (new capability):**
- Traktor master out → audio interface input → Bitwig
- Bitwig applies real-time effects (reverb, delay, spatial) to the DJ mix live
- Effects output → speakers
- Enables: live FX processing on DJ audio without separate effects hardware

**Technical notes:**
- Drum rack approach lets Push pads route MIDI to Traktor while remaining inside Bitwig plugin chain
- Master audio passthrough is simpler than stem routing (no need to split stems)
- This setup closely mirrors existing jam hardware configuration — same gear, different routing


### VJ/Streaming Automation Pipeline

**Stream setup labor (the friction points):**
- Stream title/description: need guidelines for naming convention, then auto-populate per platform
- Thumbnail generation: screenshots don't click. Need actual thumbnail art that represents the set. AI-generated using Stable Diffusion art as reference.
- Multi-platform streaming: title needs to change per platform based on what you're doing
- Analytics review: identify which sets/clips performed well, flag for follow-up

**AI-generated visuals for VJ sets:**
- WAN 2.2 (likely Wan 2.1 or similar video model) + Stable Diffusion for artwork
- LLM as prompt assistant: "here's what I like, here's reference images, generate me X variations"
- Workflow: reference images → LLM prompt suggestions → generate images → curate → convert → Resolume-ready format

**Format conversion (web → Resolume):**
- Web video formats (MP4, WebM from generation tools) don't play well with Resolume
- Need automated transcoding to Resolume-compatible format (likely ProRes or high-bitrate MJPEG AVI)
- Naming + folder organization automated post-conversion

**Clip creation from streams:**
- Extract best moments post-stream
- Automated clip segmentation? (FireCut or similar — Tom already researched this)

**Thumbnail pipeline:**
- Stable Diffusion or similar → generate thumbnail art based on set mood/genre
- LLM suggests prompt variations from reference images Tom provides
- Batch generate → curate → use

**Full pipeline stages:**
1. Pre-stream: generate thumbnail art + stream title (LLM-assisted)
2. During stream: record, optionally generate AI visual layer
3. Post-stream: transcode footage → extract clips → generate social-ready versions
4. Analytics: aggregate performance data, flag high-performers for deeper clip promotion