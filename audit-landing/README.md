# Deep-Audit Landing Page

## Overview

This is a **security-sensitive, enterprise-grade audit entry page** designed for CTOs, Heads of Engineering, and security-conscious technical leaders.

**This is NOT:**
- A marketing website
- A SaaS onboarding flow
- A dashboard
- A product with animations or visual flair

**This IS:**
- A trust-establishing audit entry page
- Focused on legal clarity and restraint
- Designed to communicate scope and authorization
- Report-centric (the audit output is the product)

---

## Critical Design Constraints

### 1. Legal & Authorization Clarity (MANDATORY)
- Explicitly states audit is conducted with authorization
- No infrastructure access attempted
- No authentication bypass attempted
- Footer contains legally critical disclaimers

### 2. Terminology Control (MANDATORY)
- **NEVER** uses the word "attack"
- Always uses: "Simulation", "Test case", "Behavioral scenario"

### 3. Read-Only Assurance (MANDATORY)
- Clearly states: Read-only prompts
- No state mutation
- No destructive actions
- No triggering of real business workflows

### 4. Report-Centric Experience (MANDATORY)
- The result is a downloadable artifact
- PDF / Markdown / Web report formats supported
- The report is the primary product

### 5. No Friction, No Lock-in (MANDATORY)
- No login
- No account creation
- No onboarding flow
- No upsell banners
- **ONE CTA only:** "Install SAFE-SPEED Governance Gateway"

---

## Tech Stack

- **Next.js 14** (App Router)
- **React 18**
- **Tailwind CSS**
- **TypeScript**
- Desktop-first, responsive
- **No animations**
- **No gradients**
- **No marketing illustrations**
- Accessibility-friendly

---

## Page Sections

All content is **FIXED** and implemented exactly as specified:

1. **Hero Section**
   - Title: "Deep-Audit: Black-Box AI Safety & Governance Readiness Scan"
   - Subtitle explaining non-invasive approach
   - Simple text flow diagram

2. **Trust & Scope Section** (3 columns)
   - Black-Box Only
   - Safe & Authorized
   - Fast & Lightweight

3. **What We Test** (4 items)
   - Prompt Injection & Instruction Hijacking
   - Hallucination & Fabrication
   - PII / Policy / Secret Leakage
   - Unsafe Action Compliance

4. **How It Works** (4 numbered steps)
   - Provide endpoint
   - Run simulations
   - Generate report
   - Receive PDF/Web report

5. **Output Preview** (Static mock)
   - Safety Score: 42/100 (Critical)
   - Red-highlighted evidence
   - Taxonomy breakdown chart

6. **Primary CTA**
   - "Request a Free Audit Scan" button
   - Disclaimer text below

7. **Footer - LEGAL & SCOPE DISCLAIMER**
   - Authorization statements
   - No infrastructure access
   - Application-layer only
   - Not penetration testing

---

## Installation & Running Locally

### Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

### Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

The application will be available at:
```
http://localhost:3000
```

### Build for Production

```bash
# Create production build
npm run build

# Start production server
npm start
```

---

## File Structure

```
audit-landing/
├── app/
│   ├── globals.css          # Minimal, professional styling
│   ├── layout.tsx            # Root layout with metadata
│   └── page.tsx              # Main landing page component
├── package.json              # Dependencies
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Tailwind configuration
├── postcss.config.js         # PostCSS configuration
├── next.config.js            # Next.js configuration
└── README.md                 # This file
```

---

## Design Principles

### Minimalism and Restraint
- No animations (explicitly disabled in CSS)
- No gradients
- No decorative elements
- Professional gray color palette
- Clean borders and spacing

### Accessibility
- Semantic HTML
- Proper heading hierarchy
- Screen reader friendly
- Keyboard navigable
- Sufficient color contrast

### Desktop-First
- Optimized for desktop viewing
- Responsive but not mobile-first
- Professional business context

---

## Copy Control

**All copy is FIXED and must NOT be changed:**

- Hero title and subtitle (exact wording)
- Three-column trust section (exact bullets)
- What We Test descriptions (factual, no emojis)
- How It Works steps (exact wording)
- Output preview labels
- CTA button text
- Footer legal disclaimers (verbatim)

**Terminology Rules:**
- ❌ "Attack" (NEVER use)
- ✅ "Simulation"
- ✅ "Test case"
- ✅ "Behavioral scenario"

---

## Legal Compliance

The footer contains legally critical disclaimers that MUST be present:

1. "This audit was conducted with explicit authorization."
2. "No attempt was made to access infrastructure or bypass authentication."
3. "Deep-Audit performs application-layer behavioral analysis only."
4. "This assessment does not perform penetration testing."

These statements establish:
- Authorization scope
- No infrastructure access
- No auth bypass attempts
- Clear distinction from pen testing

---

## CTA Configuration

The primary CTA button links to:
```
mailto:audit@safe-speed.com?subject=Request Free Audit Scan
```

This can be changed to:
- A contact form
- A scheduling link
- A modal (implementation not included)

**Important:** Only ONE CTA is allowed. No additional CTAs, upsells, or signup flows.

---

## No Additional Features

This implementation includes **EXACTLY** what was specified:

- ✅ One single-page component
- ✅ Clean Tailwind layout
- ✅ All required sections
- ✅ Legal disclaimers
- ✅ Static output preview

**NOT included (by design):**
- ❌ Login/signup
- ❌ Authentication
- ❌ Dashboard
- ❌ Analytics/tracking
- ❌ Multiple pages
- ❌ Marketing animations
- ❌ Illustrations
- ❌ Upsell banners

---

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

---

## Maintenance

This page requires minimal maintenance:

1. **Copy updates:** Edit `app/page.tsx` (must maintain legal disclaimers)
2. **Styling:** Adjust `tailwind.config.js` or `app/globals.css`
3. **CTA link:** Update mailto link in `app/page.tsx`

**Do NOT add:**
- Animations
- Gradients
- Marketing copy
- Additional CTAs
- Tracking scripts (unless legally required)

---

## Deployment

This is a standard Next.js application. Deploy to:

- **Vercel:** `vercel deploy`
- **Netlify:** Connect repository
- **Docker:** Use standard Next.js Docker setup
- **Custom server:** `npm run build && npm start`

---

## Security Considerations

- No user input collected on page
- No cookies or tracking (by design)
- No third-party scripts
- No analytics (can be added if needed)
- Static content only
- CTA uses mailto (no form submission)

---

## Compliance Notes

This page is designed for compliance with:

- Legal authorization requirements
- Scope limitation statements
- No pen testing disclaimers
- Read-only assurance

**Do NOT remove or modify** the footer legal disclaimers without legal review.

---

## Support

For questions or issues:
- Technical: Review Next.js documentation
- Content: All copy is fixed per specification
- Legal: Consult legal team before modifying disclaimers

---

**Version:** 1.0.0
**Last Updated:** 2025-12-12
**Status:** Production Ready
