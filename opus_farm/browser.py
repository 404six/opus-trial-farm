import base64

from seleniumbase import Driver

from config import BLOCKED_URLS, HEADLESS
from .scripts import JS_INTERCEPT


def _pac_url(proxy_port):
    pac = (
        f'function FindProxyForURL(u,h){{'
        f'if(shExpMatch(h,"*.opus.pro")||shExpMatch(h,"opus.pro"))'
        f'return"PROXY 127.0.0.1:{proxy_port}";'
        f'return"DIRECT";}}'
    )
    return "data:application/x-ns-proxy-autoconfig;base64," + base64.b64encode(pac.encode()).decode()


def build_driver(proxy_port):
    driver = Driver(
        uc=True,
        headless2=HEADLESS,
        page_load_strategy="eager",
        chromium_arg=[
            f"--proxy-pac-url={_pac_url(proxy_port)}",
            "--disable-quic",
            "--mute-audio",
            "--blink-settings=imagesEnabled=false",
            "--disable-background-networking",
            "--disable-features=Translate,MediaRouter,OptimizationHints",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-sync",
            "--disable-default-apps",
        ],
    )
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": BLOCKED_URLS})
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": JS_INTERCEPT})
    return driver
