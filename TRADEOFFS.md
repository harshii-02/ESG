# Tradeoffs

## 1. No Authentication

The data model is tenant-ready, but the prototype uses a seeded demo organization instead of login. This keeps the review workflow simple and avoids spending assignment time on commodity auth screens.

## 2. CSV Instead Of Deep API Integrations

SAP, utility, and travel integrations can each become a project by themselves. I chose realistic CSV shapes because they are common during onboarding and let the prototype demonstrate parsing, normalization, failure handling, and auditability.

## 3. Simple Emission Factors

The app uses transparent placeholder factors in code. Production should use a governed factor library with geography, effective dates, source citations, and versioning. The prototype keeps factors simple so reviewers can inspect the data flow clearly.

