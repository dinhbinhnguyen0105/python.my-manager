S_NAVIGATION = "div[role='navigation']"
S_BANNER = "div[role='banner']"
S_MAIN = "div[role='main']"
S_LOADING = "div[role='status'][data-visualcompletion='loading-state']"
S_TABLIST = "div[aria-orientation='horizontal'][role='tablist']"
S_TABLIST_TAB = "[role='tab'][aria-hidden='false']"
S_BUTTON = "div[role='button']"
S_TEXTBOX = "[role='textbox']"


def s_profile(language):
    if language == "vi":
        return "[aria-label='trang cá nhân' i]"
    elif language == "en":
        return "[aria-label='profile' i]"


def s_dialog_create_post(language):
    if language == "vi":
        return "[aria-label='tạo bài viết' i][role='dialog']"
    elif language == "en":
        return "[aria-label='create post' i][role='dialog']"


def s_close_button(language):
    if language == "vi":
        return "[aria-label='đóng' i][role='button']"
    elif language == "en":
        return "[aria-label='close' i][role='button']"


S_PROFILE = s_profile
S_DIALOG_CREATE_POST = s_dialog_create_post
S_CLOSE_BUTTON = s_close_button
