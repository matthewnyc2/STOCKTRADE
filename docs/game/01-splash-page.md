# 01 - SPLASH PAGE SPECIFICATION

## Overview

The splash page is the FIRST thing users see. It sets the tone for the entire experience. This is not a loading screen - it's a **statement of intent**.

---

## THE VISION

### The Scene: Scrooge McDuck's Money Bin

Imagine the iconic image of Scrooge McDuck diving into his money bin, but instead of Scrooge, it's a **giant stylized "M"** (for Money, for Market, for Mastery).

The M should feel:
- **Metallic** - Like a gold coin or trophy
- **Dimensional** - 3D with depth and shadow
- **Animated** - Subtle movement, gleaming highlights
- **Powerful** - This is the symbol of wealth mastery

### The Money Bin

Behind/around the M:
- Piles of gold coins (stylized, not realistic)
- Green dollar bills floating/falling
- Maybe some stock chart lines weaving through like ribbons
- A subtle vault door frame suggesting "you're entering the vault"

---

## ANIMATION SEQUENCE

```
Time 0.0s - 1.0s:  Black screen, anticipation
Time 1.0s - 1.5s:  Vault door SLAMS into view from above
Time 1.5s - 2.5s:  Door swings open with satisfying mechanical sound
Time 2.5s - 3.5s:  Camera pushes INTO the vault
Time 3.5s - 4.5s:  The M RISES from the pile of coins
                   Coins scatter and fall around it
                   Light gleams across the metallic surface
Time 4.5s - 5.5s:  M settles into final position, coins settling
Time 5.5s - 6.5s:  Tagline fades in below: "MASTER THE MARKET"
Time 6.5s - 7.5s:  Subtle pulse on the M, waiting for interaction
Time 7.5s+:        User can click/tap anywhere to proceed
                   OR auto-advance after 8 seconds
```

---

## TECHNICAL SPECIFICATIONS

### Option A: Video File (Recommended for V1)
- Pre-rendered MP4/WebM, 1920x1080
- 8 seconds duration
- Loop last 2 seconds for idle state
- File size target: < 5MB
- Fallback: Static image for slow connections

### Option B: Real-time Animation (V2)
- Three.js or similar for 3D M
- Particle system for coins
- More interactive but higher dev cost
- Could allow user to "dive in" with gesture

### Option C: Lottie Animation (Middle Ground)
- After Effects → Lottie export
- Vector-based, scales perfectly
- Interactive triggers possible
- Good balance of quality and file size

---

## THE M DESIGN

### Style References
- Art Deco gold lettering
- Casino/Vegas signage
- Trophy/medal aesthetic
- NOT: Crypto bro / meme coin vibes

### The M Should Convey
- Wealth (gold, metallic)
- Mastery (sharp, precise)
- Game (playful gleam)
- Trust (solid, heavy)

### Possible M Variations
1. **Solid Gold M** - Classic, simple
2. **M Made of Stacked Coins** - Clever, on-theme
3. **M as a Chart** - The legs are candlesticks going up
4. **M with Crown** - "Master" / royalty theme

---

## SOUND DESIGN

### Audio Sequence
```
0.0s: Silence (builds anticipation)
1.0s: VAULT SLAM - Heavy metal impact
1.5s: DOOR CREAK - Old vault opening
2.5s: WHOOSH - Camera movement
3.5s: COIN CASCADE - Coins falling/scattering
4.0s: GLEAM - High sparkle sound as M catches light
5.5s: Subtle ambient hum (wealth/power feeling)
```

### Audio Requirements
- All sounds should feel PREMIUM
- Reference: Casino games, heist movies
- Mute option must be available
- Remember the sound on first visit

---

## RESPONSIVE BEHAVIOR

### Desktop (1920x1080+)
- Full animation as described
- M centered with generous negative space
- Coins extend to edges

### Tablet (768px - 1024px)
- Same animation, scaled down
- Reduce particle count for performance

### Mobile (< 768px)
- Simplified animation
- M takes 60% of screen height
- Fewer coins, faster sequence (5s total)
- Consider portrait-optimized version

---

## INTERACTION STATES

### First Visit
- Full animation plays
- "Tap anywhere to enter" prompt after animation
- Store flag that user has seen intro

### Return Visit
- Option 1: Skip directly to dashboard
- Option 2: Quick version (2s)
- Option 3: User preference in settings

### Skip Button
- Small "Skip" in bottom right after 2s
- Respects user's time
- Logs that user skipped (analytics)

---

## TRANSITION TO HERO DASHBOARD

After splash, transition to hero dashboard should feel seamless:

```
User taps "Enter" or screen
     │
     ▼
M begins to shrink/recede
     │
     ▼
Camera "flies through" the M
     │
     ▼
Dashboard elements fade in from behind
     │
     ▼
Full dashboard revealed
```

The M could become the logo in the header - visual continuity.

---

## IMPLEMENTATION PROMPT FOR DEVELOPERS

```
BUILD THE STOCKTRADE SPLASH PAGE

Context:
- This is a gamified stock trading education app
- The splash sets the tone: wealthy, playful, masterful
- Think "entering Scrooge McDuck's vault"

Requirements:
1. Create a splash screen component at /app/splash or similar
2. Feature a large, metallic, animated "M" logo
3. Surround with gold coins and money imagery
4. Include vault door opening animation
5. Play for ~7 seconds, then allow proceed
6. Transition smoothly to hero dashboard
7. Remember if user has seen it (localStorage)
8. Include skip button after 2 seconds
9. Handle mobile/tablet responsively
10. Optional: Add sound effects (with mute)

Tech suggestions:
- Lottie for main animation
- Framer Motion for transitions
- CSS for shimmer/gleam effects

Deliverables:
- SplashPage component
- Animation assets (or specifications for designer)
- Transition logic to dashboard
- Skip/return visit handling

Reference:
- See 02-hero-dashboard.md for where this leads
- See 00-overview.md for full system context
```

---

## ACCEPTANCE CRITERIA

- [ ] Splash loads in < 2 seconds on 4G connection
- [ ] Animation plays smoothly at 60fps on mid-range devices
- [ ] M logo is visually striking and memorable
- [ ] Money bin aesthetic is clear but not childish
- [ ] Skip button works and remembers preference
- [ ] Transition to dashboard is seamless
- [ ] Sound can be muted and preference persists
- [ ] Mobile version is appropriately simplified
- [ ] Return visitors can bypass or see quick version

---

*Related Documents:*
- `00-overview.md` - System context
- `02-hero-dashboard.md` - What comes after splash
