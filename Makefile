DOCUMENT_OUT := document.pdf
DOCUMENT_MAIN := document.tex
TEX := lualatex

${DOCUMENT_OUT} : ${DOCUMENT_MAIN}
	${TEX} ${DOCUMENT_MAIN} -o ${DOCUMENT_OUT}
