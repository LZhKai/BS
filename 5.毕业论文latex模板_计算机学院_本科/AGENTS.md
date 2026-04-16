# Repository Guidelines

## Project Structure & Module Organization
This repository is a LaTeX thesis template centered on one main entry file:
- `main.tex`: thesis content, front matter, chapters, appendix, and references.
- `wzuthesis.cls`: custom class file defining page layout, chapter/section styles, cover pages, and bibliography formatting.
- `main.bib`: bibliography database.
- `image/`: figures and screenshots used in chapters (for example `image/chap04/`).
- `fonts/`: bundled Chinese fonts required by the template.

Generated build artifacts (`.aux`, `.log`, `.out`, `.toc`, `.bbl`, `.blg`, `.synctex.gz`, `main.pdf`) should not be edited manually.

## Build, Test, and Development Commands
Use XeLaTeX and BibTeX from the repository root:

```powershell
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

- First XeLaTeX pass builds structure.
- `bibtex main` resolves citations from `main.bib`.
- Final XeLaTeX passes resolve references, TOC, and numbering.

Optional cleanup:

```powershell
Remove-Item main.aux,main.log,main.out,main.toc,main.bbl,main.blg,main.synctex.gz -ErrorAction SilentlyContinue
```

## Coding Style & Naming Conventions
- Use UTF-8 encoding and keep line endings consistent.
- Prefer 2-4 space indentation in environments; align related LaTeX commands for readability.
- Use clear section labels and consistent chapter/section hierarchy.
- Name image assets descriptively (for example `image/chap04/system-architecture.png`).
- Keep class-level styling changes in `wzuthesis.cls`; keep thesis content in `main.tex`.

## Testing Guidelines
No unit-test framework is configured; validation is compilation-based:
- Build must complete with no fatal errors.
- Check `main.log` for unresolved references/citations.
- Verify output PDF for TOC, figure/table numbering, bibliography, and appendix formatting.

## Commit & Pull Request Guidelines
No `.git` history is present in this folder, so adopt a clear convention:
- Commit format: `type(scope): summary` (for example `docs(main): refine abstract wording`).
- Keep commits focused (content, class style, or asset updates separately).
- PRs should include: purpose, changed files, PDF impact summary, and screenshots for major layout changes.
- Link related task/issue IDs when available.
