import base64
import json
import time

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .browser import build_driver
from .email.base import EmailProvider
from .proxy import start_proxy

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _decode_user_id(token):
    try:
        p = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4))).get("sub", "")
    except Exception:
        return ""


def _click_resend(driver):
    try:
        text = (driver.execute_script("return document.body.innerText || '';") or "").lower()
        if "email delivered" in text:
            print("[*] Opus confirma 'Email delivered' — aguardando inbox mais 15s")
            return False
        if "email delayed" in text:
            resend = driver.find_elements(By.XPATH, "//a[normalize-space()='Resend']")
            if resend:
                resend[0].click()
                print("[*] Opus reportou 'Email delayed' — Resend clicado")
                return True
        print("[*] Estado incerto — aguardando mais 15s")
        return False
    except Exception as e:
        print(f"[*] _click_resend falhou: {e}")
        return False


def _wait_for_capture(driver, timeout=30):
    token = org = None
    for _ in range(timeout):
        token = token or driver.execute_script("return document.documentElement.getAttribute('data-token');")
        org = org or driver.execute_script("return document.documentElement.getAttribute('data-org');")
        if token and org:
            return token, org
        time.sleep(1)
    return token, org


def _api_context(token, org, user_id, proxy_port):
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "origin": "https://clip.opus.pro",
        "referer": "https://clip.opus.pro/",
        "user-agent": UA,
        "x-opus-org-id": org,
        "x-opus-user-id": user_id,
        "x-opus-device-platform": "web",
    }
    proxies = {"http": f"http://127.0.0.1:{proxy_port}", "https": f"http://127.0.0.1:{proxy_port}"}
    return headers, proxies


def _json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


def _create_key(token, org, user_id, proxy_port):
    headers, proxies = _api_context(token, org, user_id, proxy_port)
    r = requests.post(
        "https://api.opus.pro/api/api-keys",
        headers=headers, json={"orgId": org}, proxies=proxies, timeout=15,
    )
    return r.status_code, (_json(r).get("data") or {}).get("secretKey")


def _get_credits(token, org, user_id, proxy_port):
    headers, proxies = _api_context(token, org, user_id, proxy_port)
    r = requests.get(
        "https://api.opus.pro/api/org-credits?q=mine",
        headers=headers, proxies=proxies, timeout=15,
    )
    credits = (_json(r).get("data") or {}).get("credits", [])
    total = sum(c.get("creditAvailable", 0) for c in credits if c.get("isActive"))
    return r.status_code, total


def create_account(email_provider: EmailProvider):
    email = email_provider.generate()
    print(f"[+] Email: {email}")
    driver = proxy = None
    try:
        proxy = start_proxy()
        proxy_port = proxy.server_address[1]
        driver = build_driver(proxy_port)
        wait = WebDriverWait(driver, 20)
        driver.get("https://clip.opus.pro/auth/oauth/login")

        wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Enter email address']"))).send_keys(email)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(), 'Continue with email')]]"))).click()

        otp = email_provider.get_otp(email, on_stalled=lambda: _click_resend(driver))
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

        key = None
        for i in range(1, 7):
            try:
                status, key = _create_key(token, org, user_id, proxy_port)
                if key:
                    break
                print(f"[*] Aguardando key... {i}/6 (status={status})")
            except Exception as e:
                print(f"[*] Key retry {i}: {e}")
            time.sleep(min(i, 3))

        if not key:
            print("[!] Key não emitida")
            return None

        for i in range(1, 16):
            try:
                status, total = _get_credits(token, org, user_id, proxy_port)
                if total > 0:
                    minutes = total // 60
                    print(f"[+] KEY: {key}")
                    print(f"[+] {minutes}min ({total} credits)")
                    return f"{key} | {minutes}min ({total} credits)"
                print(f"[*] Aguardando créditos... {i}/15 (total={total})")
            except Exception as e:
                print(f"[*] Credits retry {i}: {e}")
            time.sleep(2)

        print("[!] Créditos não depositados após timeout")
    except Exception as e:
        print(f"[!] {e}")
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass
        try:
            if proxy:
                proxy.shutdown()
                proxy.server_close()
        except Exception:
            pass
    return None
