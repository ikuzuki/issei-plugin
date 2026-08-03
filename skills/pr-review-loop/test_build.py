"""Tests for the pr-review-loop skill's build.py.

Every case here is a path that used to resolve to "this PR is already covered",
so the loop reported nothing to review and the PR silently dropped out of the
sweep - the one failure mode the loop cannot afford, since a skipped PR looks
identical to a clean one. Plus the verdict-map validation, where an unknown
verdict used to be rebucketed as awaiting-review with its reviewer and note
dropped.

build.py sits beside its SKILL.md rather than in an importable package, so it is
loaded by path. Run with `python -m pytest` from this directory.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

BUILD_PY = Path(__file__).parent / "build.py"

HEAD = "a" * 40
OLDER = "b" * 40


def _load_build():
    spec = importlib.util.spec_from_file_location("pr_review_loop_build", BUILD_PY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


build = _load_build()

MARKER = "<!-- pr-review-loop: reviewed-at={} -->"


def review(
    author="adele-curve",
    state="COMMENTED",
    body="Some real review prose.",
    oid=HEAD,
    submitted="2026-08-03T11:00:00Z",
):
    """A review entry shaped like `gh pr view --json reviews` returns."""
    return {
        "author": {"login": author},
        "state": state,
        "body": body,
        "commit": None if oid is None else {"oid": oid},
        "submittedAt": submitted,
    }


def pr(reviews, author="Issei-curve", head=HEAD):
    return {"author": {"login": author}, "headRefOid": head, "reviews": reviews}


class TestSameCommit:
    """A prefix match treated an empty oid as matching every head."""

    def test_equal_shas_match(self):
        assert build.same_commit(HEAD, HEAD)

    def test_different_shas_do_not_match(self):
        assert not build.same_commit(HEAD, OLDER)

    @pytest.mark.parametrize("head,oid", [("", HEAD), (HEAD, ""), ("", "")])
    def test_missing_side_never_matches(self, head, oid):
        assert not build.same_commit(head, oid)


class TestNeedsReview:
    def test_no_reviews_needs_review(self):
        assert build.needs_review(pr([]))

    def test_current_human_review_is_coverage(self):
        assert not build.needs_review(pr([review()]))

    def test_review_on_an_older_commit_needs_review(self):
        assert build.needs_review(pr([review(oid=OLDER)]))

    def test_review_with_null_commit_needs_review(self):
        """`commit: null` is what a force-push leaves behind, which is exactly
        when the PR most needs looking at again. It used to satisfy the prefix
        match and drop the PR from every later sweep."""
        assert build.needs_review(pr([review(oid=None)]))

    def test_authors_own_bare_self_review_is_not_coverage(self):
        assert build.needs_review(pr([review(author="Issei-curve", body="note to self")]))

    def test_loop_marker_review_at_head_is_coverage_even_from_the_author(self):
        marker = review(author="Issei-curve", body="**Looks good**\n" + MARKER.format(HEAD))
        assert not build.needs_review(pr([marker]))


class TestPendingReviews:
    """GitHub sends `submittedAt: null` on a PENDING review. `.get(k, "")`
    returns None for it - the key is present - so every comparison raised and
    killed the whole sweep rather than one repo."""

    def test_pending_review_does_not_raise(self):
        prd = pr([review(state="PENDING", submitted=None), review(oid=OLDER)])
        assert build.needs_review(prd) is True

    def test_pending_review_is_not_coverage(self):
        assert build.needs_review(pr([review(state="PENDING", submitted=None)]))

    def test_marker_in_a_pending_review_does_not_suppress_the_pr(self):
        """An unsubmitted draft carrying the marker would otherwise suppress the
        PR indefinitely."""
        marker = review(
            author="Issei-curve",
            state="PENDING",
            submitted=None,
            body="**Looks good**\n" + MARKER.format(HEAD),
        )
        assert build.needs_review(pr([marker]))
        assert build.loop_marker_sha(pr([marker])) is None

    def test_latest_review_picks_the_newest_of_several(self):
        old = review(body="older", submitted="2026-08-01T09:00:00Z")
        new = review(body="newer", submitted="2026-08-03T09:00:00Z")
        assert build.latest_review(pr([old, new]))["body"] == "newer"


class TestIsRealReview:
    def test_prose_review_counts(self):
        assert build.is_real_review(review())

    def test_empty_bodied_comment_does_not_count(self):
        """GitHub records a bare inline comment as a review with an empty body.
        Counted as coverage, a handful of them silently suppressed the PR."""
        assert not build.is_real_review(review(body=""))
        assert build.needs_review(pr([review(body=""), review(body="   ")]))

    def test_approval_counts_without_a_body(self):
        assert build.is_real_review(review(state="APPROVED", body=""))

    def test_dismissed_review_does_not_count(self):
        assert not build.is_real_review(review(state="DISMISSED"))
        assert build.needs_review(pr([review(state="DISMISSED")]))


class TestHumanReviewer:
    def test_current_human_review_is_attributed(self):
        assert build.human_reviewer(pr([review()])) == ("adele-curve", False)

    def test_changes_requested_is_flagged(self):
        assert build.human_reviewer(pr([review(state="CHANGES_REQUESTED")])) == (
            "adele-curve",
            True,
        )

    def test_stale_human_review_is_not_current(self):
        assert build.human_reviewer(pr([review(oid=OLDER)])) == (None, False)

    def test_null_commit_human_review_is_not_current(self):
        """The prefix match flipped the other way here: a stale review read as
        current, so the digest showed the PR as sitting with the author."""
        assert build.human_reviewer(pr([review(oid=None)])) == (None, False)

    def test_empty_bodied_comment_is_not_a_human_review(self):
        assert build.human_reviewer(pr([review(body="")])) == (None, False)

    def test_loop_marker_review_is_not_a_human_review(self):
        marker = review(author="adele-curve", body="**Looks good**\n" + MARKER.format(HEAD))
        assert build.human_reviewer(pr([marker])) == (None, False)


class TestValidateVerdicts:
    @pytest.mark.parametrize("verdict", build.VERDICTS)
    def test_each_valid_verdict_passes(self, verdict):
        build.validate_verdicts({"repo#1": {"verdict": verdict, "reviewer": "@claude"}})

    def test_entry_without_a_verdict_passes(self):
        build.validate_verdicts({"repo#1": {"reviewer": "@adele-curve"}})

    def test_empty_map_passes(self):
        build.validate_verdicts({})

    @pytest.mark.parametrize("verdict", ["Needs changes", "LGTM", "needs judgment", ""])
    def test_unknown_verdict_raises(self, verdict):
        with pytest.raises(ValueError, match="unknown verdict"):
            build.validate_verdicts({"repo#1": {"verdict": verdict, "reviewer": "@claude"}})

    def test_the_error_names_the_offending_pr_and_value(self):
        with pytest.raises(ValueError, match=r"repo#7.*Needs changes"):
            build.validate_verdicts(
                {
                    "repo#1": {"verdict": "Looks good"},
                    "repo#7": {"verdict": "Needs changes"},
                }
            )
