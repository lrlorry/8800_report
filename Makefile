.PHONY: pdf pdf-zh verify-pdfs ch7-data clean wordcount
pdf:
	latexmk -pdf -outdir=build/thesis2 -jobname=thesis2 variants/thesis2/main.tex
	cp build/thesis2/thesis2.pdf thesis.pdf

pdf-zh:
	latexmk -xelatex -outdir=build/thesis2-zh -jobname=thsis2-zh -interaction=nonstopmode -halt-on-error -file-line-error variants/thesis2-zh/main.tex
	cp build/thesis2-zh/thsis2-zh.pdf thesis-zh.pdf

verify-pdfs:
	python3 scripts/verify_canonical_pdfs.py

# Offline analysis of existing records; no GPU benchmark is run.
ch7-data:
	python3 scripts/audit_supplement.py
	python3 scripts/audit_t4_t5.py
	python3 scripts/audit_full_review.py
	python3 scripts/build_ch7.py --source ../JHQ_GPU
	python3 scripts/audit_ch7_round2.py
	python3 scripts/build_appendix.py

clean:
	latexmk -c -outdir=build/thesis2 -jobname=thesis2 variants/thesis2/main.tex
	latexmk -c -outdir=build/thesis2-zh -jobname=thsis2-zh variants/thesis2-zh/main.tex

# A tooling estimate, not an official course word-count definition.
wordcount:
	@if command -v texcount >/dev/null 2>&1; then \
		texcount -inc -sum -sub=chapter variants/thesis2/main.tex; \
	else \
		printf '%s\n' 'Optional dependency missing: texcount. PDF compilation is unaffected.'; \
		exit 1; \
	fi
