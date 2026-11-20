# Render every example note to PDF with the obs2pdf from this checkout,
# using either the built-in defaults or your own config.toml.
#
#   make                    # built-in defaults, like CI  -> minutes.pdf, ...
#   make user               # with your config.toml       -> minutes.user.pdf, ...
#   make both               # both sets
#   make minutes.user.pdf   # one example (or minutes.pdf)
#   make user OBS2PDF_FLAGS="-p work"   # extra obs2pdf flags, e.g. a profile
#   make -B user            # force a rebuild
#   make -j both            # in parallel
#   make clean              # remove all PDFs and any kept .typ files
#
# The two sets have their own files, so switching needs no rebuild, and each
# rebuilds only what's out of date: the note, obs2pdf's own sources, and for
# `user` also your config.toml and its templates/ folder.
#
# Your config is the file obs2pdf itself uses: $OBS2PDF_CONFIG, else
# $XDG_CONFIG_HOME/obs2pdf/config.toml, else ~/.config/obs2pdf/config.toml.
# Point elsewhere with  make user USER_CONFIG=path/to/config.toml
#
# Needs uv, pandoc and typst on PATH; the first build downloads the Typst
# packages the templates use.

OBS2PDF ?= uv run obs2pdf
OBS2PDF_FLAGS ?=
USER_CONFIG ?= $(or $(OBS2PDF_CONFIG),$(or $(XDG_CONFIG_HOME),$(HOME)/.config)/obs2pdf/config.toml)
NO_CONFIG := /nonexistent/obs2pdf-config.toml

NOTES := $(wildcard *.md)
PDFS := $(NOTES:.md=.pdf)
USER_PDFS := $(NOTES:.md=.user.pdf)

# Rebuild when obs2pdf itself changes, not just the note.
SOURCES := $(wildcard ../src/obs2pdf/*.py ../src/obs2pdf/*.toml \
                      ../src/obs2pdf/templates/*.typ)
USER_SOURCES := $(wildcard $(USER_CONFIG) $(dir $(USER_CONFIG))templates/*.typ)

.DEFAULT_GOAL := default
.PHONY: default user both clean
.DELETE_ON_ERROR:

default: $(PDFS)

user: $(USER_PDFS)

both: default user

%.pdf: %.md $(SOURCES)
	OBS2PDF_CONFIG=$(NO_CONFIG) $(OBS2PDF) $< -o $@ $(OBS2PDF_FLAGS)

%.user.pdf: %.md $(SOURCES) $(USER_SOURCES)
	OBS2PDF_CONFIG=$(USER_CONFIG) $(OBS2PDF) $< -o $@ $(OBS2PDF_FLAGS)

clean:
	rm -f $(PDFS) $(USER_PDFS) $(NOTES:.md=.typ) .*.obs2pdf.typ

# Fail early with a hint instead of silently rendering with the defaults.
ifneq ($(filter user %.user.pdf,$(MAKECMDGOALS)),)
ifeq ($(wildcard $(USER_CONFIG)),)
$(error No config at $(USER_CONFIG); run `obs2pdf config init` or pass USER_CONFIG=path)
endif
endif
