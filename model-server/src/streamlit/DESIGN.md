# Streamlit Design Contract - Village Correspondence Journal

This contract governs the production `마을 통신 수첩` player surface in `player_app.py`. It does not apply to the debug-oriented `test_app.py` or the separate admin page.

## 0. Research Log

- Approved plan: `docs/plans/2026-07-11-npc-game-service-design.md` selected a village correspondence journal with left NPC roster, center durable dialogue, and right quest journal.
- Existing UI audit: `src/streamlit/test_app.py` is a functional GraphRAG/debug runtime with sidebar diagnostics, Streamlit chat messages, and no visual design system. `src/streamlit/pages/admin.py` is admin-only and remains visually separate.
- Game UI guidance: use progressive disclosure, safe zones, controller/keyboard-visible focus, redundant state encodings, readable text panels, and motion only for selection/loading/state changes.

## 1. Design Intent

- Product metaphor: a warm field notebook carried through Hazel Village, with stitched paper panels, inked route marks, sealed letters, and pinned quest slips.
- Player layout: NPC correspondence roster on the left, active conversation ledger in the center, quest journal on the right.
- Signature memory: every state should feel like a physical village note being selected, unfolded, stamped, or marked on a route, while technical IDs, prompts, retrieved chunks, model hosts, and diagnostics stay off the player surface.
- Implementation scope: production player composition, responsive presentation, and narrowly scoped Components v2 controls. No changes to `test_app.py`, `pages/admin.py`, retrieval, prompts, backend contracts, Docker topology, or data flows.

## 2. Tokens

All repeated UI values must trace to the CSS custom properties below. New visual values are added here before use.

### Color

| Token | Value | Use |
| --- | --- | --- |
| `--journal-ink` | `#2f261d` | Primary text and SVG strokes |
| `--journal-muted` | `#6e5c49` | Secondary text |
| `--journal-paper` | `#f4e7c8` | Main paper surface |
| `--journal-paper-strong` | `#fff4d6` | Raised paper cards |
| `--journal-parchment` | `#dbc290` | Borders and disabled paper |
| `--journal-wood` | `#65492f` | Dark structural rails |
| `--journal-moss` | `#436b4b` | Solved/safe/active route state |
| `--journal-river` | `#2f6f7c` | Player voice and info state |
| `--journal-berry` | `#8e3f3a` | Error/urgent state |
| `--journal-honey` | `#c9852d` | Current objective, focus, loading |
| `--journal-shadow` | `rgba(47, 38, 29, 0.22)` | Paper depth |
| `--journal-vein` | `rgba(101, 73, 47, 0.12)` | Notebook grain and ruled lines |

### State Tokens

- Active NPC: `--state-active-bg: var(--journal-paper-strong)`, `--state-active-mark: var(--journal-moss)`.
- Unread NPC: `--state-unread-mark: var(--journal-honey)` plus text label, never color only.
- Route recommendation: `--state-route-mark: var(--journal-berry)` plus route SVG and `추천 이동` label.
- Loading: `--state-loading-mark: var(--journal-honey)` plus inline text and reduced-motion-safe shimmer.
- Error: `--state-error-bg: #f1d5c9`, `--state-error-mark: var(--journal-berry)` plus explicit title.
- Empty: `--state-empty-bg: #efe0bb`, with dashed border and instructional copy.

### Radius, Shadow, Z-index

- `--radius-sm: 0.5rem`, `--radius-md: 0.85rem`, `--radius-lg: 1.35rem`, `--radius-ticket: 1.8rem 0.9rem 1.5rem 0.75rem`.
- `--shadow-paper: 0 1rem 2.5rem var(--journal-shadow)`, `--shadow-pressed: inset 0 0.18rem 0.45rem rgba(47, 38, 29, 0.16)`.
- Z-index scale: base `0`, floating marker `10`, sticky input `20`, modal/expanded journal `40`, debug/admin surfaces unchanged.

## 3. Typography

- Font stack is local/system only: `"Iowan Old Style", "Palatino Linotype", "Book Antiqua", "Georgia", "Apple SD Gothic Neo", "Malgun Gothic", serif`.
- Display labels use letter-spaced small caps in the same stack, not an external display font.
- Body Korean uses the same mixed serif/Korean stack with `word-break: keep-all`, `overflow-wrap: anywhere`, and line-height `1.65` to avoid orphaned particles or final-syllable wraps.
- Scale: hero title `clamp(1.55rem, 2vw + 1rem, 2.75rem)`, section title `1.25rem`, body `1rem`, secondary `0.92rem`, badge `0.82rem`. Nothing player-facing drops below `0.875rem`.
- Text on textured or dark surfaces uses panel backing and subtle shadow; no thin low-contrast text on background grain.

## 4. Spacing

Use an 8px-derived scale through tokens only:

| Token | Value | Use |
| --- | --- | --- |
| `--space-1` | `0.25rem` | Hairline gaps |
| `--space-2` | `0.5rem` | Badge interiors |
| `--space-3` | `0.75rem` | Compact card padding |
| `--space-4` | `1rem` | Default component gap |
| `--space-5` | `1.5rem` | Panel padding |
| `--space-6` | `2rem` | Column gutters |
| `--space-safe` | `clamp(1rem, 3vw, 3rem)` | Safe-zone page margin |

## 5. Surface Materials

- Page: warm parchment with grain made from CSS gradients only.
- Panels: layered paper cards with stitched/dashed borders and asymmetric ticket radius.
- Dialogue: NPC messages are folded paper slips, player messages are river-ink notes, system states are pinned labels.
- Quest journal: ruled paper with clue rows, hint tier stamp, and objective ribbon.
- SVG marks are inline local assets using `currentColor`; no emoji icons and no external image or CDN dependency.

## 6. Primitives

- `JournalShell`: three-region grid that maps to roster, dialogue, and quest journal on desktop.
- `StatusBar`: compact active-NPC and current-objective context above the journal grid.
- `NpcRosterItem`: focusable row with portrait seal, name, role, quest state, unread label, active treatment, and optional route marker.
- `NpcNavigator`: Components v2 control for keyboard and touch NPC selection; emits only the selected NPC ID to Streamlit.
- `ConversationBubble`: speaker-specific message card with timestamp/relationship metadata and Korean-safe wrapping.
- `QuestJournal`: objective card, clue list, hint tier stamp, and solved/progress indicators with redundant labels.
- `QuestDisclosure`: native details/summary disclosure used only on narrow layouts; quest state remains owned by Streamlit.
- `InlineComposer`: `st.chat_input` rendered inside the dialogue column, never detached at page level.
- `RouteMarker`: inline SVG path marker plus route copy, never color-only.
- `StateCard`: empty, loading, and error surfaces sharing the same panel anatomy.
- `InputPromptLegend`: keyboard/controller action labels as semantic action names, not hardcoded one-controller button copy.
- `FocusRing`: high-contrast honey outline plus offset shadow for keyboard/controller focus.

## 7. Interaction States

- Hover: changes border tone and paper depth without layout shift.
- Focus: visible 3px honey outline with dark offset shadow on every interactive primitive.
- Active: moss route seal, raised card, and `현재 대화` label.
- Unread: honey knot mark and unread count label.
- Route recommended: berry route marker plus destination text.
- Loading: progress text and subdued shimmer; no blocking spinner-only state.
- Error: explicit recovery copy, berry triangle SVG, and retry affordance in later product UI.

## 8. Motion Constraints

- Motion communicates selection, loading, or state change only.
- Allowed properties: opacity, transform, and filter. No layout property animation.
- Default durations: `180ms` for hover/focus, `240ms` for state card reveal, `320ms` maximum for loading shimmer.
- `@media (prefers-reduced-motion: reduce)` disables animation and transition effects while preserving state clarity.
- No bounce, screen shake, rotation, parallax, or decorative infinite motion.

## 9. Responsive behavior

- `1280px+`: compact status bar followed by a `17rem / minmax(0, 1fr) / 20rem` grid for roster, dialogue, and quest journal.
- `768px-1279px`: status bar and horizontal NPC switcher span the top; dialogue remains primary and quest journal follows without horizontal overflow.
- `375px-767px`: horizontal NPC switcher, active NPC/current objective, dialogue, collapsed quest disclosure, then inline composer. All touch targets are at least 44px tall.
- Safe-zone margins never collapse to zero. Static player UI stays within the title-safe interior.
- Long Korean and mixed English/Korean strings must be reviewed at 375, 768, and 1280 widths.

## 10. Accessibility

- Contrast target: 4.5:1 minimum for body text, stronger for small labels.
- State is never color-only; combine color with icon shape, label, border style, or count.
- All interactive primitives are keyboard focusable with visible focus and at least 44px target height.
- Motion honors reduced-motion preferences.
- HTML/SVG copy must include accessible labels or visible text equivalents.
- Player, model, NPC, and quest copy is escaped before entering any HTML fragment. No untrusted value is passed to `st.html` or `unsafe_allow_html=True` without escaping.
- Korean typography uses `word-break: keep-all` and `line-break: strict` where supported.

## 11. Technical Separation

- Streamlit owns API calls, bootstrap/session state, active NPC state, message submission, reruns, and error recovery.
- Python render helpers own escaped semantic HTML for status, conversation, empty/error states, and quest presentation.
- Components v2 owns only keyboard/touch NPC selection and compact quest disclosure events. It receives presentation data, emits trigger values, and never calls the game API or stores authoritative game state.
- `st.chat_input` remains a native Streamlit widget and is mounted inside the dialogue column.
- `test_app.py` remains the debug/runtime surface; `pages/admin.py` remains admin-only and neither inherits player journal styling.
- Shared CSS and SVG assets remain local under `src/streamlit`; no external CDN, font, script, or image dependency is introduced.
- Internal NPC and quest IDs stay in API/state boundaries. Player-visible copy uses Korean presentation labels.

## 12. QA Contract

- Static contracts cover friendly quest labels, inline composer placement, Components v2 registration, responsive order, escaping, and no internal IDs in rendered player markup.
- Browser QA covers 375, 768, and 1280 widths, keyboard focus, NPC switching, message submission, active/empty/error states, Korean wrapping, reduced motion, and zero horizontal overflow.
- Production verification rebuilds the Streamlit container and exercises the player through the proxy without destructive database operations.
- The full model-server unit suites and the two-server service contract remain green.

## 13. Accepted debt

- `test_app.py` remains intentionally debug-oriented and separate from the production player surface.
- Controller navigation is represented through keyboard/focus semantics; native gamepad mapping is outside the Streamlit player scope.
- Quest disclosure preference is viewport-local and is not persisted as game state.
- Font availability depends on local/system fonts; no bundled font files are added.
