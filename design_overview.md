Create a complete design system for a data analytics SaaS platform with the following specifications:
Product Overview
A modern SaaS application for data analysis that allows users to upload Looker Studio boards, clean XLSX files, and interact with their data through AI chat. The platform should feel professional, trustworthy, and data-focused while remaining approachable and easy to use.
Design Philosophy

Data-first aesthetic: Clean, spacious layouts that prioritize readability and data visualization
Progressive disclosure: Complex features revealed gradually to avoid overwhelming users
Calm technology: Subtle animations and feedback that inform without distracting
Trust and reliability: Professional appearance that conveys security and accuracy

Color System
Primary Palette
Define a primary brand color that conveys:

Intelligence and innovation (consider deep blues, purples, or teals)
Professional credibility
Include 9 shades from 50 (lightest) to 900 (darkest)

Secondary Palette

An accent color for CTAs and important actions (consider vibrant but not overwhelming)
Success green (for completed uploads/cleaning)
Warning amber (for processing states)
Error red (for failures/alerts)
Neutral grays (9 shades for backgrounds, borders, text hierarchy)

Semantic Colors

bg-primary: Main background
bg-secondary: Card/panel backgrounds
bg-tertiary: Nested sections
text-primary: Main content (high contrast)
text-secondary: Supporting text
text-tertiary: Subtle/metadata text
border-default: Standard dividers
border-subtle: Light separators

Typography
Font Families

Headings: A geometric sans-serif that feels modern and technical
Body: A humanist sans-serif optimized for readability at small sizes
Monospace: For data values, code, and technical details

Type Scale
Define sizes for:

Display (hero sections): 48px+
H1: ~36px
H2: ~30px
H3: ~24px
H4: ~20px
Body Large: ~18px
Body: ~16px
Body Small: ~14px
Caption: ~12px

Font Weights

Regular (400): Body text
Medium (500): Emphasis, labels
Semibold (600): Subheadings, buttons
Bold (700): Headlines, strong emphasis

Spacing System
Use a 4px base unit with a multiplier scale:

0.5: 2px (tight spacing)
1: 4px
2: 8px
3: 12px
4: 16px (base)
6: 24px
8: 32px
12: 48px
16: 64px
24: 96px (large section spacing)

Component Specifications
Navigation

Sidebar: Collapsible left navigation with icons + labels

Width: 240px expanded, 64px collapsed
Active state styling
Section groupings for Dashboard, AI Chat, Upload, History, Settings



Cards

Background: Slightly elevated from page background
Border radius: 8-12px (modern but not overly rounded)
Shadow: Subtle elevation (2-3 shadow levels for depth)
Padding: 24px (content cards), 16px (compact cards)

Buttons
Primary: Solid background, high contrast text, used for main actions
Secondary: Outlined, used for alternative actions
Ghost: Text-only, used for tertiary actions
Sizes: Small (32px), Medium (40px), Large (48px)
States: Default, Hover, Active, Disabled, Loading
Progress Indicators

Linear progress bars for file cleaning (with percentage)
Circular loaders for indeterminate states
Step indicators for multi-stage processes
Status badges (Processing, Complete, Failed)

Data Display

Tables: Alternating row colors, hover states, sortable headers
Charts: Color palette that works for 8+ data series
Metrics Cards: Large number display with context and trend indicators
Upload Zones: Dashed borders, clear iconography, drag-and-drop feedback

Chat Interface

Message bubbles: User (right-aligned, primary color), AI (left-aligned, neutral)
Typing indicators
Code block styling with syntax highlighting
Table/chart rendering within chat

Layout Patterns
Dashboard Page

Grid system: 12-column for responsive layouts
Card-based layout with metrics at top
Visualization area in center/bottom
Recent activity sidebar (optional)

Upload Section

Dropzone: Prominent, centered when empty
File list: Table view with progress bars per file
Bulk actions toolbar
Filter/sort controls

History Section

Timeline or table view toggle
Date range filters
Search functionality
Expandable details per entry

Settings/Profile

Two-column layout (navigation + content)
Form styling with clear labels and help text
Save indicators

Interaction Patterns
Animations

Duration: 150ms (micro), 300ms (standard), 500ms (large movements)
Easing: ease-in-out for most, ease-out for entrances
Page transitions: Subtle fade or slide
Loading states: Skeleton screens for content, spinners for actions

Feedback

Toast notifications: Top-right corner, auto-dismiss
Inline validation: Real-time for forms
Confirmations: Modal dialogs for destructive actions
Empty states: Helpful illustrations and CTAs

Accessibility Requirements

WCAG 2.1 AA compliance minimum
Color contrast ratios: 4.5:1 for body text, 3:1 for large text
Focus indicators: Visible keyboard navigation
ARIA labels for interactive elements
Screen reader friendly

Responsive Breakpoints

Mobile: 320px - 639px
Tablet: 640px - 1023px
Desktop: 1024px - 1439px
Large Desktop: 1440px+

Dark Mode (Optional)
If included, specify inverted color values maintaining contrast ratios, with dimmed data visualizations.

OUTPUT FORMAT:
Provide the complete design system as:

A comprehensive style guide with hex/RGB values
Component specifications with exact measurements
Usage examples for each pattern
Code-ready CSS custom properties or design tokens