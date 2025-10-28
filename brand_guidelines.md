# TaskifAI Brand Guidelines

**Version 1.0** | Analytics Platform Design System

---

## Table of Contents

1. [Brand Identity](#brand-identity)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Spacing & Layout](#spacing--layout)
5. [Component Patterns](#component-patterns)
6. [Animation & Motion](#animation--motion)
7. [Design Principles](#design-principles)
8. [Usage Guidelines](#usage-guidelines)

---

## Brand Identity

### Platform Name
**TaskifAI Analytics Platform**

### Brand Positioning
Professional AI-powered sales analytics platform that transforms vendor data into actionable business intelligence. The brand conveys:
- **Intelligence**: AI-driven insights and analytics
- **Precision**: Data accuracy and detailed reporting
- **Professionalism**: Enterprise-grade SaaS platform
- **Accessibility**: Clean, intuitive interface design

### Brand Voice
- Professional yet approachable
- Data-focused and analytical
- Clear and concise communication
- Empowering and insightful

---

## Color System

### Primary Colors

#### Primary - Indigo
**Main Brand Color** | Auth0-inspired professional identity

```css
--primary: hsl(239, 84%, 67%)  /* #6366F1 */
```

**Scale:**
- 50: `hsl(239, 100%, 99%)` - Lightest tint
- 100: `hsl(239, 100%, 97%)`
- 200: `hsl(239, 96%, 93%)`
- 300: `hsl(239, 94%, 87%)`
- 400: `hsl(239, 87%, 77%)`
- 500: `hsl(239, 84%, 67%)` - **Base**
- 600: `hsl(239, 76%, 59%)`
- 700: `hsl(239, 72%, 52%)`
- 800: `hsl(239, 67%, 44%)`
- 900: `hsl(239, 61%, 38%)` - Darkest shade

**Usage:**
- Primary buttons and CTAs
- Active navigation states
- Focus rings and interactive states
- Brand elements and highlights
- Links and interactive text

#### Accent - Teal/Cyan
**Data Emphasis Color**

```css
--accent: hsl(173, 80%, 40%)  /* #14B8A6 */
```

**Scale:**
- 50: `hsl(173, 80%, 97%)`
- 100: `hsl(173, 80%, 93%)`
- 200: `hsl(173, 78%, 84%)`
- 300: `hsl(173, 76%, 72%)`
- 400: `hsl(173, 78%, 56%)`
- 500: `hsl(173, 80%, 40%)` - **Base**
- 600: `hsl(173, 83%, 32%)`
- 700: `hsl(173, 85%, 26%)`
- 800: `hsl(173, 87%, 21%)`
- 900: `hsl(173, 90%, 17%)`

**Usage:**
- Data visualizations (primary chart color)
- Metrics and KPI highlights
- Active sidebar navigation
- Badges and status indicators
- Gradient accents with primary

### Neutral Colors

#### Background & Surfaces
```css
--background: hsl(0, 0%, 98%)        /* Light gray background */
--foreground: hsl(222.2, 84%, 4.9%)  /* Near-black text */
--card: hsl(0, 0%, 100%)             /* White cards */
--popover: hsl(0, 0%, 100%)          /* White popovers */
```

#### Secondary & Muted
```css
--secondary: hsl(220, 14.3%, 95.9%)       /* Light gray */
--muted: hsl(220, 14.3%, 95.9%)           /* Subtle backgrounds */
--muted-foreground: hsl(220, 8.9%, 46.1%) /* Muted text */
```

#### Borders & Inputs
```css
--border: hsl(220, 13%, 91%)  /* Light gray borders */
--input: hsl(220, 13%, 91%)   /* Input borders */
--ring: hsl(239, 84%, 67%)    /* Focus ring (primary) */
```

### Semantic Colors

#### Success
```css
--success: hsl(142, 71%, 45%)  /* Green #22C55E */
```
**Usage:** Success states, positive trends, completed actions

#### Warning
```css
--warning: hsl(38, 92%, 50%)  /* Amber #F59E0B */
```
**Usage:** Warning states, caution indicators, pending actions

#### Destructive/Error
```css
--destructive: hsl(0, 72%, 51%)  /* Red #EF4444 */
```
**Usage:** Error states, delete actions, critical alerts, admin sections

### Sidebar Colors

#### Dark Charcoal Theme
```css
--sidebar-background: hsl(217, 33%, 17%)   /* #1F2937 */
--sidebar-foreground: hsl(220, 13%, 91%)   /* Light text */
--sidebar-border: hsl(217, 32.6%, 22%)     /* Border */
--sidebar-hover: hsl(239, 84%, 67%)        /* Primary on hover */
--sidebar-active: hsl(173, 80%, 40%)       /* Accent when active */
```

### Chart Palette

**8-Color Data Series** (optimized for teal-focused visualizations)

1. `--chart-1: hsl(173, 80%, 40%)` - Teal (primary)
2. `--chart-2: hsl(239, 84%, 67%)` - Indigo
3. `--chart-3: hsl(142, 71%, 45%)` - Green
4. `--chart-4: hsl(38, 92%, 50%)` - Amber
5. `--chart-5: hsl(262, 83%, 58%)` - Purple
6. `--chart-6: hsl(346, 77%, 50%)` - Rose
7. `--chart-7: hsl(47, 96%, 53%)` - Yellow
8. `--chart-8: hsl(199, 89%, 48%)` - Sky Blue

**Usage Rules:**
- Use chart-1 (teal) for primary data series
- Use chart-2 (indigo) for secondary data
- Reserve chart-3 (green) for positive metrics
- Reserve chart-4 (amber) for warning metrics

---

## Typography

### Font Families

#### Sans Serif - Primary
```css
--font-sans: 'Inter', system-ui, -apple-system, sans-serif
```
**Usage:** Body text, UI elements, general interface

#### Heading Font
```css
--font-heading: 'DM Sans', 'Inter', system-ui, sans-serif
```
**Usage:** Page titles, section headings, card titles

#### Monospace
```css
--font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace
```
**Usage:** Code snippets, data tables, numeric values

### Type Scale

**Global UI Scale:** 90% (compact interface optimized for data density)

#### Headings

**H1 - Page Titles**
```css
font-size: 2.25rem (36px)
font-weight: 700 (Bold)
line-height: 1.2
letter-spacing: -0.025em (Tight)
font-family: var(--font-heading)
```

**H2 - Section Titles**
```css
font-size: 1.875rem (30px)
font-weight: 600 (Semibold)
line-height: 1.3
letter-spacing: -0.025em (Tight)
font-family: var(--font-heading)
```

**H3 - Card Titles**
```css
font-size: 1.5rem (24px)
font-weight: 600 (Semibold)
line-height: 1.4
letter-spacing: -0.025em (Tight)
font-family: var(--font-heading)
```

**H4 - Subsection Titles**
```css
font-size: 1.25rem (20px)
font-weight: 600 (Semibold)
line-height: 1.4
letter-spacing: -0.025em (Tight)
font-family: var(--font-heading)
```

**H5 - Small Headings**
```css
font-size: 1.125rem (18px)
font-weight: 500 (Medium)
line-height: 1.5
```

**H6 - Micro Headings**
```css
font-size: 1rem (16px)
font-weight: 500 (Medium)
line-height: 1.5
```

#### Body Text

**Default Body**
```css
font-size: 0.9rem (14.4px at 90% scale)
line-height: 1.6
font-weight: 400 (Regular)
```

**Small Text**
```css
font-size: 0.875rem (14px)
line-height: 1.5
```

**Extra Small**
```css
font-size: 0.75rem (12px)
line-height: 1.4
```

#### Data Display

**Metric Values** (Large numbers, KPIs)
```css
font-size: 1.875rem (30px)
font-weight: 700 (Bold)
font-variant-numeric: tabular-nums
letter-spacing: -0.025em
```

**Metric Labels**
```css
font-size: 0.875rem (14px)
font-weight: 500 (Medium)
text-transform: uppercase
letter-spacing: 0.05em (Wide)
color: var(--muted-foreground)
```

### Typography Features

**Font Feature Settings:**
```css
font-feature-settings: 'rlig' 1, 'calt' 1;
-webkit-font-smoothing: antialiased;
-moz-osx-font-smoothing: grayscale;
```

**Tabular Numbers** (for data tables and metrics):
```css
font-variant-numeric: tabular-nums;
```

---

## Spacing & Layout

### Spacing Scale

**4px Grid System** - All spacing should use multiples of 4px

```css
--spacing-0: 0
--spacing-1: 0.25rem   /* 4px */
--spacing-2: 0.5rem    /* 8px */
--spacing-3: 0.75rem   /* 12px */
--spacing-4: 1rem      /* 16px */
--spacing-5: 1.25rem   /* 20px */
--spacing-6: 1.5rem    /* 24px */
--spacing-8: 2rem      /* 32px */
--spacing-10: 2.5rem   /* 40px */
--spacing-12: 3rem     /* 48px */
--spacing-16: 4rem     /* 64px */
--spacing-24: 6rem     /* 96px */
```

### Layout Containers

**Container**
```css
max-width: 1400px (2xl breakpoint)
padding: 2rem (32px)
margin: 0 auto (centered)
```

**Responsive Breakpoints**
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1400px

### Border Radius

```css
--radius: 0.625rem (10px) /* Standard radius */
```

**Derivative Radii:**
- `lg`: `var(--radius)` (10px)
- `md`: `calc(var(--radius) - 2px)` (8px)
- `sm`: `calc(var(--radius) - 4px)` (6px)
- `full`: `9999px` (pills, avatars)
- `xl`: `0.75rem` (12px, special cases)

---

## Component Patterns

### Buttons

#### Variants

**Default (Primary)**
```css
background: var(--primary)
color: var(--primary-foreground)
shadow: sm
hover: bg-primary/90 + shadow-md
active: scale-[0.98]
```

**Destructive**
```css
background: var(--destructive)
color: var(--destructive-foreground)
shadow: sm
hover: bg-destructive/90 + shadow-md
```

**Outline**
```css
border: 1px solid var(--input)
background: var(--background)
hover: bg-accent + text-accent-foreground
```

**Secondary**
```css
background: var(--secondary)
color: var(--secondary-foreground)
hover: bg-secondary/80
```

**Ghost**
```css
background: transparent
hover: bg-accent + text-accent-foreground
```

**Link**
```css
color: var(--primary)
text-decoration: underline-offset-4
hover: underline
```

#### Sizes

- `sm`: height 36px, padding 12px, text xs
- `default`: height 40px, padding 16px, text sm
- `lg`: height 44px, padding 32px, text base
- `icon`: 40px × 40px square

#### States

**Loading**
```jsx
<Button isLoading>
  <Loader2 className="h-4 w-4 animate-spin" />
  Loading...
</Button>
```

**Disabled**
```css
pointer-events: none
opacity: 0.5
```

### Cards

#### Standard Card
```css
background: var(--card)
border: 1px solid var(--border)
border-radius: var(--radius)
box-shadow: 0 1px 3px rgb(0 0 0 / 0.1)
```

#### Card Structure
```jsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
  <CardFooter>
    {/* Actions */}
  </CardFooter>
</Card>
```

#### Card Spacing
- Header padding: 24px
- Content padding: 24px (top: 0 to connect with header)
- Footer padding: 24px (top: 0)

#### Hover Effect
```css
transition: box-shadow 200ms ease
hover: box-shadow-md
```

### KPI Cards

**Special Design Pattern**

```css
/* Gradient overlay on hover */
.kpi-card:hover::before {
  background: linear-gradient(to bottom right,
    var(--primary)/5%, transparent, var(--accent)/5%);
  opacity: 1;
}

/* Icon container */
.kpi-icon {
  height: 44px;
  width: 44px;
  border-radius: 12px;
  background: linear-gradient(to bottom right,
    var(--primary)/10%, var(--accent)/10%);
  border: 1px solid var(--primary)/20%;
}
```

### Badges

#### Variants

**Default**
```css
background: var(--primary)
color: var(--primary-foreground)
```

**Success**
```css
background: hsl(142, 71%, 45%)
color: white
```

**Warning**
```css
background: hsl(38, 92%, 50%)
color: white
```

**Destructive**
```css
background: var(--destructive)
color: white
```

**Outline**
```css
border: 1px solid var(--border)
color: var(--foreground)
```

#### Size
```css
padding: 2px 10px
font-size: 0.75rem (12px)
font-weight: 600 (Semibold)
border-radius: 9999px (full)
```

### Elevation System

**Shadow Levels** - Use for depth hierarchy

```css
/* Level 1 - Subtle */
.elevation-1 {
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1),
              0 1px 2px -1px rgb(0 0 0 / 0.1);
}

/* Level 2 - Standard */
.elevation-2 {
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1),
              0 2px 4px -2px rgb(0 0 0 / 0.1);
}

/* Level 3 - Elevated */
.elevation-3 {
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1),
              0 4px 6px -4px rgb(0 0 0 / 0.1);
}

/* Level 4 - Floating */
.elevation-4 {
  box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1),
              0 8px 10px -6px rgb(0 0 0 / 0.1);
}
```

**Usage:**
- Level 1: Cards, inputs
- Level 2: Dropdowns, tooltips
- Level 3: Modals, dialogs
- Level 4: Top-level overlays

### Focus States

**Standard Focus Ring**
```css
outline: none
ring: 2px solid var(--ring)
ring-offset: 2px
ring-offset-color: var(--background)
```

Apply to all interactive elements: buttons, inputs, links, checkboxes.

---

## Animation & Motion

### Duration Tokens

```css
--duration-instant: 100ms   /* Micro-interactions */
--duration-quick: 200ms     /* Standard transitions */
--duration-smooth: 300ms    /* Smooth entrances */
--duration-long: 500ms      /* Complex animations */
```

### Easing Functions

```css
--ease-entrance: cubic-bezier(0.16, 1, 0.3, 1)      /* Smooth entry */
--ease-exit: cubic-bezier(0.7, 0, 0.84, 0)          /* Quick exit */
--ease-interactive: cubic-bezier(0.4, 0, 0.2, 1)    /* UI interactions */
```

### Standard Animations

#### Fade In
```css
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
animation: fadeIn 300ms cubic-bezier(0.16, 1, 0.3, 1);
```

#### Fade Out
```css
@keyframes fadeOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-4px);
  }
}
animation: fadeOut 200ms cubic-bezier(0.7, 0, 0.84, 0);
```

#### Scale In
```css
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
animation: scaleIn 200ms cubic-bezier(0.16, 1, 0.3, 1);
```

#### Slide Up
```css
@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
animation: slideUp 300ms cubic-bezier(0.16, 1, 0.3, 1);
```

#### Pulse Glow
```css
@keyframes pulse-glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
animation: pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
```

### Interactive States

**Button Interaction**
```css
transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
active: scale-[0.98];
```

**Hover Scale**
```css
.interactive:hover {
  transform: translateY(-2px);
}
.interactive:active {
  transform: translateY(0) scale(0.98);
}
```

**Success Pulse**
```css
@keyframes successPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
animation: successPulse 300ms cubic-bezier(0.16, 1, 0.3, 1);
```

### Stagger Animations

**Staggered Children** (list items, cards)
```css
.stagger-children > *:nth-child(1) { animation-delay: 0ms; }
.stagger-children > *:nth-child(2) { animation-delay: 50ms; }
.stagger-children > *:nth-child(3) { animation-delay: 100ms; }
.stagger-children > *:nth-child(4) { animation-delay: 150ms; }
.stagger-children > *:nth-child(5) { animation-delay: 200ms; }
```

---

## Design Principles

### 1. Clean & Professional
- Minimalist design with purposeful whitespace
- Subtle gradients for depth without distraction
- Professional SaaS aesthetic suitable for business users

### 2. Data-Focused
- Clear hierarchy emphasizing metrics and insights
- High contrast for data visualization
- Tabular numbers for numerical alignment
- Compact 90% UI scale for information density

### 3. Modern & Accessible
- WCAG AA compliant color contrasts
- Clear focus states for keyboard navigation
- Semantic HTML and ARIA labels
- Responsive design for all screen sizes

### 4. Consistent & Predictable
- 4px spacing grid for visual rhythm
- Standardized component patterns
- Predictable interactive behaviors
- Cohesive color application

### 5. Subtle Motion
- Purposeful animations that enhance UX
- Quick transitions (200ms standard)
- Smooth entrances (300ms)
- No gratuitous or distracting motion

### 6. Gradient Accents
- Primary-to-accent gradients for brand elements
- Subtle background gradients on hover states
- 5-10% opacity for non-intrusive depth
- Used sparingly for visual interest

---

## Usage Guidelines

### Color Application Rules

#### DO:
- Use primary (indigo) for primary actions and brand elements
- Use accent (teal) for data highlights and active states
- Reserve semantic colors (success/warning/destructive) for their intended purposes
- Maintain WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
- Use gradients from primary to accent for brand consistency

#### DON'T:
- Mix semantic colors for non-semantic purposes
- Use destructive color for non-destructive actions
- Override focus ring colors (maintain accessibility)
- Use pure black (#000000) or pure white (#FFFFFF) for text

### Typography Rules

#### DO:
- Use DM Sans for all headings (h1-h4)
- Use Inter for body text and UI elements
- Use tabular numbers for data tables and metrics
- Maintain 90% global scale for UI density
- Use uppercase + wide tracking for labels

#### DON'T:
- Mix more than 2 font weights in a single component
- Use font sizes outside the defined type scale
- Override global 90% scale without design approval
- Use decorative or script fonts

### Spacing Rules

#### DO:
- Use the 4px spacing grid for all margins and padding
- Maintain consistent card padding (24px)
- Use container max-width (1400px) for content areas
- Stack spacing vertically using the spacing scale

#### DON'T:
- Use arbitrary pixel values not on the 4px grid
- Create overly tight layouts (<8px spacing)
- Exceed 1400px container width for content

### Component Usage

#### Buttons
```jsx
// Primary action
<Button variant="default">Save Changes</Button>

// Destructive action
<Button variant="destructive">Delete</Button>

// Secondary action
<Button variant="outline">Cancel</Button>

// Subtle action
<Button variant="ghost">Edit</Button>
```

#### Cards
```jsx
// Standard card
<Card className="shadow-sm">
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Supporting description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

#### KPI Display
```jsx
// Metric with trend
<KPICard
  title="Total Revenue"
  value="$1.2M"
  icon={DollarSign}
  trend={{ value: 12.5, isPositive: true }}
  sparklineData={[/* data */]}
/>
```

#### Badges
```jsx
// Status indicators
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="destructive">Failed</Badge>
```

### Accessibility Requirements

#### Color Contrast
- Normal text (< 18px): 4.5:1 minimum
- Large text (≥ 18px): 3:1 minimum
- UI components: 3:1 minimum

#### Focus Management
- All interactive elements must have visible focus states
- Use standard focus ring (2px primary with 2px offset)
- Maintain logical tab order

#### Semantic HTML
- Use proper heading hierarchy (h1 → h2 → h3)
- Label all form inputs
- Provide alt text for images
- Use semantic landmarks (nav, main, aside)

### Responsive Behavior

#### Mobile (< 768px)
- Single column layouts
- Full-width cards
- Collapsed sidebar (icon-only)
- Touch-friendly targets (min 44px)

#### Tablet (768px - 1024px)
- Two-column layouts where appropriate
- Expanded sidebar with labels
- Optimized card grids

#### Desktop (> 1024px)
- Multi-column layouts
- Full sidebar navigation
- Maximum content width: 1400px
- Optimized data tables

---

## Implementation Notes

### CSS Variables
All colors and design tokens are defined as CSS custom properties in `frontend/src/index.css`. Reference them using:

```css
color: hsl(var(--primary));
background: hsl(var(--card));
border-radius: var(--radius);
padding: var(--spacing-4);
```

### Tailwind Integration
The design system is integrated with Tailwind CSS v4. Use utility classes:

```jsx
<div className="bg-card border border-border rounded-lg p-6 shadow-sm">
  <h3 className="text-2xl font-semibold text-foreground">Title</h3>
  <p className="text-sm text-muted-foreground">Description</p>
</div>
```

### Component Library
Reusable components are located in `frontend/src/components/ui/`. Always use these components rather than recreating patterns.

---

## Version History

**v1.0** - Initial brand guidelines
- Established color system (indigo/teal)
- Defined typography scale (Inter/DM Sans)
- Component patterns and usage rules
- Animation and motion guidelines

---

## Contact & Governance

For questions about these guidelines or to propose changes, contact the design team.

**Approval Required For:**
- New color additions to the palette
- Changes to primary/accent brand colors
- New typography weights or families
- Major component pattern changes
