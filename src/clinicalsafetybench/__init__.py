"""
ClinicalSafetyBench
===================
A lightweight, open-source AI safety evaluation suite for clinical AI tools
deployed in sub-Saharan African primary healthcare settings.

Grounded in Kenya, Rwanda, and Nigeria national treatment guidelines.
"""

__version__ = "0.1.0"
__author__  = "ClinicalSafetyBench Contributors"
__license__ = "MIT"

from clinicalsafetybench.benchmark  import BenchmarkLoader
from clinicalsafetybench.evaluator  import Evaluator
from clinicalsafetybench.scoring.rubric import Rubric

__all__ = ["BenchmarkLoader", "Evaluator", "Rubric"]
