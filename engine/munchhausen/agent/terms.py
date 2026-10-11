"""The term vocabulary (SPEC § 22.4, § 20.3; LANGUAGE.md § 4): seeding and in-process matching.

Pure functions over `Term` rows. The Atlas `$search` path (`store/repositories.AtlasTerms.extract`) and its
in-process fallback both end in `present_terms`, so the two agree on what a question presents.

**Seeding** reads the adapter's schema summary (collection and field names) and noun phrases mined from the
first `VOCAB_WARMUP` stream questions. It never reads the pack: `seed_terms` takes no pack argument, and a
test asserts no pack id, definition or transform parameter lands in `terms`.

**Matching** biases broad (§ 6.2 Do): every vocabulary phrase — a term or one of its aliases — that occurs
as a contiguous run of tokens is presented, including a shorter term inside a longer one ("customers"
inside "active customers"). A false match costs one `considered-not-applicable`; a miss is silent.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from munchhausen.domain.question import Question, SchemaSummary
from munchhausen.domain.registers import Term

_WORD = re.compile(r"[a-z][a-z0-9']*|\d[\d,.]*")

# Function words that end a noun phrase. Grammar, not a tunable.
STOPWORDS: frozenset[str] = frozenset({
    "a", "about", "above", "across", "after", "against", "all", "along", "also", "am", "among", "an", "and",
    "any", "are", "as", "at", "average", "be", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "compute", "could", "count", "did", "do", "does", "doing", "down", "during", "each", "either", "every",
    "few", "find", "for", "from", "get", "give", "had", "has", "have", "having", "he", "her", "here", "hers",
    "him", "his", "how", "how's", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "list", "many",
    "may", "me", "mean", "might", "more", "most", "much", "must", "my", "name", "names", "neither", "no", "nor",
    "not", "number", "of", "off", "on", "once", "only", "or", "other", "our", "out", "over", "own", "per",
    "report", "return", "same", "she", "should", "show", "so", "some", "such", "sum", "tell", "than", "that",
    "the", "their", "them", "then", "there", "these", "they", "this", "those", "through", "to", "too", "total",
    "under", "until", "up", "upon", "us", "very", "was", "we", "were", "what", "what's", "whats", "when", "where",
    "whether", "which", "while", "who", "whom", "whose", "why", "will", "with", "within", "without", "would",
    "you", "your",
})


def tokens(text: str) -> list[str]:
    return [_stem(t) for t in _WORD.findall(text.lower().replace("_", " "))]


def _stem(token: str) -> str:
    """Light plural folding so "customer" and "customers" present the same phrase."""
    token = token.strip("'").rstrip(".,")
    if len(token) > 3 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def present_terms(text: str, rows: Iterable[Term]) -> frozenset[str]:
    """The canonical terms whose phrase (the term or an alias) occurs in `text` as a token run."""
    toks = tokens(text)
    if not toks:
        return frozenset()
    joined = f" {' '.join(toks)} "
    out: set[str] = set()
    for row in rows:
        for phrase in (row.term, *row.aliases):
            pt = tokens(phrase)
            if pt and f" {' '.join(pt)} " in joined:
                out.add(row.term)
                break
    return frozenset(out)


def schema_terms(schema: SchemaSummary) -> list[str]:
    """Collection names and every segment of the dotted field paths as lower-case phrases
    (`tier_and_details.$key.tier` → "tier and details", "tier"). Map-key placeholders (`$key`) and
    underscore-led names (`_id`) are skipped. Names only: the types never enter the vocabulary."""
    out: list[str] = []
    for coll, fields in schema.collections.items():
        out.append(_phrase(coll))
        for path in fields:
            out += [_phrase(seg) for seg in path.split(".") if seg and not seg.startswith(("_", "$"))]
    return [t for t in dict.fromkeys(out) if t and len(t) > 1]


def noun_phrases(text: str, max_tokens: int) -> set[str]:
    """Maximal runs of content words (no stopwords, no numbers), and their sub-runs up to `max_tokens`."""
    runs: list[list[str]] = [[]]
    for w in re.findall(r"[A-Za-z][A-Za-z'-]*|\d[\d,.]*|[^\sA-Za-z\d]", text):
        lw = w.lower().strip("'")
        # numbers, punctuation, stopwords and all-caps codes (ticker-like parameter values) end a phrase
        if not lw[:1].isalpha() or lw in STOPWORDS or (w.isupper() and len(w) > 1):
            runs.append([])
            continue
        runs[-1].append(lw)
    out: set[str] = set()
    for run in runs:
        for n in range(1, max_tokens + 1):
            for i in range(len(run) - n + 1):
                out.add(" ".join(run[i:i + n]))
    return out


def seed_terms(schema: SchemaSummary, questions: Sequence[Question], *, min_questions: int,
               max_tokens: int) -> list[Term]:
    """The seed vocabulary: schema terms at index 0, then each noun phrase presented by ≥ `min_questions`
    of the warmup questions, admitted at the index of the question where it reached that count."""
    rows = {t: Term(term=t, source="schema", admitted_at_idx=0) for t in schema_terms(schema)}
    seen: dict[str, int] = {}
    for idx, q in enumerate(questions):
        for p in noun_phrases(q.text, max_tokens):
            key = " ".join(tokens(p))
            seen[key] = seen.get(key, 0) + 1
            if seen[key] == min_questions and not any(" ".join(tokens(t)) == key for t in rows):
                rows[p] = Term(term=p, source="question", admitted_at_idx=idx)
    return list(rows.values())


def _phrase(name: str) -> str:
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    return " ".join(spaced.replace("_", " ").replace(".", " ").lower().split())

