import base64
import json
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .browser import build_driver
from .email.base import EmailProvider
from .proxy import start_proxy
from .scripts import JS_CREATE_KEY


def _decode_user_id(token):
    try:
        p = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4))).get("sub", "")
    except Exception:
        return ""


def _wait_for_capture(driver, timeout=30):
    token = org = None
    for _ in range(timeout):
        token = token or driver.execute_script("return document.documentElement.getAttribute('data-token');")
        org = org or driver.execute_script("return document.documentElement.getAttribute('data-org');")
        if token and org:
            return token, org
        time.sleep(1)
    return token, org


def create_account(email_provider: EmailProvider):
    email = email_provider.generate()
    print(f"[+] Email: {email}")
    driver = proxy = None
    try:
        proxy = start_proxy()
        driver = build_driver(proxy.server_address[1])
        wait = WebDriverWait(driver, 20)

        driver.get("https://clip.opus.pro/auth/oauth/login")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Enter email address']"))).send_keys(email)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(), 'Continue with email')]]"))).click()

        otp = email_provider.get_otp(email)
        if not otp:
            print("[!] OTP não recebido")
            return None
        print(f"[+] OTP: {otp}")

        wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Enter verification code']"))).send_keys(otp)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//div[normalize-space(text())='Continue']]"))).click()

        token, org = _wait_for_capture(driver)
        if not (token and org):
            print("[!] Interceptação falhou")
            return None
        print(f"[+] OrgID: {org}")

        user_id = _decode_user_id(token)
        wait.until(lambda d: "login" not in d.current_url.lower())
        wait.until(lambda d: "Your Free Trial Has Started" in d.page_source or "gtm_user_first_login" in d.current_url.lower())
        driver.set_script_timeout(15)

        for i in range(1, 7):
            r = driver.execute_async_script(JS_CREATE_KEY, token, org, user_id)
            key = (r.get("key") or {}).get("data", {}).get("secretKey")
            if key:
                credits = (r.get("credits") or {}).get("data", {}).get("credits", [])
                total = sum(c.get("creditAvailable", 0) for c in credits if c.get("isActive"))
                minutes = total // 60
                print(f"[+] KEY: {key}")
                print(f"[+] {minutes}min ({total} credits)")
                return f"{key} | {minutes}min ({total} credits)"
            print(f"[*] Provisionando... {i}/6")
            time.sleep(3)
    except Exception as e:
        print(f"[!] {e}")
    finally:
        if driver:
            driver.quit()
        if proxy:
            proxy.shutdown()
            proxy.server_close()
    return None
