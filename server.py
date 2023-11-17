import json
import time
import flask
from playwright.sync_api import sync_playwright

APP = flask.Flask(__name__)
PLAY = sync_playwright().start()
BROWSER = PLAY.chromium.launch_persistent_context(
    user_data_dir='C:\\XXX\\XXX\\AppData\\Local\\ms-playwright',
    executable_path= ('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'),
    headless=False,
)
PAGE = BROWSER.new_page()

def get_input_box():
    return PAGE.query_selector(".text-area")

def is_logged_in():
    return get_input_box() is not None

def is_loading_response():
    return PAGE.query_selector(".stop").is_enabled()

def send_message(message):
    box = get_input_box()
    box.click()
    box.fill(message)
    box.press("Enter")

def get_last_message():
    while is_loading_response():
        time.sleep(0.25)

    page_elements = PAGE.query_selector_all("div[class*='ac-textBlock']")

    if not page_elements:
        return "No messages found."

    last_element = page_elements.pop()
    code_block = last_element.query_selector("code")

    if code_block:
        return last_element.inner_text()
    else:
        return last_element.inner_text(), None

@APP.route("/", methods=["GET"])
def index():
    return flask.send_file("index.html")

@APP.route("/select_tone", methods=["GET"])
def select_tone():
    selected_tone = flask.request.args.get("tone")

    if selected_tone.lower() == "creative":
        tone_button_selector = ".tone-creative"

    elif selected_tone.lower() == "balanced":
        tone_button_selector = ".tone-balanced"

    elif selected_tone.lower() == "precise":
        tone_button_selector = ".tone-precise"
    
    else:
        response_dict = {"text": "Invalid tone selected", "codeBlock": None}
        return json.dumps(response_dict)
    try:
        PAGE.click(tone_button_selector)

    except Exception as e:
        
        print("Error clicking tone button:", str(e))
        response_dict = {"text": "Error changing tone", "codeBlock": None}
        return json.dumps(response_dict)

    response_dict = {"text": "", "codeBlock": None}
    return json.dumps(response_dict)

@APP.route("/chat", methods=["GET"])
def chat():
    message_or_tone = flask.request.args.get("q")
    print("Sending message or tone: ", message_or_tone)

    if message_or_tone.lower() in ["creative", "balanced", "precise"]:
        return flask.redirect(flask.url_for("select_tone", tone=message_or_tone.lower()))

    send_message(message_or_tone)
    response = get_last_message()

    if isinstance(response, tuple) and len(response) >= 2:
        text_response, code_block_response = response
    else:
        text_response, code_block_response = response, None

    if "new topic" in text_response.lower():
        PAGE.query_selector("button[aria-label='New topic']").click()
        send_message(message_or_tone)
        response = get_last_message()

        if isinstance(response, tuple) and len(response) >= 2:
            text_response, code_block_response = response
        else:
            text_response, code_block_response = response, None

    response_dict = {"text": text_response, "codeBlock": code_block_response}

    return json.dumps(response_dict)

@APP.route("/restart", methods=["POST"])
def restart():
    global PAGE,BROWSER,PLAY
    PAGE.close()
    BROWSER.close()
    PLAY.stop()
    time.sleep(0.25)
    PLAY = sync_playwright().start()
    BROWSER = PLAY.firefox.launch_persistent_context(
        user_data_dir='C:\\XXX\\XXX\\AppData\\Local\\ms-playwright',
        executable_path= ('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'),
        headless=False,
    )
    PAGE = BROWSER.new_page()
    PAGE.goto("https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=hpcodx")
    return "API restart!"


def start_browser():
    PAGE.goto("https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=hpcodx")
    time.sleep(3.25)
    if not is_logged_in():
        print("Please log in to Bing AI Chat")
        print("Press enter when you're done")
        input()
    else:
        print("Logged in")
        APP.run(host='127.0.0.1', port=8000, threaded=False)

if __name__ == "__main__":
    start_browser()