# Makefile

PYTHON=python2
RM=rm -f

MWPARSER=$(PYTHON) mwparser.py

all:

clean:
	-$(RM) out

test:
	$(MWPARSER) jawiki.xml.bz2 >out 2>&1
