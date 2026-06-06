"""Lightweight, deterministic internationalisation (i18n) layer for FinClariX.

FinClariX's business plan promises that "everyone can choose their preferred
language". Before this module existed, the language selector only affected
AI-generated clause explanations (and only when an Anthropic API key was
configured) — every other piece of on-screen text (section headers, risk
badges, button labels, the four breakdown-part labels, the Financial Exposure
Summary heading, etc.) stayed in English regardless of the selection.

This module closes that gap with a small, static translation table plus a
single lookup helper, `t(key, lang)`. It is intentionally:

  * STATIC / DETERMINISTIC — a plain dict lookup, no network calls, no AI.
    This keeps the multilingual UI working perfectly even with no
    ANTHROPIC_API_KEY set, consistent with the rest of the app's philosophy
    that AI only ever *polishes* a deterministic baseline, never replaces it.

  * ENGLISH-FIRST — "English" is both the default UI language and the
    fallback for (a) any key missing from a language's table and (b) any
    language not present in `_STRINGS` at all. Nothing can ever render blank.

Scope note — what this module deliberately does NOT translate:
  The long, free-form narrative sentences in `src/clause_breakdown.py`
  (`_WHY_TEMPLATES` / `_ACTION_TEMPLATES`) and the composed exposure-summary
  phrases in `src/financial_extractor.py` (e.g. "early termination penalty
  based on three months of €1,350 rent") are assembled by concatenating
  fragments and inserting numbers. Word order, articles, and noun/adjective
  agreement differ enough across these 13 languages that naively translating
  the fragments would frequently produce broken or misleading sentences —
  arguably worse than showing clear English. Those deterministic narrative
  strings therefore stay in English as the baseline (numbers and currency
  symbols are already language-neutral); when an API key is configured,
  `explain_clause()` already asks Claude to respond in the selected language,
  producing natural, grammatically correct prose on top of that baseline.
  Everything a user sees on first load and on every results page — labels,
  headers, badges, buttons, section titles — IS translated below, so picking
  a language visibly changes the whole interface.
"""

# Language names below match `_LANGUAGES` in app.py exactly.
_FALLBACK_LANG = "English"

_STRINGS: dict[str, dict[str, str]] = {

    "English": {
        "ai_disabled_notice": (
            "AI explanations are disabled (no API key set) — showing the "
            "rule-based breakdown in English."
        ),
        "risk_summary": "Risk Summary",
        "metric_high": "High Risk",
        "metric_medium": "Medium Risk",
        "metric_low": "Low Risk",
        "metric_informational": "Informational",
        "section_informational": "Informational Risk",
        "badge_high": "HIGH",
        "badge_medium": "MEDIUM",
        "badge_low": "LOW",
        "badge_informational": "INFORMATIONAL",
        "clause_singular": "clause",
        "clause_plural": "clauses",
        "flagged_terms": "Flagged terms",
        "plain_talk": "Plain talk",
        "full_clause_text": "Full clause text",
        "exposure_title": "Financial Exposure Summary",
        "exposure_subtitle": (
            "Figures below are computed deterministically from amounts and time "
            "periods stated directly in the contract — not estimated by AI."
        ),
        "label_explanation": "Plain-language explanation",
        "label_why": "Why it matters",
        "label_financial_impact": "Potential financial impact",
        "label_suggested_action": "Suggested action before signing",
        "download_report": "Download Markdown Report",
        "settings_title": "Settings",
        "language_label": "Language",
        "enable_ai_label": "Enable AI explanations",
        "how_it_works_title": "How it works",
        "analyse_button": "Analyse Contract",
        "tab_upload": "Upload PDF",
        "tab_paste": "Paste Text",
        "translation_unavailable_notice": "Translation unavailable — showing English.",
    },

    "Spanish": {
        "ai_disabled_notice": (
            "Las explicaciones de IA están desactivadas (no hay clave de API) "
            "— se muestra el desglose basado en reglas en inglés."
        ),
        "risk_summary": "Resumen de riesgos",
        "metric_high": "Riesgo alto",
        "metric_medium": "Riesgo medio",
        "metric_low": "Riesgo bajo",
        "metric_informational": "Informativo",
        "section_informational": "Riesgo informativo",
        "badge_high": "ALTO",
        "badge_medium": "MEDIO",
        "badge_low": "BAJO",
        "badge_informational": "INFORMATIVO",
        "clause_singular": "cláusula",
        "clause_plural": "cláusulas",
        "flagged_terms": "Términos señalados",
        "plain_talk": "En palabras sencillas",
        "full_clause_text": "Texto completo de la cláusula",
        "exposure_title": "Resumen de exposición financiera",
        "exposure_subtitle": (
            "Las cifras se calculan de forma determinista a partir de los importes "
            "y plazos indicados directamente en el contrato — no son estimaciones "
            "de la IA."
        ),
        "label_explanation": "Explicación en lenguaje sencillo",
        "label_why": "Por qué es importante",
        "label_financial_impact": "Posible impacto financiero",
        "label_suggested_action": "Acción sugerida antes de firmar",
        "download_report": "Descargar informe en Markdown",
        "settings_title": "Ajustes",
        "language_label": "Idioma",
        "enable_ai_label": "Activar explicaciones con IA",
        "how_it_works_title": "Cómo funciona",
        "analyse_button": "Analizar contrato",
        "tab_upload": "Subir PDF",
        "tab_paste": "Pegar texto",
        "translation_unavailable_notice": "Traducción no disponible — se muestra en inglés.",
    },

    "Dutch": {
        "ai_disabled_notice": (
            "AI-uitleg is uitgeschakeld (geen API-sleutel) — de "
            "regelgebaseerde uitleg wordt in het Engels getoond."
        ),
        "risk_summary": "Risico-overzicht",
        "metric_high": "Hoog risico",
        "metric_medium": "Gemiddeld risico",
        "metric_low": "Laag risico",
        "metric_informational": "Informatief",
        "section_informational": "Informatief risico",
        "badge_high": "HOOG",
        "badge_medium": "GEMIDDELD",
        "badge_low": "LAAG",
        "badge_informational": "INFORMATIEF",
        "clause_singular": "clausule",
        "clause_plural": "clausules",
        "flagged_terms": "Gemarkeerde termen",
        "plain_talk": "In gewone taal",
        "full_clause_text": "Volledige clausuletekst",
        "exposure_title": "Overzicht financiële blootstelling",
        "exposure_subtitle": (
            "Onderstaande cijfers worden deterministisch berekend op basis van "
            "bedragen en termijnen die rechtstreeks in het contract staan — niet "
            "geschat door AI."
        ),
        "label_explanation": "Uitleg in gewone taal",
        "label_why": "Waarom dit ertoe doet",
        "label_financial_impact": "Mogelijke financiële impact",
        "label_suggested_action": "Aanbevolen actie vóór ondertekening",
        "download_report": "Markdown-rapport downloaden",
        "settings_title": "Instellingen",
        "language_label": "Taal",
        "enable_ai_label": "AI-uitleg inschakelen",
        "how_it_works_title": "Hoe het werkt",
        "analyse_button": "Contract analyseren",
        "tab_upload": "PDF uploaden",
        "tab_paste": "Tekst plakken",
        "translation_unavailable_notice": "Vertaling niet beschikbaar — Engels wordt getoond.",
    },

    "French": {
        "ai_disabled_notice": (
            "Les explications par IA sont désactivées (pas de clé API) — la "
            "décomposition basée sur des règles s'affiche en anglais."
        ),
        "risk_summary": "Résumé des risques",
        "metric_high": "Risque élevé",
        "metric_medium": "Risque moyen",
        "metric_low": "Risque faible",
        "metric_informational": "Informatif",
        "section_informational": "Risque informatif",
        "badge_high": "ÉLEVÉ",
        "badge_medium": "MOYEN",
        "badge_low": "FAIBLE",
        "badge_informational": "INFORMATIF",
        "clause_singular": "clause",
        "clause_plural": "clauses",
        "flagged_terms": "Termes signalés",
        "plain_talk": "En clair",
        "full_clause_text": "Texte intégral de la clause",
        "exposure_title": "Résumé de l'exposition financière",
        "exposure_subtitle": (
            "Les chiffres ci-dessous sont calculés de manière déterministe à "
            "partir des montants et délais indiqués directement dans le contrat "
            "— ils ne sont pas estimés par l'IA."
        ),
        "label_explanation": "Explication en langage clair",
        "label_why": "Pourquoi c'est important",
        "label_financial_impact": "Impact financier potentiel",
        "label_suggested_action": "Action suggérée avant de signer",
        "download_report": "Télécharger le rapport Markdown",
        "settings_title": "Paramètres",
        "language_label": "Langue",
        "enable_ai_label": "Activer les explications par IA",
        "how_it_works_title": "Comment ça marche",
        "analyse_button": "Analyser le contrat",
        "tab_upload": "Importer un PDF",
        "tab_paste": "Coller le texte",
        "translation_unavailable_notice": "Traduction indisponible — affichage en anglais.",
    },

    "German": {
        "ai_disabled_notice": (
            "KI-Erklärungen sind deaktiviert (kein API-Schlüssel) — die "
            "regelbasierte Aufschlüsselung wird auf Englisch angezeigt."
        ),
        "risk_summary": "Risikoübersicht",
        "metric_high": "Hohes Risiko",
        "metric_medium": "Mittleres Risiko",
        "metric_low": "Geringes Risiko",
        "metric_informational": "Informativ",
        "section_informational": "Informatives Risiko",
        "badge_high": "HOCH",
        "badge_medium": "MITTEL",
        "badge_low": "GERING",
        "badge_informational": "INFORMATIV",
        "clause_singular": "Klausel",
        "clause_plural": "Klauseln",
        "flagged_terms": "Markierte Begriffe",
        "plain_talk": "Klartext",
        "full_clause_text": "Vollständiger Klauseltext",
        "exposure_title": "Übersicht der finanziellen Risiken",
        "exposure_subtitle": (
            "Die folgenden Zahlen werden deterministisch aus den im Vertrag "
            "genannten Beträgen und Fristen berechnet — nicht von einer KI "
            "geschätzt."
        ),
        "label_explanation": "Erklärung in einfacher Sprache",
        "label_why": "Warum das wichtig ist",
        "label_financial_impact": "Mögliche finanzielle Auswirkung",
        "label_suggested_action": "Empfohlene Maßnahme vor der Unterschrift",
        "download_report": "Markdown-Bericht herunterladen",
        "settings_title": "Einstellungen",
        "language_label": "Sprache",
        "enable_ai_label": "KI-Erklärungen aktivieren",
        "how_it_works_title": "So funktioniert es",
        "analyse_button": "Vertrag analysieren",
        "tab_upload": "PDF hochladen",
        "tab_paste": "Text einfügen",
        "translation_unavailable_notice": "Übersetzung nicht verfügbar — Anzeige auf Englisch.",
    },

    "Italian": {
        "ai_disabled_notice": (
            "Le spiegazioni IA sono disattivate (nessuna chiave API) — viene "
            "mostrata la suddivisione basata su regole in inglese."
        ),
        "risk_summary": "Riepilogo dei rischi",
        "metric_high": "Rischio alto",
        "metric_medium": "Rischio medio",
        "metric_low": "Rischio basso",
        "metric_informational": "Informativo",
        "section_informational": "Rischio informativo",
        "badge_high": "ALTO",
        "badge_medium": "MEDIO",
        "badge_low": "BASSO",
        "badge_informational": "INFORMATIVO",
        "clause_singular": "clausola",
        "clause_plural": "clausole",
        "flagged_terms": "Termini segnalati",
        "plain_talk": "In parole semplici",
        "full_clause_text": "Testo completo della clausola",
        "exposure_title": "Riepilogo dell'esposizione finanziaria",
        "exposure_subtitle": (
            "Le cifre seguenti sono calcolate in modo deterministico a partire "
            "dagli importi e dai periodi indicati direttamente nel contratto — "
            "non sono stime dell'IA."
        ),
        "label_explanation": "Spiegazione in linguaggio semplice",
        "label_why": "Perché è importante",
        "label_financial_impact": "Possibile impatto finanziario",
        "label_suggested_action": "Azione consigliata prima di firmare",
        "download_report": "Scarica il report in Markdown",
        "settings_title": "Impostazioni",
        "language_label": "Lingua",
        "enable_ai_label": "Attiva le spiegazioni IA",
        "how_it_works_title": "Come funziona",
        "analyse_button": "Analizza contratto",
        "tab_upload": "Carica PDF",
        "tab_paste": "Incolla testo",
        "translation_unavailable_notice": "Traduzione non disponibile — visualizzazione in inglese.",
    },

    "Portuguese": {
        "ai_disabled_notice": (
            "As explicações por IA estão desativadas (sem chave de API) — a "
            "análise baseada em regras é exibida em inglês."
        ),
        "risk_summary": "Resumo de riscos",
        "metric_high": "Risco alto",
        "metric_medium": "Risco médio",
        "metric_low": "Risco baixo",
        "metric_informational": "Informativo",
        "section_informational": "Risco informativo",
        "badge_high": "ALTO",
        "badge_medium": "MÉDIO",
        "badge_low": "BAIXO",
        "badge_informational": "INFORMATIVO",
        "clause_singular": "cláusula",
        "clause_plural": "cláusulas",
        "flagged_terms": "Termos sinalizados",
        "plain_talk": "Em linguagem simples",
        "full_clause_text": "Texto completo da cláusula",
        "exposure_title": "Resumo da exposição financeira",
        "exposure_subtitle": (
            "Os valores abaixo são calculados de forma determinística a partir "
            "dos montantes e prazos indicados diretamente no contrato — não são "
            "estimativas da IA."
        ),
        "label_explanation": "Explicação em linguagem simples",
        "label_why": "Por que isso importa",
        "label_financial_impact": "Possível impacto financeiro",
        "label_suggested_action": "Ação sugerida antes de assinar",
        "download_report": "Baixar relatório em Markdown",
        "settings_title": "Configurações",
        "language_label": "Idioma",
        "enable_ai_label": "Ativar explicações por IA",
        "how_it_works_title": "Como funciona",
        "analyse_button": "Analisar contrato",
        "tab_upload": "Enviar PDF",
        "tab_paste": "Colar texto",
        "translation_unavailable_notice": "Tradução indisponível — exibindo em inglês.",
    },

    "Polish": {
        "ai_disabled_notice": (
            "Objaśnienia AI są wyłączone (brak klucza API) — wyświetlane jest "
            "podsumowanie oparte na regułach w języku angielskim."
        ),
        "risk_summary": "Podsumowanie ryzyka",
        "metric_high": "Wysokie ryzyko",
        "metric_medium": "Średnie ryzyko",
        "metric_low": "Niskie ryzyko",
        "metric_informational": "Informacyjne",
        "section_informational": "Ryzyko informacyjne",
        "badge_high": "WYSOKIE",
        "badge_medium": "ŚREDNIE",
        "badge_low": "NISKIE",
        "badge_informational": "INFORMACYJNE",
        "clause_singular": "klauzula",
        "clause_plural": "klauzule",
        "flagged_terms": "Oznaczone terminy",
        "plain_talk": "Po prostu",
        "full_clause_text": "Pełny tekst klauzuli",
        "exposure_title": "Podsumowanie ekspozycji finansowej",
        "exposure_subtitle": (
            "Poniższe kwoty są obliczane w sposób deterministyczny na podstawie "
            "kwot i okresów podanych bezpośrednio w umowie — nie są szacowane "
            "przez AI."
        ),
        "label_explanation": "Wyjaśnienie w prostym języku",
        "label_why": "Dlaczego to ważne",
        "label_financial_impact": "Potencjalny wpływ finansowy",
        "label_suggested_action": "Sugerowane działanie przed podpisaniem",
        "download_report": "Pobierz raport w Markdown",
        "settings_title": "Ustawienia",
        "language_label": "Język",
        "enable_ai_label": "Włącz objaśnienia AI",
        "how_it_works_title": "Jak to działa",
        "analyse_button": "Analizuj umowę",
        "tab_upload": "Prześlij PDF",
        "tab_paste": "Wklej tekst",
        "translation_unavailable_notice": "Tłumaczenie niedostępne — wyświetlanie w języku angielskim.",
    },

    "Romanian": {
        "ai_disabled_notice": (
            "Explicațiile AI sunt dezactivate (nicio cheie API) — se afișează "
            "analiza bazată pe reguli în limba engleză."
        ),
        "risk_summary": "Rezumatul riscurilor",
        "metric_high": "Risc ridicat",
        "metric_medium": "Risc mediu",
        "metric_low": "Risc scăzut",
        "metric_informational": "Informativ",
        "section_informational": "Risc informativ",
        "badge_high": "RIDICAT",
        "badge_medium": "MEDIU",
        "badge_low": "SCĂZUT",
        "badge_informational": "INFORMATIV",
        "clause_singular": "clauză",
        "clause_plural": "clauze",
        "flagged_terms": "Termeni semnalați",
        "plain_talk": "Pe înțelesul tuturor",
        "full_clause_text": "Textul integral al clauzei",
        "exposure_title": "Rezumatul expunerii financiare",
        "exposure_subtitle": (
            "Cifrele de mai jos sunt calculate determinist pe baza sumelor și "
            "perioadelor menționate direct în contract — nu sunt estimate de AI."
        ),
        "label_explanation": "Explicație pe înțelesul tuturor",
        "label_why": "De ce contează",
        "label_financial_impact": "Impact financiar potențial",
        "label_suggested_action": "Acțiune recomandată înainte de semnare",
        "download_report": "Descarcă raportul Markdown",
        "settings_title": "Setări",
        "language_label": "Limbă",
        "enable_ai_label": "Activează explicațiile AI",
        "how_it_works_title": "Cum funcționează",
        "analyse_button": "Analizează contractul",
        "tab_upload": "Încarcă PDF",
        "tab_paste": "Lipește text",
        "translation_unavailable_notice": "Traducere indisponibilă — se afișează în engleză.",
    },

    "Swedish": {
        "ai_disabled_notice": (
            "AI-förklaringar är inaktiverade (ingen API-nyckel) — den "
            "regelbaserade uppdelningen visas på engelska."
        ),
        "risk_summary": "Risköversikt",
        "metric_high": "Hög risk",
        "metric_medium": "Medelhög risk",
        "metric_low": "Låg risk",
        "metric_informational": "Informativ",
        "section_informational": "Informativ risk",
        "badge_high": "HÖG",
        "badge_medium": "MEDEL",
        "badge_low": "LÅG",
        "badge_informational": "INFORMATIV",
        "clause_singular": "klausul",
        "clause_plural": "klausuler",
        "flagged_terms": "Flaggade termer",
        "plain_talk": "Klarspråk",
        "full_clause_text": "Fullständig klausultext",
        "exposure_title": "Sammanfattning av finansiell exponering",
        "exposure_subtitle": (
            "Siffrorna nedan beräknas deterministiskt utifrån belopp och "
            "tidsperioder som anges direkt i avtalet — de är inte uppskattade "
            "av AI."
        ),
        "label_explanation": "Förklaring på vanligt språk",
        "label_why": "Varför det spelar roll",
        "label_financial_impact": "Möjlig ekonomisk påverkan",
        "label_suggested_action": "Föreslagen åtgärd före undertecknande",
        "download_report": "Ladda ner Markdown-rapport",
        "settings_title": "Inställningar",
        "language_label": "Språk",
        "enable_ai_label": "Aktivera AI-förklaringar",
        "how_it_works_title": "Så fungerar det",
        "analyse_button": "Analysera avtal",
        "tab_upload": "Ladda upp PDF",
        "tab_paste": "Klistra in text",
        "translation_unavailable_notice": "Översättning ej tillgänglig — visas på engelska.",
    },

    "Czech": {
        "ai_disabled_notice": (
            "Vysvětlení od AI jsou vypnuta (chybí API klíč) — zobrazuje se "
            "rozbor založený na pravidlech v angličtině."
        ),
        "risk_summary": "Přehled rizik",
        "metric_high": "Vysoké riziko",
        "metric_medium": "Střední riziko",
        "metric_low": "Nízké riziko",
        "metric_informational": "Informativní",
        "section_informational": "Informativní riziko",
        "badge_high": "VYSOKÉ",
        "badge_medium": "STŘEDNÍ",
        "badge_low": "NÍZKÉ",
        "badge_informational": "INFORMATIVNÍ",
        "clause_singular": "ustanovení",
        "clause_plural": "ustanovení",
        "flagged_terms": "Označené pojmy",
        "plain_talk": "Jednoduše řečeno",
        "full_clause_text": "Celý text ustanovení",
        "exposure_title": "Přehled finanční expozice",
        "exposure_subtitle": (
            "Níže uvedené částky jsou počítány deterministicky na základě "
            "částek a lhůt uvedených přímo ve smlouvě — nejsou odhadovány "
            "pomocí AI."
        ),
        "label_explanation": "Vysvětlení jednoduchým jazykem",
        "label_why": "Proč na tom záleží",
        "label_financial_impact": "Možný finanční dopad",
        "label_suggested_action": "Doporučený krok před podpisem",
        "download_report": "Stáhnout zprávu ve formátu Markdown",
        "settings_title": "Nastavení",
        "language_label": "Jazyk",
        "enable_ai_label": "Povolit vysvětlení od AI",
        "how_it_works_title": "Jak to funguje",
        "analyse_button": "Analyzovat smlouvu",
        "tab_upload": "Nahrát PDF",
        "tab_paste": "Vložit text",
        "translation_unavailable_notice": "Překlad není k dispozici — zobrazeno v angličtině.",
    },

    "Hungarian": {
        "ai_disabled_notice": (
            "Az AI-magyarázatok ki vannak kapcsolva (nincs API-kulcs) — a "
            "szabályalapú bontás angol nyelven jelenik meg."
        ),
        "risk_summary": "Kockázati összefoglaló",
        "metric_high": "Magas kockázat",
        "metric_medium": "Közepes kockázat",
        "metric_low": "Alacsony kockázat",
        "metric_informational": "Tájékoztató jellegű",
        "section_informational": "Tájékoztató jellegű kockázat",
        "badge_high": "MAGAS",
        "badge_medium": "KÖZEPES",
        "badge_low": "ALACSONY",
        "badge_informational": "TÁJÉKOZTATÓ",
        "clause_singular": "záradék",
        "clause_plural": "záradékok",
        "flagged_terms": "Megjelölt kifejezések",
        "plain_talk": "Egyszerűen szólva",
        "full_clause_text": "A záradék teljes szövege",
        "exposure_title": "Pénzügyi kitettség összefoglalója",
        "exposure_subtitle": (
            "Az alábbi számok a szerződésben közvetlenül megadott összegek és "
            "időtartamok alapján, determinisztikusan kerülnek kiszámításra — "
            "nem AI általi becslések."
        ),
        "label_explanation": "Magyarázat egyszerű nyelven",
        "label_why": "Miért fontos",
        "label_financial_impact": "Lehetséges pénzügyi hatás",
        "label_suggested_action": "Javasolt lépés aláírás előtt",
        "download_report": "Markdown jelentés letöltése",
        "settings_title": "Beállítások",
        "language_label": "Nyelv",
        "enable_ai_label": "AI-magyarázatok engedélyezése",
        "how_it_works_title": "Hogyan működik",
        "analyse_button": "Szerződés elemzése",
        "tab_upload": "PDF feltöltése",
        "tab_paste": "Szöveg beillesztése",
        "translation_unavailable_notice": "A fordítás nem érhető el — angol nyelven jelenik meg.",
    },

    "Greek": {
        "ai_disabled_notice": (
            "Οι επεξηγήσεις AI είναι απενεργοποιημένες (δεν υπάρχει κλειδί "
            "API) — εμφανίζεται η ανάλυση βάσει κανόνων στα αγγλικά."
        ),
        "risk_summary": "Σύνοψη κινδύνου",
        "metric_high": "Υψηλός κίνδυνος",
        "metric_medium": "Μέτριος κίνδυνος",
        "metric_low": "Χαμηλός κίνδυνος",
        "metric_informational": "Ενημερωτικό",
        "section_informational": "Ενημερωτικός κίνδυνος",
        "badge_high": "ΥΨΗΛΟΣ",
        "badge_medium": "ΜΕΤΡΙΟΣ",
        "badge_low": "ΧΑΜΗΛΟΣ",
        "badge_informational": "ΕΝΗΜΕΡΩΤΙΚΟ",
        "clause_singular": "ρήτρα",
        "clause_plural": "ρήτρες",
        "flagged_terms": "Επισημασμένοι όροι",
        "plain_talk": "Σε απλά λόγια",
        "full_clause_text": "Πλήρες κείμενο ρήτρας",
        "exposure_title": "Σύνοψη οικονομικής έκθεσης",
        "exposure_subtitle": (
            "Τα παρακάτω ποσά υπολογίζονται ντετερμινιστικά από τα ποσά και τις "
            "χρονικές περιόδους που αναφέρονται απευθείας στη σύμβαση — δεν "
            "εκτιμώνται από AI."
        ),
        "label_explanation": "Επεξήγηση σε απλή γλώσσα",
        "label_why": "Γιατί έχει σημασία",
        "label_financial_impact": "Πιθανός οικονομικός αντίκτυπος",
        "label_suggested_action": "Προτεινόμενη ενέργεια πριν την υπογραφή",
        "download_report": "Λήψη αναφοράς Markdown",
        "settings_title": "Ρυθμίσεις",
        "language_label": "Γλώσσα",
        "enable_ai_label": "Ενεργοποίηση επεξηγήσεων AI",
        "how_it_works_title": "Πώς λειτουργεί",
        "analyse_button": "Ανάλυση σύμβασης",
        "tab_upload": "Μεταφόρτωση PDF",
        "tab_paste": "Επικόλληση κειμένου",
        "translation_unavailable_notice": "Η μετάφραση δεν είναι διαθέσιμη — εμφανίζεται στα αγγλικά.",
    },

    # Simplified Chinese — added on request as a high-demand demo language
    # (also requires `_LANGUAGES` in app.py to list "Chinese").
    "Chinese": {
        "ai_disabled_notice": (
            "AI 解释功能已禁用（未设置 API 密钥）——以下显示基于规则的英文解读。"
        ),
        "risk_summary": "风险摘要",
        "metric_high": "高风险",
        "metric_medium": "中风险",
        "metric_low": "低风险",
        "metric_informational": "仅供参考",
        "section_informational": "仅供参考风险",
        "badge_high": "高风险",
        "badge_medium": "中风险",
        "badge_low": "低风险",
        "badge_informational": "参考信息",
        "clause_singular": "条款",
        "clause_plural": "条款",
        "flagged_terms": "标记的关键词",
        "plain_talk": "大白话解读",
        "full_clause_text": "条款全文",
        "exposure_title": "财务风险敞口摘要",
        "exposure_subtitle": (
            "以下数字均根据合同中直接列明的金额和期限确定性地计算得出 —— 并非由 AI 估算。"
        ),
        "label_explanation": "通俗解释",
        "label_why": "为何重要",
        "label_financial_impact": "潜在财务影响",
        "label_suggested_action": "签约前的建议行动",
        "download_report": "下载 Markdown 报告",
        "settings_title": "设置",
        "language_label": "语言",
        "enable_ai_label": "启用 AI 解释",
        "how_it_works_title": "工作原理",
        "analyse_button": "分析合同",
        "tab_upload": "上传 PDF",
        "tab_paste": "粘贴文本",
        "translation_unavailable_notice": "翻译暂不可用——显示英文原文。",
    },
}


def t(key: str, lang: str = _FALLBACK_LANG) -> str:
    """Translate `key` into `lang`, falling back to English when the language
    or the key isn't found — so a missing translation degrades to readable
    English instead of a blank string or a raw key name."""
    table = _STRINGS.get(lang) or _STRINGS[_FALLBACK_LANG]
    fallback_table = _STRINGS[_FALLBACK_LANG]
    return table.get(key) or fallback_table.get(key, key)
