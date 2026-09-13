#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
latexmk -xelatex -bibtex -interaction=nonstopmode -halt-on-error \
  -outdir=build-motivation motivation_method.tex
cp build-motivation/motivation_method.pdf motivation_method.pdf
