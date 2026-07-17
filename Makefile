.PHONY: test eval package offline release clean help

PYTHON ?= python
SKILL_DIR := skill/grok-geo
VERSION := 1.0.0
DIST_ZIP := dist/grok-geo-v1.0.0.zip

help:
	@echo "Targets: test eval package offline release clean"

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

eval:
	$(PYTHON) $(SKILL_DIR)/evals/run_evals.py

offline:
	$(PYTHON) $(SKILL_DIR)/examples/run_offline_demo.py --base-dir ./geo-audit-runs --keep

package:
	$(PYTHON) scripts/package_skill.py

release: test eval package
	$(PYTHON) $(SKILL_DIR)/evals/run_evals.py --output dist/eval-report-v$(VERSION).json
	$(PYTHON) -c "import shutil; shutil.copy2('$(SKILL_DIR)/CHANGELOG.md', 'dist/CHANGELOG-v$(VERSION).md')"
	@echo "Release artifacts generated in dist/"

clean:
	$(PYTHON) -c "import shutil,pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').glob('**/__pycache__')]"