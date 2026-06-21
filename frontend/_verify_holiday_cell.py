"""Throwaway verification script for the holiday-cell-height fix. Not part
of the app; deleted after the run. Confirms:
1. get_css() (pure function, no Streamlit needed) contains the new
   stVerticalBlockBorderWrapper reset rules and the updated .ly-cal-holiday
   block (height:100%, no more hardcoded 78px triple).
2. A real AppTest render of the manager Calendar screen for June 2026 (the
   exact month/holiday from the user's screenshot: 26 Jun / Muharram)
   completes with zero exceptions.
3. The holiday cell's markup (.ly-cal-holiday, day number, "Muharram") is
   present in the rendered output.
4. The block tree actually contains a container whose key matches the new
   f"{key_prefix}-hol-{iso}" pattern -- i.e. st.container(height=78,...) was
   really invoked for this day, not skipped.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from design_tokens import get_css

css = get_css()
assert "stVerticalBlockBorderWrapper" in css, "new wrapper-reset rule missing from get_css() output"
assert ".ly-cal-holiday {" in css
holiday_block = css.split(".ly-cal-holiday {")[1].split("}")[0]
assert "height: 100%;" in holiday_block, f"expected height:100% in .ly-cal-holiday, got: {holiday_block}"
assert "78px" not in holiday_block, f".ly-cal-holiday should no longer hardcode 78px, got: {holiday_block}"
print("CHECK 1 PASSED: get_css() contains the new rules, .ly-cal-holiday now uses height:100%")

from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py")
at.run()
assert not at.exception, f"Exception on initial load: {at.exception}"

at.session_state["user"] = {
    "id": 1, "name": "Asha Krishnan", "email": "manager@leavely.com",
    "role": "manager", "manager_id": None, "location": "Chennai",
    "bio": None, "is_active": True, "must_change_password": False,
}
at.session_state["nav"] = "Calendar"
at.run()
assert not at.exception, f"Exception rendering Calendar: {at.exception}"

# Confirm June 2026 is the month being shown (it should be, since "today"
# inside the sandboxed test run is whatever the system clock says -- but
# force it explicitly via the same state key calendar_section uses, so this
# test doesn't silently stop covering the holiday once June 2026 is in the
# past).
at.session_state["mgr-month"] = (2026, 6)
at.run()
assert not at.exception, f"Exception after forcing June 2026: {at.exception}"

all_markdown = "\n".join(m.value for m in at.markdown)
assert "ly-cal-holiday" in all_markdown, "holiday cell markup not found in rendered output"
assert "Muharram" in all_markdown, "holiday name not found in rendered output"
print("CHECK 2 PASSED: Calendar (June 2026) renders the Muharram holiday cell with zero exceptions")

# Walk the actual block tree for a container with the new holiday key.
found_container_key = None
def walk(node, depth=0):
    global found_container_key
    key = getattr(node, "key", None)
    if key and "mgr-hol-2026-06-26" in str(key):
        found_container_key = key
    children = getattr(node, "children", None)
    if children:
        for child in (children.values() if isinstance(children, dict) else children):
            walk(child, depth + 1)

walk(at.main)
assert found_container_key, "did not find a container keyed 'mgr-hol-2026-06-26-...' in the block tree -- st.container(height=78) for the holiday cell was not actually invoked"
print(f"CHECK 3 PASSED: found holiday st.container in block tree, key={found_container_key}")

print("ALL VERIFICATION CHECKS PASSED")
