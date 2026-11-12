---
name: wbrs-psychoacoustic-mix
description: >-
  Psychoacoustic music selection, harmonic CQT scale auditing, middle-octave register
  protection, diatonically tuned SFX synthesis, and broadcast EBU R128 (-14.0 LUFS)
  mastering runbook for Webres Studio (WVF). Prevents minor/chromatic dissonance,
  piercing high-octave or erratic sub-octave jumps ("octavas raras"), syncopated
  brass/punch hits, bar-skip splices, and muffled or overpowering music beds. Use
  whenever generating tracks in FlowMusic, auditing .m4a/.wav candidates, synthesizing
  cues, or mixing voice + music in WVF projects.
---

# WBRS Psychoacoustic Music & Broadcast Mix Engineering (`wbrs-psychoacoustic-mix`)

Distilled from 4 controlled acoustic A/B tests audited by ear by William Romero and verified via harmonic Constant-Q / STFT chromagrams in `noticias/tech-2026-11-08` (see `/Users/williamromero/MediaProjects/WBRS/manual_ingenieria_retencion_punto_dulce.md` §7).

---

## 1. The 4 Musical Selection Laws (Before Importing Any FlowMusic Track)

1. **Bright Diatonic Major Mode Only (`F# Major`, `G Major`, `A Major`, `E Major` · Harmonic Purity `>= 80%`):**
   - Under executive spoken Spanish, minor keys or modal chromatic passing tones (`> 20%` out-of-scale harmonic energy, as in rejected track *Impulso Ágil*) register subconsciously as tuning errors or anxiety.
   - Only select tracks whose harmonic spectrum concentrates `>= 80%` inside the 7 degrees `[0, 2, 4, 5, 7, 9, 11]` of a **Major** key with dominant major-third triad weight (`I - IV - V - vi`).

2. **Middle Melodic Register Only — Zero "Octavas Raras" (Bregman Stream Segregation Law):**
   - William's spoken voice occupies `115–175 Hz` (fundamental), `180–400 Hz` (chest warmth), and `1,600–3,400 Hz` (consonant intelligibility formants $F_2, F_3$).
   - **Prohibited:** Piercing lead synths/bells in **Octaves 6–7 (`1,600–3,600 Hz`)**, erratic sub-bass notes in **Octave 1 (`< 55 Hz`)**, or sudden melodic leaps `> 1 octave`. By Bregman's auditory stream segregation principle, octave jumps pull conscious attention away from the narrator (*"what was that weird note?"*) and mask speech consonants.
   - **Required:** Confine melodic instruments (clean pop guitar, warm plucks, soft marimba/keys) to **Octaves 3–4 (`185–780 Hz`)** moving in stepwise or compact intervals (`<= perfect 5th`).

3. **Steady 8th/16th Subdivision (`116–124 BPM`) — Zero Syncopated *Punch / Brass Hits*:**
   - Syncopated funk/brass stabs followed by micro-silences create `+7 to +9 dB` mid-band crest spikes that collide randomly with unstressed spoken syllables and make the video feel like it is braking.
   - Require a **continuous, smooth rhythmic carpet** (`16th`-note shaker/muted guitar/warm synth pulse around `120 BPM`).

4. **Zero Internal Bar-Skip Splices (`0 Splices` Rule):**
   - **Never** cut out bars in the middle of a music file and crossfade non-adjacent bars together—joining incompatible chord voicings creates an audible harmonic lurch. Always extract **one uninterrupted slice** starting cleanly on a `Beat 1` downbeat (`15 ms` micro-ramp in).

### Approved FlowMusic Generation Prompt Template
```text
Upbeat bright melodic indie-pop tech instrumental in F# Major, 120 BPM, steady continuous 16th-note warm muted guitar and clean synth pluck groove in middle register (octaves 3 and 4 only, 200-700 Hz), strictly diatonic major chord progression (I-V-vi-IV), smooth consistent dynamics, NO brass hits, NO orchestra stabs, NO high-pitched piccolo bells or octave jumps, NO minor or chromatic chords, NO vocals, clean modern commercial documentary bed.
```

---

## 2. The Golden Loudness Window (`-12.0 to -13.5 dB` Below Voice)

| Bed Level Relative to Voice | Audible Result | Verdict |
| :---: | :--- | :---: |
| `-8.5 dB` | Masks spoken consonants (`s, t, c`) and fatigues the listener. | **FAIL (Too Loud)** |
| **`-12.0 to -13.5 dB`** | **Crystal-clear speech + unmistakable melodic momentum on phone & laptop speakers.** | **GOLDEN WINDOW** |
| `-19.0 dB` or lower | Drops below `-33 LUFS` absolute; completely disappears on mobile speakers. | **FAIL (Inaudible)** |

### Mandatory Mixing & Mastering Chain
1. **Voice (`1.000x` strictly — `atempo` prohibited by `AGENTS.md §A.5`):**
   `highpass=f=80, acompressor=threshold=-24dB:ratio=3.0:attack=4:release=140:makeup=2.2, alimiter=limit=0.76`
2. **Music Bed Spectral Pocket & Valley Compensation:**
   - Carve a subtle vocal-formant pocket on the music stem ONLY: `equalizer=f=1900:t=q:w=1.1:g=-2.2`.
   - Apply gentle `+2.5 to +3.5 dB` envelope compensation if an arrangement thins out mid-track, and lift `+6.0 to +6.5 dB` smoothly on the `1.5 s` end-card tail.
3. **Two-Pass Linear Broadcast Master (`48 kHz` Stereo):**
   `loudnorm=I=-14:TP=-1.5:LRA=9:linear=true` → Target **`-14.0 ± 0.8 LUFS`**, True Peak **`<= -1.2 dBTP`**.

---

## 3. Diatonically Tuned SFX (`<= 1 Cue per 5.0 s`, Max `8–10` Total)

Never fire fixed C-Major chimes over an F#-Major or A-Major song. Every pitched cue must be synthesized from the detected tonic frequency $f_R$ of the chosen music track via $f(n) = f_R \cdot 2^{n/12}$:

- **`click` (`24 ms`, Causal Cursor click):** Athermal percussive sweep $1480 e^{-160t} + 220\text{ Hz}$ (`0` harmonic clash in any key).
- **`whoosh_s` (`200 ms`, max `1` entering end-sheet):** Bandpass-filtered noise with $\sin^{1.8}(\pi t / 0.20)$ envelope.
- **`chime` (`340 ms`, meter `94–100%` completion):** Pure Octave + Fifth (`f(12) + f(19)`).
- **`sub_soft` (`260 ms`, mid-video Re-hook pattern interrupt):** Tonic Octave-1 drop (`2 * f(-24) -> f(-24)`).
- **`bloom` (`750 ms`, closing brand emblem):** Full Major Triad (`f(0) + f(4) + f(7) + f(12)`).

---

## 4. Automated Pre-Mix & Post-Mix Auditor (`wvf audit-music`)

Always run `wvf audit-music` on candidate FlowMusic tracks **before** mixing, and again with `--voice` and `--master` **after** mixing:

```bash
# 1. Audit a candidate track before mixing (outputs key, CQT purity, octave balance, punch hits, and exact SFX Hz):
wvf audit-music audio/candidate_flowmusic.m4a --target-dur 45

# 2. Verify full mix delta (-12.0 to -13.5 dB) and master loudness (-14 LUFS) and write check/music_audit.json:
wvf audit-music audio/music_only.wav --voice audio/voice.wav --master audio/master.wav
```
