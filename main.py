# from ciscoreset.xml import XMLPhone
# from ciscoreset.credentials import get_credentials
# from ciscoreset.configs import ROOT_DIR
# from pathlib import Path

# p = XMLPhone("10.12.4.231", *get_credentials(), "8865")
# p.download_screenshot(str(ROOT_DIR / "tmp" / "tester.bmp"))


from ciscoreset.gui import run

run()
