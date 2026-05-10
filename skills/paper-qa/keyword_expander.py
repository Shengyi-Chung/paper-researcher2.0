from typing import List


KEYWORD_MAP = {

    # =====================================================
    # Efficiency
    # =====================================================

    "efficient": [
        "lightweight",
        "fast inference",
        "real-time",
        "low latency",
        "efficient",
        "compressed",
        "memory efficient"
    ],

    "lightweight": [
        "compact",
        "efficient",
        "mobile",
        "fast inference"
    ],

    # =====================================================
    # Robustness
    # =====================================================

    "robust": [
        "noise resistant",
        "stable",
        "generalizable",
        "uncertainty aware",
        "robustness"
    ],

    "generalization": [
        "cross-domain",
        "transfer",
        "domain adaptation",
        "generalizable"
    ],

    # =====================================================
    # Uncertainty
    # =====================================================

    "uncertainty": [
        "confidence estimation",
        "bayesian",
        "probabilistic",
        "uncertainty aware",
        "calibration"
    ],

    # =====================================================
    # Hierarchical
    # =====================================================

    "hierarchical": [
        "multi-scale",
        "coarse-to-fine",
        "temporal hierarchy",
        "hierarchical modeling"
    ],

    # =====================================================
    # Transformer
    # =====================================================

    "transformer": [
        "attention",
        "self-attention",
        "vision transformer",
        "ViT"
    ],

    # =====================================================
    # Segmentation
    # =====================================================

    "segmentation": [
        "temporal segmentation",
        "action segmentation",
        "sequence segmentation"
    ],

    # =====================================================
    # Novelty
    # =====================================================

    "novel": [
        "state-of-the-art",
        "new architecture",
        "innovative",
        "new paradigm"
    ]
}


def expand_keyword(keyword: str) -> List[str]:
    """
    Expand a keyword into related retrieval terms.
    """

    keyword = keyword.lower().strip()

    expanded = [keyword]

    if keyword in KEYWORD_MAP:
        expanded.extend(KEYWORD_MAP[keyword])

    return list(set(expanded))


def expand_keywords(keywords: List[str]) -> List[str]:
    """
    Expand multiple keywords.
    """

    expanded = []

    for keyword in keywords:
        expanded.extend(expand_keyword(keyword))

    return list(set(expanded))