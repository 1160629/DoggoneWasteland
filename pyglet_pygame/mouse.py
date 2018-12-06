global window
window = None


def get_pos():
    global window
    mx, my = window.window.mpos
    return mx, window.window.height-my

def get_pressed():
    global window
    mpressed = window.window.mpressed
    return mpressed