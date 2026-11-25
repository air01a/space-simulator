########################################
# "Ghost" attractor: where an attractor will be when the orbiter enters
# (or leaves) its SOI. Text helpers (no Kivy)
########################################


def format_eta(seconds):
    """Delay before an event: "+12 min", "+97 h 03" (up to 5 days), "+6 d 01 h" """
    minutes = max(0, int(seconds // 60))
    if minutes < 60:
        return "+%d min" % minutes
    hours, minutes = divmod(minutes, 60)
    if hours < 120:
        return "+%d h %02d" % (hours, minutes)
    days, hours = divmod(hours, 24)
    return "+%d d %02d h" % (days, hours)


def ghost_label(name, seconds):
    return "%s %s" % (name, format_eta(seconds))
