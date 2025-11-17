import re
import time
import uuid
import sys
from urllib.parse import urljoin

import requests

BASE_URL = "http://127.0.0.1:8001/"


def wait_for_server(timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(urljoin(BASE_URL, "login"), timeout=2)
            if r.status_code in (200, 302):
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def extract_xsrf(html: str) -> str:
    # Tornado uses hidden input name="_xsrf" in forms when xsrf_cookies=True
    m = re.search(r'name="_xsrf"\s+value="([^"]+)"', html)
    if not m:
        raise RuntimeError("_xsrf token not found in page")
    return m.group(1)


def main():
    s = requests.Session()

    if not wait_for_server():
        print("Server not responding on", BASE_URL, file=sys.stderr)
        sys.exit(2)

    # Register
    username = f"smoketest_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.test"
    password = "Test1234!"

    r = s.get(urljoin(BASE_URL, "register"))
    r.raise_for_status()
    xsrf = extract_xsrf(r.text)

    r = s.post(urljoin(BASE_URL, "register"), data={
        "_xsrf": xsrf,
        "username": username,
        "email": email,
        "password1": password,
        "password2": password,
    }, allow_redirects=True)
    r.raise_for_status()

    # After register, should be logged in; check houses page
    r = s.get(urljoin(BASE_URL, "houses"))
    r.raise_for_status()

    # Add house
    r = s.get(urljoin(BASE_URL, "houses/add"))
    r.raise_for_status()
    xsrf = extract_xsrf(r.text)

    house_name = f"Maison {uuid.uuid4().hex[:4]}"
    r = s.post(urljoin(BASE_URL, "houses/add"), data={
        "_xsrf": xsrf,
        "name": house_name,
        "address": "1 rue de Test",
    }, allow_redirects=True)
    r.raise_for_status()

    # Get houses list and find add_room link with id
    r = s.get(urljoin(BASE_URL, "houses"))
    r.raise_for_status()
    m = re.search(r"/houses/add_room\?house_id=(\d+)", r.text)
    if not m:
        print("No add_room link with house_id found", file=sys.stderr)
        sys.exit(3)
    house_id = m.group(1)

    # Add room
    r = s.get(urljoin(BASE_URL, f"houses/add_room?house_id={house_id}"))
    r.raise_for_status()
    xsrf = extract_xsrf(r.text)

    room_name = f"Salon {uuid.uuid4().hex[:4]}"
    r = s.post(urljoin(BASE_URL, "houses/add_room"), data={
        "_xsrf": xsrf,
        "house_id": house_id,
        "name": room_name,
    }, allow_redirects=True)
    r.raise_for_status()

    # Verify room appears on list
    r = s.get(urljoin(BASE_URL, "houses"))
    r.raise_for_status()
    if room_name not in r.text or house_name not in r.text:
        print("Room or house not found in listing", file=sys.stderr)
        sys.exit(4)

    print("SMOKE TEST PASSED: registration, login, add house, add room")


if __name__ == "__main__":
    main()
