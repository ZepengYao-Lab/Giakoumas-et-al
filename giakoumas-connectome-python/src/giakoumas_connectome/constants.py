"""Shared constants for the standalone connectome project."""

SEZ_NEUROPILS = frozenset({"GNG", "PRW", "SAD", "FLA_L", "FLA_R", "CAN"})
SEZ_NEUROPILS_COLLAPSED = frozenset({"GNG", "PRW", "SAD", "FLA", "CAN"})

PRIMARY_NTS = ("ACH", "GABA", "GLUT")
SECONDARY_NTS = ("DA", "SER")

SUPERCLASS_ORDER = (
    "sensory",
    "ascending",
    "central",
    "descending",
    "motor",
    "endocrine",
    "optic",
    "visual_projection",
    "visual_centrifugal",
)

DIRECT_INPUT_SUPERCLASS_ORDER = SUPERCLASS_ORDER + ("unclassified",)

DIRECT_INPUT_NERVE_ORDER = (
    "AN",
    "CV",
    "MxLbN",
    "OCN",
    "PhN",
    "aPhN",
    "NCC",
    "ON",
    "no_nerve",
)

HOP_ORDER = ("1", "2", "3", ">3")

HOP_COLOR_MAP = {
    "1": "#CC3311",
    "2": "#33BBEE",
    "3": "#009E73",
    ">3": "gray",
}
