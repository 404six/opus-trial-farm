import time

from config import META_CHAVES, OUTPUT_FILE
from opus_farm.automation import create_account
from opus_farm.email.darkemail import DarkEmailProvider


def main():
    provider = DarkEmailProvider()
    n = 0
    with open(OUTPUT_FILE, "a") as f:
        while n < META_CHAVES:
            print(f"\n{'=' * 40}\n[*] Conta {n + 1}/{META_CHAVES}")
            result = create_account(provider)
            if result:
                f.write(result + "\n")
                f.flush()
                n += 1
            time.sleep(3)
    print(f"\n[+] {n} chaves salvas em {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
