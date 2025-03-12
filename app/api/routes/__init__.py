from .auth import router as auth_router
from .users import router as users_router
from .receipts import router as receipts_router
from .categories import router as categories_router
from .imap_settings import router as imap_settings_router
from .analytics import router as analytics_router


import sys
print("Python path:", sys.path)
print("Trying to import budgets module")
from .budgets import router as budget_router