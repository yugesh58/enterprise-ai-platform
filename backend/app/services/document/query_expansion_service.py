import re


class QueryExpansionService:
    """
    Expands natural-language queries into a small set of
    retrieval-oriented concepts.

    The goal is not to rewrite the user's question completely.
    Instead, we preserve the original query and add useful
    domain-specific retrieval terms.
    """

    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "does",
        "for",
        "from",
        "have",
        "has",
        "how",
        "i",
        "in",
        "is",
        "me",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "which",
        "who",
        "with",
        "you",
        "your",
    }

    CONCEPT_MAP = {
        "power automate": [
            "Power Automate",
            "automation",
            "workflow automation",
        ],
        "copilot studio": [
            "Copilot Studio",
            "automation",
        ],
        "power automate desktop": [
            "Power Automate Desktop",
            "automation",
            "workflow automation",
        ],
        "machine learning": [
            "Machine Learning",
            "ML",
        ],
        "generative ai": [
            "Generative AI",
            "AI",
        ],
        "agentic ai": [
            "Agentic AI",
            "AI",
        ],
        "retrieval augmented generation": [
            "Retrieval-Augmented Generation",
            "RAG",
        ],
        "retrieval-augmented generation": [
            "Retrieval-Augmented Generation",
            "RAG",
        ],
        "vector database": [
            "Vector Databases",
            "FAISS",
        ],
        "vector databases": [
            "Vector Databases",
            "FAISS",
        ],
        "azure openai": [
            "Azure OpenAI",
            "OpenAI",
        ],
        "power platform": [
            "Power Platform",
            "automation",
        ],
    }

    def __init__(
        self,
        max_expansions: int = 5,
        max_keyword_terms: int = 2,
    ) -> None:
        if max_expansions < 0:
            raise ValueError("max_expansions cannot be negative")
        if max_keyword_terms < 0:
            raise ValueError("max_keyword_terms cannot be negative")

        self.max_expansions = max_expansions
        self.max_keyword_terms = max_keyword_terms

    def expand(self, query: str) -> list[str]:
        """
        Return an ordered list of retrieval queries.

        The original query is always preserved.
        Domain concepts are added before generic individual words.
        """

        query = query.strip()

        if not query:
            return []

        query_lower = query.lower()

        expansions: list[str] = []

        # ---------------------------------------------------------
        # 1. Domain-specific concepts
        # ---------------------------------------------------------

        for phrase, concepts in self.CONCEPT_MAP.items():
            if phrase in query_lower:
                expansions.extend(concepts)

        # ---------------------------------------------------------
        # 2. Question intent
        # ---------------------------------------------------------

        if any(
            term in query_lower
            for term in (
                "skill",
                "skills",
                "know",
                "knowledge",
                "technology",
                "technologies",
                "expertise",
            )
        ):
            expansions.extend(
                [
                    "skills",
                    "technologies",
                    "expertise",
                ]
            )

        if any(
            term in query_lower
            for term in (
                "project",
                "projects",
                "built",
                "developed",
                "worked on",
            )
        ):
            expansions.extend(
                [
                    "projects",
                    "developed",
                    "built",
                ]
            )

        if any(
            term in query_lower
            for term in (
                "database",
                "databases",
                "data store",
                "data stores",
            )
        ):
            expansions.extend(
                [
                    "databases",
                    "PostgreSQL",
                    "SQLite",
                ]
            )

        if any(
            term in query_lower
            for term in (
                "experience",
                "worked",
                "work",
            )
        ):
            expansions.extend(
                [
                    "experience",
                    "professional experience",
                ]
            )

        # ---------------------------------------------------------
        # 3. Meaningful individual words
        # ---------------------------------------------------------

        words = re.findall(
            r"[A-Za-z0-9+#.-]+",
            query,
        )

        meaningful_words = [
            word.lower()
            for word in words
            if word.lower() not in self.STOP_WORDS
            and len(word) >= 3
        ]

        expansions.extend(meaningful_words[: self.max_keyword_terms])

        # ---------------------------------------------------------
        # 4. Original query
        # ---------------------------------------------------------

        expansions.append(query)

        # ---------------------------------------------------------
        # 5. Remove duplicates while preserving order
        # ---------------------------------------------------------

        unique_expansions = list(
            dict.fromkeys(
                item.strip()
                for item in expansions
                if item.strip()
            )
        )

        additional_expansions = [
            item
            for item in unique_expansions
            if item.casefold() != query.casefold()
        ]

        return additional_expansions[: self.max_expansions] + [query]
