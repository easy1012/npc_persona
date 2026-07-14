# NPC Persona v2 Static Deck Design System

## 1. Atmosphere & Identity

The deck feels like a quiet technical command briefing: dense, precise, Korean-first, and readable from a laptop or projector without needing any network. The signature is a dark editorial canvas with thin graphite panels and compact diagrams, so the audience reads the v2 runtime contract as an evidence map instead of a marketing page.

## 2. Color

### Palette

| Role | Token | Value | Usage |
|---|---|---:|---|
| Canvas | `--color-canvas` | `#08090a` | Page background |
| Panel | `--color-panel` | `#0f1115` | Slide surface |
| Panel raised | `--color-panel-raised` | `#151821` | Diagram and note surfaces |
| Text primary | `--color-text` | `#f4f6fb` | Headings and strong body |
| Text secondary | `--color-muted` | `#c7cede` | Explanatory body |
| Text tertiary | `--color-dim` | `#9aa3b8` | Meta labels |
| Border | `--color-border` | `#242833` | Card and deck boundaries |
| Border subtle | `--color-border-subtle` | `#1a1e27` | Internal dividers |
| Accent | `--color-accent` | `#7c83ff` | Active state and source links |
| Accent soft | `--color-accent-soft` | `#323977` | Diagram highlights |
| Success | `--color-success` | `#35c989` | QA pass and safe gates |
| Warning | `--color-warning` | `#f2b84b` | Approval-required gates |

### Rules

- The deck is dark-mode native; light surfaces are not introduced.
- Accent is reserved for active navigation, source links, and diagram focus nodes.
- Any new color must be added here before use in `styles.css`.

## 3. Typography

### Scale

| Level | Token | Size | Weight | Line Height | Usage |
|---|---|---:|---:|---:|---|
| Display | `--font-display` | `clamp(2rem, 5vw, 4.5rem)` | 700 | 1.05 | Deck title and slide title |
| Heading | `--font-heading` | `clamp(1.35rem, 2.6vw, 2rem)` | 650 | 1.2 | Card headings |
| Body | `--font-body` | `clamp(1rem, 1.5vw, 1.125rem)` | 400 | 1.72 | Korean explanatory copy |
| Small | `--font-small` | `0.875rem` | 500 | 1.55 | Source links and labels |
| Caption | `--font-caption` | `0.75rem` | 650 | 1.4 | Counters and badges |
| Mono | `--font-mono-size` | `0.8125rem` | 500 | 1.55 | IDs and paths |

### Font Stack

- Primary: `Apple SD Gothic Neo`, `Malgun Gothic`, `Segoe UI`, `system-ui`, `sans-serif`.
- Mono: `SFMono-Regular`, `Consolas`, `Liberation Mono`, `monospace`.

### Rules

- Use local system font stacks only.
- Korean headings use `word-break: keep-all` and `overflow-wrap: anywhere` to avoid clipped or awkward syllable wrapping.
- Body copy never drops below 16px on mobile.

## 4. Spacing & Layout

### Base Unit

All spacing derives from a 4px base.

| Token | Value | Usage |
|---|---:|---|
| `--space-1` | `4px` | Tight inline gaps |
| `--space-2` | `8px` | Badge and chip rhythm |
| `--space-3` | `12px` | Compact card padding |
| `--space-4` | `16px` | Default internal spacing |
| `--space-6` | `24px` | Slide card padding |
| `--space-8` | `32px` | Desktop grid gaps |
| `--space-10` | `40px` | Slide outer padding |
| `--space-12` | `48px` | Large viewport breathing room |

### Grid

- Max deck width: `1280px`.
- Desktop slide layout: two-column evidence grid with a larger explanatory panel and a diagram panel.
- Mobile slide layout: one column, sticky topbar, all content constrained to viewport width.
- Breakpoints: `820px` and `520px`.

### Rules

- No horizontal overflow; all long file paths wrap with `overflow-wrap: anywhere`.
- Slide content uses the same panel rhythm and gap tokens across all 12 slides.

## 5. Components

### Topbar

- **Structure**: deck title, slide counter, previous/next buttons.
- **Spacing**: `--space-3`, `--space-4`, and `--space-6`.
- **States**: hover, active, disabled, and focus-visible.
- **Accessibility**: real buttons with `aria-label`; counter updates from script.

### Source Slide

- **Structure**: label rail, title, `explain` prose, source link, diagram card, fact grid.
- **Spacing**: `--space-6` on mobile, `--space-8` on desktop.
- **Accessibility**: inactive slides receive `aria-hidden="true"`; active slide receives `aria-hidden="false"`.
- **Motion**: opacity and transform only.

### Diagram Card

- **Structure**: inline SVG with `class="diagram"`, local text labels, and token-colored shapes.
- **Variants**: flow, gate, state, compare, evidence.
- **Accessibility**: each SVG has a `<title>` and readable adjacent explanation.

### Source Link

- **Structure**: local relative anchor back to the source Markdown file.
- **States**: accent hover, focus ring, and wrapped file path.
- **Accessibility**: link text names the exact source document.

## 6. Motion & Interaction

### Timing

| Type | Duration | Easing | Usage |
|---|---:|---|---|
| Micro | `140ms` | `ease-out` | Button press and link hover |
| Standard | `240ms` | `ease-in-out` | Slide activation |
| Emphasis | `480ms` | `cubic-bezier(0.16, 1, 0.3, 1)` | First slide reveal |

### Rules

- Animate only `opacity` and `transform`.
- Keyboard navigation supports ArrowRight and ArrowLeft.
- Hash navigation is stable and updates the active slide.
- Reduced motion disables transitions and animations.

## 7. Depth & Surface

### Strategy

Use mixed dark tonal shift plus thin borders. Shadows stay subtle and only reinforce the active deck surface.

| Level | Token | Value | Usage |
|---|---|---|---|
| Border default | `--surface-border` | `1px solid var(--color-border)` | Slide and diagram panels |
| Border subtle | `--surface-border-subtle` | `1px solid var(--color-border-subtle)` | Internal fact cards |
| Shadow active | `--shadow-active` | `0 24px 80px rgba(0, 0, 0, 0.36)` | Active deck frame |

The deck must never fake UI with a raster image. Diagrams are local inline SVG, text is real DOM, and links resolve to local Markdown sources.
