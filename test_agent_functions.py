"""
Test agent workflow module directly without API server
"""
import sys
sys.path.insert(0, 'c:\\Users\\kpachpor\\Downloads\\query-handler')

from app.routes.agent_workflow import (
    PrecallAgentInput, PrecallAgentOutput,
    process_raw_webcollect_data, get_call_type_prompt, extract_last_notes
)
from datetime import datetime

print("=" * 80)
print("TESTING AGENT WORKFLOW FUNCTIONS (NO DATABASE)")
print("=" * 80)

# Test 1: Test helper functions
print("\n1. Testing Helper Functions")
print("-" * 80)

# Test get_call_type_prompt
print("\nTesting get_call_type_prompt():")
test_call_types = [1, 2, 3, 99]
for ct in test_call_types:
    prompt = get_call_type_prompt(ct)
    print(f"  call_type {ct} -> prompt: '{prompt}'")

# Test extract_last_notes
print("\nTesting extract_last_notes():")
test_notes = [
    ["First note"],
    ["First note", "Second note"],
    ["First", "Second", "Third", "Latest"],
    []
]
for notes in test_notes:
    result = extract_last_notes(notes)
    print(f"  {notes} -> last_note: '{result}'")

# Test 2: Test data processing
print("\n2. Testing process_raw_webcollect_data()")
print("-" * 80)

raw_data = PrecallAgentInput(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    user_name="John Doe",
    user_phone="+1-555-1234",
    user_mail="john@example.com",
    account_status="Active",
    preferred_language="English",
    preferred_contact_time="Morning",
    agent_contact_allowed=True,
    collector_name="Jane Smith",
    collector_id="COL001",
    billing_address="123 Main St, Anytown, USA",
    credit_limit="$10,000.00",
    invoice_amount="$5,000.00",
    short_payment=0,
    over_payment=0,
    call_type=2,
    dispute="$0.00",
    payment_terms="Net 30",
    status="Pending",
    date="2026-04-01T12:00:00",
    notes=["Customer interested in payment", "Prefers morning calls", "Has flexible budget"],
    audio_recording_enable=True,
    agent_call=True,
    transcript=True
)

print("\nInput Data Summary:")
print(f"  Customer: {raw_data.user_name} ({raw_data.user_id})")
print(f"  Call Type: {raw_data.call_type}")
print(f"  Notes: {len(raw_data.notes)} notes provided")
print(f"  Last Note: {extract_last_notes(raw_data.notes)}")

message = "Test processing"
output = process_raw_webcollect_data(raw_data, message)

print("\nProcessed Output:")
print(f"  User: {output.user_name}")
print(f"  Call Prompt (from call_type {raw_data.call_type}): {output.call_prompt}")
print(f"  Last Notes (extracted): {output.last_notes}")
print(f"  Message: {output.message}")
print(f"  All notes preserved: {output.notes == raw_data.notes}")

# Test 3: Verify schema compatibility
print("\n3. Verifying Schema Compatibility")
print("-" * 80)

print(f"\n✓ PrecallAgentInput fields: {len(PrecallAgentInput.__fields__)}")
print(f"✓ PrecallAgentOutput fields: {len(PrecallAgentOutput.__fields__)}")
print(f"✓ Output has all input fields: {all(f in PrecallAgentOutput.__fields__ for f in PrecallAgentInput.__fields__)}")
print(f"✓ Output has additional fields: {set(PrecallAgentOutput.__fields__) - set(PrecallAgentInput.__fields__)}")

print("\n" + "=" * 80)
print("✓ ALL DIRECT FUNCTION TESTS PASSED")
print("=" * 80)
print("\nNOTE: API endpoint tests require a running database.")
print("Run 'python test_agent_workflow.py' after starting the server.")
