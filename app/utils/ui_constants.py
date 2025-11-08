"""
ثوابت UI برای یکپارچگی ظاهری برنامه
"""

# ==================== RESPONSIVE RATIOS ====================
# نسبت‌های صفحه نمایش
DIALOG_WIDTH_RATIO = 0.75      # 75% عرض صفحه
DIALOG_HEIGHT_RATIO = 0.80     # 80% ارتفاع صفحه
SMALL_DIALOG_WIDTH_RATIO = 0.5 # 50% عرض (برای دیالوگ‌های کوچک)
SMALL_DIALOG_HEIGHT_RATIO = 0.6 # 60% ارتفاع


# ==================== FONT SIZES ====================
# اندازه فونت‌ها (بر حسب pt)
FONT_SIZE_TITLE = 18           # عنوان اصلی صفحات
FONT_SIZE_SECTION = 14         # عنوان بخش‌ها
FONT_SIZE_BUTTON = 11          # متن دکمه‌ها
FONT_SIZE_LABEL = 10           # برچسب‌های معمولی
FONT_SIZE_INPUT = 10           # فیلدهای ورودی
FONT_SIZE_SMALL = 9            # متن‌های کوچک (راهنما، توضیحات)


# ==================== BUTTON HEIGHTS ====================
# ارتفاع دکمه‌ها (بر حسار پیکسل)
BUTTON_HEIGHT_LARGE = 50       # دکمه‌های بزرگ (صفحه اصلی)
BUTTON_HEIGHT_MEDIUM = 40      # دکمه‌های متوسط (دیالوگ‌ها)
BUTTON_HEIGHT_SMALL = 32       # دکمه‌های کوچک (جداول)


# ==================== WIDGET HEIGHTS ====================
# ارتفاع ویجت‌ها
INPUT_HEIGHT = 35              # فیلدهای ورودی
TEXTAREA_HEIGHT = 80           # جعبه متن چندخطی
TABLE_MIN_HEIGHT_RATIO = 0.3   # 30% ارتفاع برای جداول
PREVIEW_TABLE_HEIGHT = 150     # جدول پیش‌نمایش


# ==================== SPACINGS ====================
# فاصله‌گذاری
SPACING_LARGE = 20             # فاصله بزرگ بین بخش‌ها
SPACING_MEDIUM = 10            # فاصله متوسط
SPACING_SMALL = 5              # فاصله کوچک

MARGIN_LARGE = 20              # حاشیه بزرگ
MARGIN_MEDIUM = 15             # حاشیه متوسط
MARGIN_SMALL = 10              # حاشیه کوچک


# ==================== COLORS ====================
# پالت رنگی برنامه
COLOR_PRIMARY = "#2196F3"      # آبی اصلی
COLOR_SUCCESS = "#4CAF50"      # سبز موفقیت
COLOR_WARNING = "#FF9800"      # نارنجی هشدار
COLOR_DANGER = "#F44336"       # قرمز خطر
COLOR_INFO = "#9C27B0"         # بنفش اطلاعات

# رنگ‌های روشن (Hover)
COLOR_PRIMARY_LIGHT = "#64B5F6"
COLOR_SUCCESS_LIGHT = "#81C784"
COLOR_WARNING_LIGHT = "#FFB74D"
COLOR_DANGER_LIGHT = "#E57373"
COLOR_INFO_LIGHT = "#BA68C8"

# رنگ‌های تیره (Pressed)
COLOR_PRIMARY_DARK = "#1976D2"
COLOR_SUCCESS_DARK = "#388E3C"
COLOR_WARNING_DARK = "#F57C00"
COLOR_DANGER_DARK = "#D32F2F"
COLOR_INFO_DARK = "#7B1FA2"

# رنگ‌های خنثی
COLOR_BACKGROUND = "#FAFAFA"
COLOR_SURFACE = "#FFFFFF"
COLOR_BORDER = "#E0E0E0"
COLOR_TEXT = "#333333"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_TEXT_DISABLED = "#999999"


# ==================== BORDER RADIUS ====================
RADIUS_SMALL = 4               # گوشه‌های کوچک
RADIUS_MEDIUM = 6              # گوشه‌های متوسط
RADIUS_LARGE = 8               # گوشه‌های بزرگ


# ==================== HELPER FUNCTIONS ====================
def get_button_style(color: str, font_size: int = FONT_SIZE_BUTTON, height: int = BUTTON_HEIGHT_MEDIUM) -> str:
    """
    تولید استایل یکپارچه برای دکمه‌ها
    
    Args:
        color: رنگ اصلی دکمه
        font_size: اندازه فونت
        height: ارتفاع دکمه
        
    Returns:
        رشته CSS برای دکمه
    """
    # تشخیص رنگ روشن و تیره
    color_light = COLOR_LIGHT_MAP.get(color, color)
    color_dark = COLOR_DARK_MAP.get(color, color)
    
    return f"""
        QPushButton {{
            background: {color};
            color: white;
            border: none;
            border-radius: {RADIUS_MEDIUM}px;
            padding: 10px 20px;
            font-size: {font_size}pt;
            font-weight: bold;
            min-height: {height}px;
        }}
        QPushButton:hover {{
            background: {color_light};
        }}
        QPushButton:pressed {{
            background: {color_dark};
        }}
        QPushButton:disabled {{
            background: {COLOR_BORDER};
            color: {COLOR_TEXT_DISABLED};
        }}
    """


def get_input_style() -> str:
    """استایل یکپارچه برای فیلدهای ورودی"""
    return f"""
        QLineEdit, QTextEdit, QSpinBox, QComboBox {{
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_SMALL}px;
            padding: 8px;
            font-size: {FONT_SIZE_INPUT}pt;
            background: {COLOR_SURFACE};
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 2px solid {COLOR_PRIMARY};
        }}
    """


def get_label_style(size: str = "normal") -> str:
    """
    استایل یکپارچه برای برچسب‌ها
    
    Args:
        size: اندازه - "title", "section", "normal", "small"
    """
    sizes = {
        "title": FONT_SIZE_TITLE,
        "section": FONT_SIZE_SECTION,
        "normal": FONT_SIZE_LABEL,
        "small": FONT_SIZE_SMALL
    }
    font_size = sizes.get(size, FONT_SIZE_LABEL)
    
    return f"""
        QLabel {{
            font-size: {font_size}pt;
            color: {COLOR_TEXT};
        }}
    """


def get_groupbox_style() -> str:
    """استایل یکپارچه برای GroupBox ها"""
    return f"""
        QGroupBox {{
            border: 2px solid {COLOR_BORDER};
            border-radius: {RADIUS_MEDIUM}px;
            margin-top: 15px;
            padding: 15px;
            font-size: {FONT_SIZE_SECTION}pt;
            font-weight: bold;
            background: {COLOR_SURFACE};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top right;
            padding: 5px 10px;
            background: {COLOR_SURFACE};
        }}
    """


def get_table_style() -> str:
    """استایل یکپارچه برای جداول"""
    return f"""
        QTableWidget {{
            border: 1px solid {COLOR_BORDER};
            border-radius: {RADIUS_SMALL}px;
            gridline-color: {COLOR_BORDER};
            font-size: {FONT_SIZE_LABEL}pt;
            background: {COLOR_SURFACE};
        }}
        QTableWidget::item {{
            padding: 8px;
        }}
        QTableWidget::item:selected {{
            background: {COLOR_PRIMARY_LIGHT};
            color: white;
        }}
        QHeaderView::section {{
            background: {COLOR_BACKGROUND};
            padding: 8px;
            border: 1px solid {COLOR_BORDER};
            font-weight: bold;
            font-size: {FONT_SIZE_LABEL}pt;
        }}
    """


# نقشه رنگ‌ها برای تبدیل
COLOR_LIGHT_MAP = {
    COLOR_PRIMARY: COLOR_PRIMARY_LIGHT,
    COLOR_SUCCESS: COLOR_SUCCESS_LIGHT,
    COLOR_WARNING: COLOR_WARNING_LIGHT,
    COLOR_DANGER: COLOR_DANGER_LIGHT,
    COLOR_INFO: COLOR_INFO_LIGHT,
}

COLOR_DARK_MAP = {
    COLOR_PRIMARY: COLOR_PRIMARY_DARK,
    COLOR_SUCCESS: COLOR_SUCCESS_DARK,
    COLOR_WARNING: COLOR_WARNING_DARK,
    COLOR_DANGER: COLOR_DANGER_DARK,
    COLOR_INFO: COLOR_INFO_DARK,
}


# ==================== RESPONSIVE HELPERS ====================
def get_responsive_dialog_size(screen_geometry, ratio_type: str = "normal"):
    """
    محاسبه سایز Responsive برای دیالوگ‌ها
    
    Args:
        screen_geometry: geometry صفحه نمایش
        ratio_type: "normal" یا "small"
        
    Returns:
        (width, height) بر حسب پیکسل
    """
    if ratio_type == "small":
        width_ratio = SMALL_DIALOG_WIDTH_RATIO
        height_ratio = SMALL_DIALOG_HEIGHT_RATIO
    else:
        width_ratio = DIALOG_WIDTH_RATIO
        height_ratio = DIALOG_HEIGHT_RATIO
    
    width = int(screen_geometry.width() * width_ratio)
    height = int(screen_geometry.height() * height_ratio)
    
    return width, height


def get_responsive_table_height(screen_geometry):
    """محاسبه ارتفاع Responsive برای جداول"""
    min_height = 250  # حداقل ارتفاع
    dynamic_height = int(screen_geometry.height() * TABLE_MIN_HEIGHT_RATIO)
    return max(min_height, dynamic_height)
