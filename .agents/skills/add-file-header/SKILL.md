# Add file header skill

## Objective

Add a standard header to every new file in the repository to ensure minimal metadata (file, author, date, description, license). This skill contains only the header template and guidance; implementing scripts or hooks is optional.

## Scope

Use this skill when:

- A new file is added to the repository and a consistent header is required.
- You want guidance for automating header insertion via hooks or tooling (optional).

This skill does not modify already-versioned files that already contain the header marker.

## Basic template (example)

Templates use the comment style according to the file extension.

Example header (for files using line `#` comments):

# ==================================================
# File:    {filename}
# Author:  {author}
# Date:    {date}
# Desc:    {description}
# License: {license}
# Header:  generated
# ==================================================

Replaceable fields:
- filename: file name
- author: default from `git config user.name` if available
- date: ISO formatted date
- description: short description (optional)
- license: project license or short text

## Recommended usage

1. Manual:

   Copy the template above to the top of new files and fill the fields.

2. Integration with change controls (optional):

   Consider adding a script or hook (for example in pre-commit) that applies this template to added files.

## Implementation details

- The template should include a marker like `Header:  generated` so automated tooling can detect presence.
- Choose the comment style according to the file extension (e.g., `#` for Python/YAML/Markdown, block comments for C/Java/JS, XML comments for HTML/XML).
- Be cautious with formats that do not accept comments (e.g., JSON/TOML) — prefer to keep them unchanged or use sidecar metadata.

## Checklist

- [ ] Review and adapt the template according to project policies
- [ ] Optionally integrate a hook or script to enforce the header on added files
- [ ] Optionally document the guideline in CONTRIBUTING.md

## Notes

This document contains only the template and guidance. No script is included in this skill; implementing automation is optional and outside the scope of this skill.
