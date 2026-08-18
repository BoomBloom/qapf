import logging
import re
from datetime import datetime, timedelta, timezone
from itertools import islice

import arxiv
from github import Github, GithubException

from .schemas import CodeRepository, ExtractedAlphaResearch

logger = logging.getLogger(__name__)

# arXiv categories covering quantitative finance, statistical learning, and AI.
QUANT_CATEGORIES = "cat:q-fin.* OR cat:stat.ML OR cat:cs.AI"

GITHUB_URL_RE = re.compile(r"https?://github\.com/([\w\-.]+)/([\w\-.]+)")


class ResearchIngestionPipeline:
    """Ingests recent quant/stats/ML papers from arXiv and cross-references
    open-source implementations on GitHub, producing structured records for
    downstream agents (stats, alpha mining, software engineering)."""

    def __init__(self, github_token: str | None = None):
        self.arxiv_client = arxiv.Client(page_size=100, delay_seconds=3.0, num_retries=3)
        self.github_client = Github(github_token) if github_token else Github()

    def fetch_recent_quant_papers(
        self, topics: list[str], days_back: int = 7, max_results: int = 15
    ) -> list[arxiv.Result]:
        topic_query = " OR ".join(f'all:"{t}"' for t in topics)
        full_query = f"({QUANT_CATEGORIES}) AND ({topic_query})"
        logger.info("Querying arXiv: %s", full_query)

        search = arxiv.Search(
            query=full_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        papers = [r for r in self.arxiv_client.results(search) if r.published >= cutoff_date]
        logger.info("Found %d papers within the last %d days", len(papers), days_back)
        return papers

    def _extract_latex_equations(self, abstract: str) -> list[str]:
        inline_math = re.findall(r"\$(.*?)\$", abstract)
        block_math = re.findall(r"\$\$(.*?)\$\$", abstract, re.DOTALL)
        candidates = set(inline_math + block_math)
        # Abstracts often wrap plain numbers in $...$ (e.g. sampling rates
        # like "$0.1$s"); those aren't math concepts. Keep only expressions
        # with a variable/operator/LaTeX command, not bare numerals.
        return [c for c in candidates if not re.fullmatch(r"[\d.\s+-]+", c)]

    def _repos_linked_in_abstract(self, abstract: str) -> list[CodeRepository]:
        """Papers often name their own repo directly in the abstract — a much
        stronger signal than a fuzzy title search, and one a title search can
        miss entirely."""
        repositories = []
        for owner, name in GITHUB_URL_RE.findall(abstract):
            full_name = f"{owner}/{name.rstrip('.')}"
            try:
                repo = self.github_client.get_repo(full_name)
                repositories.append(
                    CodeRepository(
                        name=repo.full_name,
                        url=repo.html_url,
                        stars=repo.stargazers_count,
                        description=repo.description,
                        primary_language=repo.language,
                    )
                )
            except GithubException as e:
                logger.warning("Could not fetch linked repo %s: %s", full_name, e)
        return repositories

    def search_github_implementations(
        self, paper_title: str, arxiv_id: str, abstract: str = ""
    ) -> list[CodeRepository]:
        repositories = self._repos_linked_in_abstract(abstract)
        linked_names = {r.name for r in repositories}

        clean_title = re.sub(r"[^a-zA-Z0-9\s]", "", paper_title)
        short_title = " ".join(clean_title.split()[:5])
        query = f'"{arxiv_id}" OR "{short_title}"'
        logger.info("Searching GitHub for implementation: %s", query)

        try:
            results = self.github_client.search_repositories(query=query, sort="stars", order="desc")
            # PyGithub's PaginatedList raises IndexError when sliced past the
            # actual result count instead of returning fewer items; islice
            # doesn't have that problem.
            for repo in islice(results, 3):
                if repo.full_name in linked_names:
                    continue
                repositories.append(
                    CodeRepository(
                        name=repo.full_name,
                        url=repo.html_url,
                        stars=repo.stargazers_count,
                        description=repo.description,
                        primary_language=repo.language,
                    )
                )
        except GithubException as e:
            logger.warning("GitHub search failed for %s: %s", arxiv_id, e)

        return repositories

    def run(
        self, topics: list[str], max_results: int = 5, days_back: int = 7
    ) -> list[ExtractedAlphaResearch]:
        raw_papers = self.fetch_recent_quant_papers(topics, days_back=days_back, max_results=max_results)
        structured_output = []

        for paper in raw_papers:
            math_expressions = self._extract_latex_equations(paper.summary)
            clean_arxiv_id = paper.entry_id.split("/")[-1].split("v")[0]
            github_repos = self.search_github_implementations(
                paper.title, clean_arxiv_id, abstract=paper.summary
            )

            structured_output.append(
                ExtractedAlphaResearch(
                    arxiv_id=clean_arxiv_id,
                    title=paper.title,
                    published=paper.published.strftime("%Y-%m-%d"),
                    authors=[author.name for author in paper.authors],
                    abs_url=paper.entry_id,
                    pdf_url=paper.pdf_url,
                    categories=paper.categories,
                    summary=paper.summary.replace("\n", " "),
                    extracted_math_concepts=math_expressions,
                    linked_repositories=github_repos,
                )
            )

        return structured_output
