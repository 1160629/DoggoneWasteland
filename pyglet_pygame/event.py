global window
window = None

def get():
    global window
    window.window.dispatch_events()
    return []