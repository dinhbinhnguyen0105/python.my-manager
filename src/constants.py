import os

PATH_RE_DB = os.path.join("src", "data", "real_estate.db")
RE_CONNECTION = "re_connection"
PATH_USER_DB = os.path.join("src", "data", "user.db")
USER_CONNECTION = "user_connection"

TABLE_RE = "table_re"
TABLE_USER = "table_user"

TABLE_RE_SETTINGS_STATUSES = "table_re_settings_statuses"
TABLE_RE_SETTINGS_PROVINCES = "table_re_settings_provinces"
TABLE_RE_SETTINGS_DISTRICTS = "table_re_settings_districts"
TABLE_RE_SETTINGS_WARDS = "table_re_settings_wards"
TABLE_RE_SETTINGS_OPTIONS = "table_re_settings_options"
TABLE_RE_SETTINGS_CATEGORIES = "table_re_settings_categories"
TABLE_RE_SETTINGS_BUILDING_LINES = "table_re_settings_building_lines"
TABLE_RE_SETTINGS_FURNITURES = "table_re_settings_furnitures"
TABLE_RE_SETTINGS_LEGALS = "table_re_settings_legals"
TABLE_RE_SETTINGS_IMG_DIRS = "table_re_settings_image_directories"

TABLE_RE_SETTINGS_TITLE = "table_re_settings_title"
TABLE_RE_SETTINGS_DESCRIPTION = "table_re_settings_description"

TABLE_USER_SETTINGS_UDD = "table_user_settings_udd"
TABLE_USER_SETTINGS_PROXY = "table_user_settings_proxy"

ICONS = [
    "🌼",
    "🌸",
    "🌺",
    "🏵️",
    "🌻",
    "🌷",
    "🌹",
    "🥀",
    "💐",
    "🌾",
    "🎋",
    "☘",
    "🍀",
    "🍃",
    "🍂",
    "🍁",
    "🌱",
    "🌿",
    "🎍",
    "🌵",
    "🌴",
    "🌳",
    "🎄",
    "🍄",
    "🌎",
    "🌍",
    "🌏",
    "🌜",
    "🌛",
    "🌕",
    "🌖",
    "🌗",
    "🌘",
    "🌑",
    "🌒",
    "🌓",
    "🌔",
    "🌚",
    "🌝",
    "🌙",
    "💫",
    "⭐",
    "🌟",
    "✨",
    "⚡",
    "🔥",
    "💥",
    "☄️",
    "🌞",
    "☀️",
    "🌤️",
    "⛅",
    "🌥️",
    "🌦️",
    "☁️",
    "🌧️",
    "⛈️",
    "🌩️",
    "🌨️",
    "🌈",
    "💧",
    "💦",
    "☂️",
    "☔",
    "🌊",
    "🌫",
    "🌪",
    "💨",
    "❄",
    "🌬",
    "⛄",
    "☃️",
    "♥️",
    "❤️",
    "💛",
    "💚",
    "💙",
    "💜",
    "🖤",
    "💖",
    "💝",
    "💔",
    "❣️",
    "💕",
    "💞",
    "💓",
    "💗",
    "💘",
    "💟",
    "💌",
    "💋",
    "👄",
    "💄",
    "💍",
    "📿",
    "🎁",
    "👙",
    "👗",
    "👚",
    "👕",
    "👘",
    "️🎽",
    "👘",
    "👖",
    "👠",
    "👡",
    "👢",
    "👟",
    "👞",
    "👒",
    "🎩",
    "🎓",
    "👑",
    "⛑️",
    "👓",
    "🕶️",
    "🌂",
    "👛",
    "👝",
    "👜",
    "💼",
    "🎒",
    "🛍️",
    "️🛒",
    "️🎭",
    "️🎦",
    "️🎨",
    "️🤹",
    "️🎊",
    "️🎉",
    "️🎈",
    "️🎧",
    "️🎷",
    "️🎺",
    "️🎸",
    "️🎻",
    "️🥁",
    "️🎹",
    "️🎤",
    "️🎵",
    "️🎶",
    "️🎼",
    "️⚽",
    "️🏀",
    "️🏈",
    "️⚾",
    "️🏐",
    "️🏉",
    "️🎱",
    "️🎾",
    "️🏸",
    "️🏓",
    "️🏏",
    "️🏑",
    "️🏒",
    "️🥅",
    "️⛸️",
    "️🎿",
    "️🥊",
    "️🥋",
    "️⛳",
    "️🎳",
    "️🏹",
    "️🎣",
    "️🎯",
    "🚵",
    "️🎖️",
    "️🏅",
    "️🥇",
    "️🥈",
    "️🥉",
    "️🏆",
]
RE_SETTING_STATUSES = [
    {"label_vi": "sẵn có", "label_en": "available", "value": "available"},
    {"label_vi": "không sẵn có", "label_en": "unavailable", "value": "unavailable"},
    {"label_vi": "đã ngừng", "label_en": "discontinued", "value": "discontinued"},
    {"label_vi": "sắp có", "label_en": "coming soon", "value": "coming_soon"},
]
RE_SETTING_PROVINCES = [
    {"label_vi": "lâm đồng", "label_en": "lam dong", "value": "lam_dong"},
]
RE_SETTING_DISTRICTS = [
    {"label_vi": "đà lạt", "label_en": "da lat", "value": "da_lat"},
]
RE_SETTING_WARDS = [
    {"label_vi": "phường 1", "label_en": "ward 1", "value": "1"},
    {"label_vi": "phường 2", "label_en": "ward 2", "value": "2"},
    {"label_vi": "phường 3", "label_en": "ward 3", "value": "3"},
    {"label_vi": "phường 4", "label_en": "ward 4", "value": "4"},
    {"label_vi": "phường 5", "label_en": "ward 5", "value": "5"},
    {"label_vi": "phường 6", "label_en": "ward 6", "value": "6"},
    {"label_vi": "phường 7", "label_en": "ward 7", "value": "7"},
    {"label_vi": "phường 8", "label_en": "ward 8", "value": "8"},
    {"label_vi": "phường 9", "label_en": "ward 9", "value": "9"},
    {"label_vi": "phường 10", "label_en": "ward 10", "value": "10"},
    {"label_vi": "phường 11", "label_en": "ward 11", "value": "11"},
    {"label_vi": "phường 12", "label_en": "ward 12", "value": "12"},
    {
        "label_vi": "xã trạm hành",
        "label_en": "ward tram hanh",
        "value": "tram_hanh",
    },
    {"label_vi": "xã tà nung", "label_en": "ward ta nung", "value": "ta_nung"},
    {
        "label_vi": "xã xuân trường",
        "label_en": "ward xuan truong",
        "value": "xuan_truong",
    },
    {"label_vi": "xã xuân thọ", "label_en": "ward xuan tho", "value": "xuan_tho"},
]
RE_SETTING_OPTIONS = [
    {"label_vi": "bán", "label_en": "sell", "value": "sell"},
    {"label_vi": "cho thuê", "label_en": "rent", "value": "rent"},
    {"label_vi": "sang nhượng", "label_en": "assignment", "value": "assignment"},
]
RE_SETTING_CATEGORIES = [
    {"label_vi": "nhà phố", "label_en": "private house", "value": "private_house"},
    {"label_vi": "nhà mặt tiền", "label_en": "shop house", "value": "shop_house"},
    {"label_vi": "biệt thự", "label_en": "villa", "value": "villa"},
    {"label_vi": "đất nền", "label_en": "land", "value": "land"},
    {"label_vi": "căn hộ/ chung cư", "label_en": "apartment", "value": "apartment"},
    {"label_vi": "homestay", "label_en": "homestay", "value": "homestay"},
    {"label_vi": "khách sạn", "label_en": "hotel", "value": "hotel"},
    {"label_vi": "kho/bãi", "label_en": "workshop", "value": "workshop"},
    {"label_vi": "MBKD", "label_en": "retail space", "value": "retail_space"},
    {
        "label_vi": "coffee house",
        "label_en": "coffee house",
        "value": "coffee_house",
    },
    {"label_vi": "nhà hàng", "label_en": "restaurant", "value": "restaurant"},
]
RE_SETTING_BUILDING_LINES = [
    {"label_vi": "đường xe hơi", "label_en": "big road", "value": "big_road"},
    {"label_vi": "đường xe máy", "label_en": "small road", "value": "small_road"},
]
RE_SETTING_LEGALS = [
    {"label_vi": "giấy tờ tay", "label_en": "none", "value": "none"},
    {"label_vi": "sổ nông nghiệp chung", "label_en": "snnc", "value": "snnc"},
    {
        "label_vi": "sổ nông nghiệp phân quyền",
        "label_en": "snnpq",
        "value": "snnpq",
    },
    {"label_vi": "sổ nông nghiệp riêng", "label_en": "snnr", "value": "snnr"},
    {"label_vi": "sổ xây dựng chung", "label_en": "sxdc", "value": "sxdc"},
    {"label_vi": "sổ xây dựng phân quyền", "label_en": "sxdpq", "value": "sxdpq"},
    {"label_vi": "sổ xây dựng riêng", "label_en": "sxdr", "value": "sxdr"},
]
RE_SETTING_FURNITURES = [
    {"label_vi": "không nội thất", "label_en": "none", "value": "none"},
    {"label_vi": "nội thất cơ bản", "label_en": "basic", "value": "basic"},
    {"label_vi": "đầy đủ nội thất", "label_en": "full", "value": "full"},
]
RE_SETTING_IMG_DIRS = [
    {"value": os.path.join("repositories", "products", "re"), "is_selected": 1}
]
RE_SETTING_TEMPLATE_TITLES = [
    {
        "tid": "T.T.default",
        "option_id": 1,
        "value": "[<option>] <icon><icon> cần <option> <category> <price> <unit>, <ward>, <district>, <province> <icon><icon>",
    }
]
RE_SETTING_TEMPLATE_DESCRIPTIONS = [
    {
        "tid": "T.D.default",
        "option_id": 1,
        "value": "ID: <PID>\n🗺 Vị trí: đường <street>, <ward>, <district>\n📏 Diện tích: <area>\n🏗 Kết cấu: <structure>\n🛌 Công năng: <function>\n📺 Nội thất: <furniture>\n🚗 Lộ giới: <building_line>\n📜 Pháp lý: <legal>\n<icon><icon> Mô tả:\n<description>\n------------\n💵 Giá: <price><unit>- Thương lượng chính chủ\n\n☎ Liên hệ: 0375.155.525 - Mr. Bình\n🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺\n🌺Ký gửi mua, bán - cho thuê, thuê bất động sản xin liên hệ 0375.155.525 - Mr. Bình🌺\n🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺",
    }
]
USER_SETTING_UDD = [
    {"value": os.path.join("repositories", "users", "user_data_dir"), "is_selected": 1}
]
