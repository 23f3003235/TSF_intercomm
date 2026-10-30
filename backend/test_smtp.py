
import os
import ssl
import smtplib
import sys

from dotenv import load_dotenv

# Always read the latest values from .env
load_dotenv(override=True)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = (
    os.getenv("SMTP_APP_PASSWORD", "")
    .replace(" ", "")
    .strip()
)


def print_environment():
    print("=" * 55)
    print("GMAIL SMTP DIAGNOSTIC")
    print("=" * 55)

    print("Python:", sys.version.split()[0])
    print("OpenSSL:", ssl.OPENSSL_VERSION)
    print("SMTP server:", SMTP_HOST)
    print("SMTP port:", SMTP_PORT)

    print("\nCredential configuration:")
    print("SMTP user:", SMTP_USER or "NOT CONFIGURED")
    print("App Password present:", bool(SMTP_PASSWORD))
    print("App Password length:", len(SMTP_PASSWORD))

    if not SMTP_USER or not SMTP_PASSWORD:
        raise SystemExit(
            "\nERROR: SMTP credentials are missing from .env"
        )

    if len(SMTP_PASSWORD) != 16:
        raise SystemExit(
            "\nERROR: Gmail App Password should contain "
            "16 characters after removing spaces."
        )


def connect_smtp():
    server = smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=20
    )

    try:
        print("\nConnecting to Gmail SMTP...")

        code, message = server.ehlo()
        print("EHLO response:", code)

        if code != 250:
            raise RuntimeError("SMTP EHLO failed")

        print("STARTTLS supported:",
              server.has_extn("starttls"))

        print("\nStarting TLS...")

        context = ssl.create_default_context()
        server.starttls(context=context)

        print("TLS established successfully")

        code, message = server.ehlo()
        print("EHLO after TLS:", code)

        if code != 250:
            raise RuntimeError("EHLO after TLS failed")

        print(
            "Available AUTH methods:",
            server.esmtp_features.get("auth", "None")
        )

        return server

    except Exception:
        server.close()
        raise


def test_authentication(method):
    print("\n" + "-" * 55)
    print("Testing authentication:", method)
    print("-" * 55)

    server = None

    try:
        server = connect_smtp()

        advertised = server.esmtp_features.get("auth", "")
        supported = advertised.upper().split()

        if method not in supported:
            print(
                "SKIPPED:",
                method,
                "not advertised by server"
            )
            return False

        if method == "PLAIN":
            server.auth(
                "PLAIN",
                lambda challenge=None: (
                    "\0" + SMTP_USER + "\0" + SMTP_PASSWORD
                ),
                initial_response_ok=True
            )

        elif method == "LOGIN":
            server.auth(
                "LOGIN",
                lambda challenge=None: SMTP_USER
                if challenge is None
                else SMTP_PASSWORD,
                initial_response_ok=True
            )

        print("\nSUCCESS: Gmail authentication completed")
        print("Authentication method:", method)
        return True

    except smtplib.SMTPAuthenticationError as error:
        print("\nAUTHENTICATION REJECTED")
        print("SMTP code:", error.smtp_code)
        print("SMTP response:", error.smtp_error.decode(
            errors="replace"
        ) if isinstance(error.smtp_error, bytes)
          else str(error.smtp_error))
        return False

    except smtplib.SMTPServerDisconnected as error:
        print("\nCONNECTION CLOSED DURING AUTHENTICATION")
        print("Error:", str(error))
        return False

    except Exception as error:
        print("\nFAILED")
        print("Error type:", type(error).__name__)
        print("Error:", str(error))
        return False

    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                server.close()


def main():
    print_environment()

    if test_authentication("PLAIN"):
        return

    if test_authentication("LOGIN"):
        return

    print("\n" + "=" * 55)
    print("RESULT: SMTP AUTHENTICATION FAILED")
    print("=" * 55)

    print(
        "\nPossible causes:\n"
        "1. Gmail App Password is invalid or revoked.\n"
        "2. SMTP_USER does not match the App Password account.\n"
        "3. Network or security software interrupts SMTP AUTH.\n"
        "4. Google account policy restricts SMTP authentication."
    )


if __name__ == "__main__":
    main()

