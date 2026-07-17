.PHONY: align deploy occurrences clean help

# Chemins
SQLITE ?= /tmp/strong.sqlite
MODEL ?= glm-5.2:cloud

# Construction de l'alignement (LSG -> BYM)
align:
	@echo "═══ Détection des décalages de versification ═══"
	python3 scripts/detect_versif_offsets.py
	@echo ""
	@echo "═══ Reconstruction de l'alignement ═══"
	python3 scripts/build_strongs.py --sqlite $(SQLITE)
	@echo ""
	@echo "═══ Mise à jour du dictionnaire ═══"
	python3 scripts/build_gloss_dict.py
	@echo ""
	@echo "══️ Alignement final ═══"
	python3 scripts/build_strongs.py --sqlite $(SQLITE)
	@echo ""
	@echo "══️ Index Strong's → versets ═══"
	python3 scripts/build_strong_index.py
	@echo ""
	@echo "══️ Occurrences ═══"
	python3 -c "import json; from collections import Counter; s=json.load(open('db/strongs/bym_strongs.json')); occ=Counter(); [occ.update({seg['strong']:1}) for segs in s.values() for seg in segs if seg.get('strong')]; json.dump(dict(occ), open('db/strongs/occurrences.json','w'), ensure_ascii=False)"
	@echo "✅ Alignement terminé"

# Construction du lexique (depuis strong.sqlite)
lexicon:
	@echo "══️ Construction du lexique ═══"
	python3 scripts/build_lexicon.py --sqlite $(SQLITE)

# Alignement par LLM (arrière-plan)
llm:
	@echo "══️ Lancement de l'alignement LLM ═══"
	@echo "Modèle: $(MODEL)"
	@echo "Log: /tmp/llm-align.log"
	PYTHONUNBUFFERED=1 nohup python3 scripts/align_with_llm.py --model $(MODEL) --batch-size 1 --sqlite $(SQLITE) > /tmp/llm-align.log 2>&1 &
	@echo "PID: $$!"
	@echo "Suivre: tail -f /tmp/llm-align.log"

# Arrêter le LLM
llm-stop:
	@-kill $$(! ps aux | grep "align_with_llm" | grep -v grep | awk '{print $$2}') 2>/dev/null
	@echo "LLM arrêté"

# Déploiement sur Vercel
deploy:
	@echo "══️ Déploiement Vercel ═══"
	vercel deploy --prod --yes

# Alignement + Déploiement
all: align deploy
	@echo "✅ Alignement + déploiement terminés"

# Nettoyage
clean:
	@-rm -f /tmp/llm-align.log
	@-rm -rf scripts/__pycache__
	@echo "✅ Nettoyé"

# Aide
help:
	@echo "Commandes disponibles:"
	@echo ""
	@echo "  make align     - Reconstruire l'alignement LSG→BYM + dictionnaire + index + occurrences"
	@echo "  make lexicon   - Reconstruire le lexique Strong's depuis strong.sqlite"
	@echo "  make llm       - Lancer l'alignement LLM en arrière-plan"
	@echo "  make llm-stop  - Arrêter l'alignement LLM"
	@echo "  make deploy    - Déployer sur Vercel (production)"
	@echo "  make all       - Alignement + déploiement"
	@echo "  make clean     - Nettoyer les fichiers temporaires"
	@echo ""
	@echo "Variables:"
	@echo "  SQLITE  - chemin vers strong.sqlite (défaut: /tmp/strong.sqlite)"
	@echo "  MODEL   - modèle Ollama pour LLM (défaut: glm-5.2:cloud)"
	@echo ""
	@echo "Exemples:"
	@echo "  make align"
	@echo "  make deploy"
	@echo "  make all"
	@echo "  make llm MODEL=kimi-k2.7-code:cloud"