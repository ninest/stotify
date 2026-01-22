# PRD: Custom Notification Groups

**Version:** 2.0
**Status:** Planning
**Author:** Claude
**Date:** 2026-01-22

---

## Executive Summary

Transition from per-alert notification channels to custom named groups, allowing users to subscribe to logical collections of alerts (e.g., "portfolio", "tech-watch") instead of individual ticker-threshold combinations.

**Current:** `stotify-AAPL-H250`, `stotify-GOOGL-L320` (N channels for N alerts)
**Proposed:** `stotify-portfolio`, `stotify-tech-watch` (M channels for M groups)

---

## Problem Statement

### Current Limitations
- **Channel proliferation**: Each ticker-threshold creates a new channel
- **Subscription overhead**: Users must subscribe to 10+ channels for a small portfolio
- **Poor organization**: No way to group related alerts (e.g., all tech stocks, all ETFs)
- **Management complexity**: Adding/removing alerts requires subscription updates

### User Pain Points
- "I have 20 stocks to monitor, I don't want 40+ ntfy.sh subscriptions"
- "I want all my portfolio alerts in one place, not scattered across channels"
- "I can't easily mute/unmute a category of stocks"

---

## Goals & Non-Goals

### Goals
✅ Allow custom named groups for organizing alerts
✅ Single subscription per logical group
✅ Maintain all existing alert functionality (high/low thresholds)
✅ Keep configuration simple and readable
✅ Update all tests to reflect new structure
✅ Update GitHub Actions workflow to list groups instead of individual channels

### Non-Goals
❌ Multi-channel support (one alert → multiple channels)
❌ Nested groups or hierarchies
❌ Per-group notification settings (priority, sound, etc.)
❌ Dynamic group creation via API
❌ Backward compatibility with old config format (breaking change)

---

## Solution Design

### Configuration Schema

#### New Structure (`alerts.json`)
```json
{
  "groups": {
    "portfolio": [
      {"ticker": "AAPL", "high": 248, "low": 246},
      {"ticker": "MSFT", "high": 420}
    ],
    "tech-watch": [
      {"ticker": "GOOGL", "high": 340},
      {"ticker": "NVDA", "low": 800}
    ],
    "crypto-stocks": [
      {"ticker": "COIN", "high": 220, "low": 180}
    ]
  }
}
```

#### Schema Rules
- **Root key:** `"groups"` (object/dict)
- **Group names:** Keys in the groups object
  - Must be valid ntfy.sh channel names
  - Alphanumeric, hyphens, underscores only
  - No spaces or special characters
  - Max 100 characters (ntfy.sh limitation)
  - Case-sensitive
- **Alerts:** Arrays of alert objects (existing structure)
  - Each alert requires `ticker` (string)
  - Must have at least one of `high` or `low` (number)
  - Both thresholds allowed on same alert

#### Old Structure (deprecated)
```json
{
  "alerts": [
    {"ticker": "AAPL", "high": 248, "low": 246}
  ]
}
```

---

## Component Changes

### 1. Configuration Loading (`stotify/main.py`)

#### `load_config()` Updates
**Current validation:**
- Expects `"alerts"` array
- Validates ticker + threshold presence

**New validation:**
- Expects `"groups"` dict
- Validates group names (alphanumeric + hyphens/underscores)
- Validates each group has ≥1 alert
- Validates each alert has ticker + (high or low)
- Error messages include group name for debugging

**Error cases:**
- Missing `"groups"` key → `ValueError: Config must have 'groups' object`
- Empty groups → `ValueError: Group 'xyz' has no alerts`
- Invalid group name → `ValueError: Group name 'my group!' contains invalid characters`
- Alert missing ticker → `ValueError: Alert in group 'portfolio' missing 'ticker'`
- Alert missing thresholds → `ValueError: Alert for AAPL in group 'portfolio' must have 'high' or 'low'`

#### `check_alerts()` Updates
**Current signature:**
```python
def check_alerts(config: dict, skip_market_check: bool = False) -> int
```

**New behavior:**
- Iterate over groups first, then alerts within each group
- Pass group name to `send_alert()`
- Return total count (same as before)

**Pseudocode:**
```
for group_name, alerts in config["groups"].items():
    for alert in alerts:
        check price
        if threshold crossed:
            send_alert(..., group_name)
```

---

### 2. Notification System (`stotify/notifier.py`)

#### `get_channel()` Replacement
**Current:**
```python
def get_channel(ticker: str, alert_type: str, threshold: float, prefix: str | None = None) -> str:
    # Returns: stotify-AAPL-H250
```

**New:**
```python
def get_channel(group_name: str, prefix: str | None = None) -> str:
    # Returns: stotify-portfolio
```

**Simplification:** No ticker/threshold logic needed

#### `send_alert()` Updates
**Current signature:**
```python
def send_alert(ticker: str, price: float, alert_type: str, threshold: float) -> bool
```

**New signature:**
```python
def send_alert(ticker: str, price: float, alert_type: str, threshold: float, group_name: str) -> bool
```

**Message format:**
- **Old:** `"AAPL is $255.50 (above $250.00)"`
- **New:** `"[portfolio] AAPL is $255.50 (above $250.00)"`

**Changes:**
- Add `group_name` parameter
- Prefix message with `[{group_name}]`
- Call `get_channel(group_name)` instead of old signature

---

### 3. Helper Scripts

#### `scripts/list_topics.py`
**Current behavior:**
- Outputs one line per alert-threshold
- Example: `stotify-AAPL-H248`, `stotify-AAPL-L246`, `stotify-GOOGL-H323`

**New behavior:**
- Outputs one line per group
- Example: `stotify-portfolio`, `stotify-tech-watch`, `stotify-crypto-stocks`

**Pseudocode:**
```
config = load_config()
for group_name in config["groups"].keys():
    print(get_channel(group_name))
```

**Output format:**
```
stotify-portfolio
stotify-tech-watch
stotify-crypto-stocks
```

---

### 4. GitHub Actions Workflow

#### `.github/workflows/check_stocks.yml`
**Current:** No listing step

**New:** Add job/step to list all notification channels

**Two approaches:**

**Option A: Add step to existing workflow**
```yaml
- name: List notification channels
  run: uv run python scripts/list_topics.py
```

**Option B: Separate workflow** (`.github/workflows/list_topics.yml`)
- Runs on: push to main, manual trigger
- Lists all active channels
- Useful for documentation/verification

**Recommendation:** Option A (simpler, shows channels on every run)

**Placement:** After package install, before check_alerts step

---

## Testing Strategy

### Unit Tests to Update

#### `tests/test_main.py`
**Fixtures to update:**
- All config fixtures from `"alerts"` to `"groups"` format
- Add valid group name tests
- Add invalid group name tests (spaces, special chars, empty)

**New test cases:**
- `test_load_config_with_groups()` - Valid groups structure
- `test_load_config_missing_groups_key()` - Error on missing key
- `test_load_config_invalid_group_name()` - Validation errors
- `test_load_config_empty_group()` - Error on empty alert array
- `test_check_alerts_with_groups()` - Integration test

**Update existing:**
- All alert checking tests to use groups structure
- Config validation tests

#### `tests/test_notifier.py`
**Update:**
- `test_get_channel()` - New signature, simpler logic
  - Input: `("portfolio", "stotify")`
  - Output: `"stotify-portfolio"`
- `test_send_alert()` - New signature with group_name
  - Verify message includes `[group_name]` prefix
  - Verify correct channel used

**New test cases:**
- `test_get_channel_with_custom_prefix()`
- `test_get_channel_default_prefix()`
- `test_send_alert_message_format()` - Verify `[group] ticker...` format

#### `tests/test_stock.py`
**No changes needed** - Stock price fetching unaffected

#### `tests/test_market_hours.py`
**No changes needed** - Market hours logic unaffected

### Integration Tests

**Scenario 1: Multiple groups, single alert each**
- Config with 3 groups, 1 alert per group
- Verify 3 different channels used
- Verify correct group prefix in messages

**Scenario 2: Single group, multiple alerts**
- Config with 1 group, 5 alerts
- All notifications go to same channel
- Each message has correct ticker info

**Scenario 3: Mixed high/low in same group**
- Group with 2 high alerts, 2 low alerts
- Verify all use same channel
- Verify "above" vs "below" wording

**Scenario 4: Same ticker in multiple groups**
- AAPL in both "portfolio" and "tech-watch"
- Verify separate notifications to each group's channel
- Verify no cross-contamination

### Test Data

**Sample valid config:**
```json
{
  "groups": {
    "test-group": [
      {"ticker": "AAPL", "high": 250}
    ]
  }
}
```

**Sample invalid configs:**
```json
// Missing groups key
{"alerts": []}

// Empty group
{"groups": {"empty": []}}

// Invalid group name
{"groups": {"my portfolio!": [{"ticker": "AAPL", "high": 250}]}}

// Missing ticker
{"groups": {"test": [{"high": 250}]}}

// Missing thresholds
{"groups": {"test": [{"ticker": "AAPL"}]}}
```

---

## Validation Requirements

### Group Name Validation

**Valid characters:** `a-z A-Z 0-9 - _`
**Invalid:** spaces, special chars (`!@#$%^&*()`, etc.)

**Validation logic:**
```python
import re

def is_valid_group_name(name: str) -> bool:
    """Check if group name is valid ntfy.sh channel name."""
    if not name:
        return False
    if len(name) > 100:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
```

**Error messages:**
- Empty name: `"Group name cannot be empty"`
- Too long: `"Group name 'xyz...' exceeds 100 characters"`
- Invalid chars: `"Group name 'my group' contains invalid characters (only a-z, A-Z, 0-9, -, _ allowed)"`

### Alert Validation (unchanged)
- Ticker required (string)
- At least one of high/low required (number)
- Both high/low allowed

---

## Migration Guide

### For Users

**Step 1: Backup current config**
```bash
cp alerts.json alerts.json.backup
```

**Step 2: Convert to new format**

**Before:**
```json
{
  "alerts": [
    {"ticker": "AAPL", "high": 248, "low": 246},
    {"ticker": "GOOGL", "high": 323}
  ]
}
```

**After:**
```json
{
  "groups": {
    "my-stocks": [
      {"ticker": "AAPL", "high": 248, "low": 246},
      {"ticker": "GOOGL", "high": 323}
    ]
  }
}
```

**Step 3: List new channels**
```bash
uv run python scripts/list_topics.py
```

**Step 4: Update subscriptions**
- Unsubscribe from old channels (`stotify-AAPL-H248`, etc.)
- Subscribe to new group channels (`stotify-my-stocks`)

### Migration Script (optional future work)
```bash
# Converts old format to new with single "alerts" group
python scripts/migrate_config.py alerts.json
```

---

## User Workflows

### Workflow 1: Create New Group
1. Edit `alerts.json`
2. Add new group with alerts
3. Run `uv run python scripts/list_topics.py` to see channel name
4. Subscribe to channel on ntfy.sh app/web
5. Alerts will route to new channel on next run

### Workflow 2: Move Alert Between Groups
1. Edit `alerts.json`
2. Cut alert from one group, paste into another
3. No subscription changes needed (group channels unchanged)
4. Alert notifications now appear in new group's channel

### Workflow 3: Temporarily Mute Group
1. Mute group channel in ntfy.sh app (not in config)
2. Alerts still sent, but notifications suppressed by app
3. Unmute when ready to receive again

### Workflow 4: Split Large Group
1. Edit `alerts.json`
2. Create new group, move some alerts from existing group
3. Subscribe to new group channel
4. Both groups now active

---

## Edge Cases & Decisions

### 1. Same ticker in multiple groups
**Decision:** Allow
**Rationale:** Flexibility (e.g., AAPL in both "portfolio" and "high-volatility")
**Behavior:** Separate notifications sent to each group's channel

### 2. Empty groups
**Decision:** Error during validation
**Rationale:** Likely configuration mistake, no value in empty groups
**Error:** `ValueError: Group 'xyz' has no alerts`

### 3. Group name collisions with ntfy.sh reserved topics
**Decision:** No special handling (low risk)
**Rationale:** Unlikely to use names like "config", "announcements"
**Future:** Could add reserved word check if needed

### 4. Very long group names
**Decision:** Max 100 characters (ntfy.sh limit)
**Error:** `ValueError: Group name exceeds 100 characters`

### 5. Unicode in group names
**Decision:** Block non-ASCII characters
**Rationale:** URL safety, ntfy.sh compatibility
**Validation:** ASCII-only via regex `^[a-zA-Z0-9_-]+$`

### 6. Duplicate alerts within same group
**Decision:** Allow
**Rationale:** No harm (same notification sent twice)
**Future:** Could add warning in validation

---

## Success Metrics

### Pre-Launch
- ✅ All tests passing (100% pass rate)
- ✅ GitHub Actions workflow runs successfully
- ✅ Manual verification with real ntfy.sh channels

### Post-Launch
- Configuration is easier to read and organize
- Fewer ntfy.sh subscriptions required
- No functionality regressions (all alerts still fire correctly)

---

## Implementation Checklist

### Phase 1: Core Changes
- [ ] Update `load_config()` validation for groups structure
- [ ] Add group name validation function
- [ ] Update `get_channel()` to new signature
- [ ] Update `send_alert()` with group_name parameter
- [ ] Update `check_alerts()` to iterate groups

### Phase 2: Testing
- [ ] Update all test fixtures to groups format
- [ ] Update `test_main.py` config validation tests
- [ ] Update `test_notifier.py` channel generation tests
- [ ] Add new group name validation tests
- [ ] Add integration tests for multi-group scenarios
- [ ] Verify all tests pass

### Phase 3: Tooling
- [ ] Update `scripts/list_topics.py` for groups
- [ ] Update `.github/workflows/check_stocks.yml` to list channels
- [ ] Test workflow runs successfully

### Phase 4: Documentation
- [ ] Update README with new config format
- [ ] Add migration guide
- [ ] Update example configs
- [ ] Document group naming rules

### Phase 5: Deployment
- [ ] Commit all changes
- [ ] Push to feature branch
- [ ] Verify GitHub Actions run
- [ ] Manual test with real alerts
- [ ] Merge to main

---

## Open Questions

1. **Default group name if single group?** (e.g., auto-use "alerts" for simplicity)
   - Decision: No, require explicit naming for clarity

2. **Should we validate no duplicate alerts within a group?**
   - Decision: Allow for now, add warning later if needed

3. **Environment variable for group prefix override?**
   - Decision: Keep existing `NTFY_PREFIX` behavior (works same way)

4. **Should list_topics.py show alert counts per group?**
   - Decision: No, keep simple (just channel names)

5. **Example config in repo should have how many groups?**
   - Decision: 2-3 groups showing different use cases

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Users forget to update config | High - alerts stop working | Clear error messages, migration guide |
| Invalid group names break notifications | Medium - silent failure | Validation at config load, fail fast |
| Tests don't cover edge cases | Medium - bugs in production | Comprehensive test plan, integration tests |
| GitHub Actions workflow fails | Low - manual workaround exists | Test workflow before merge |

---

## Future Enhancements (Out of Scope)

- **Per-group notification settings** (priority, sound, icons)
- **Nested groups** (hierarchical organization)
- **Web UI for config management**
- **Automatic migration script**
- **Group-level muting/scheduling in config**
- **Email/SMS support per group**

---

## Approval & Sign-off

**Ready for implementation:** Pending user approval
**Breaking change:** Yes (v2.0)
**Estimated effort:** 2-4 hours (coding + testing)

---

## References

- Current codebase: `/home/user/stotify/`
- ntfy.sh docs: https://docs.ntfy.sh/
- Existing config: `/home/user/stotify/alerts.json`
- Test suite: `/home/user/stotify/tests/`
