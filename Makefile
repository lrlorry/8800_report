.PHONY: pdf pdf-zh ch7-data clean wordcount
pdf:
	latexmk -pdf main.tex
	cp build/main.pdf thesis.pdf

pdf-zh:
	python3 scripts/build_zh_tables.py
	latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error main-zh.tex
	cp build/main-zh.pdf thesis-zh.pdf

# Offline analysis of existing records; no GPU benchmark is run.
ch7-data:
	python3 scripts/build_ch7.py --source ../JHQ_GPU

clean:
	latexmk -c main.tex

# A tooling estimate, not an official course word-count definition.
wordcount:
	@if command -v texcount >/dev/null 2>&1; then \
		texcount -inc -sum -sub=chapter main.tex; \
	else \
		printf '%s\n' 'Optional dependency missing: texcount. PDF compilation is unaffected.'; \
		exit 1; \
	fi
