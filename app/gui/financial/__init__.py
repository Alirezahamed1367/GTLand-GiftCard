"""
ماژول‌های رابط کاربری مالی - سیستم جدید
"""

# فقط ماژول‌های ضروری Import می‌شوند
from .role_manager_dialog import RoleManagerDialog
from .smart_import_wizard import SmartImportWizard
from .conflict_resolution_dialog import ConflictResolutionDialog
from .report_builder_widget import ReportBuilderWidget

__all__ = [
    'RoleManagerDialog',
    'SmartImportWizard',
    'ConflictResolutionDialog',
    'ReportBuilderWidget'
]
