"""Compatibility facade for modular Order Employee.

New code should import from app.modules.employees.order.service.
"""

from app.modules.employees.order.service import *  # noqa: F401,F403
from app.modules.employees.order.service import _next_number_fallback  # noqa: F401