# Baseline Diagnostic Check — CampusFlow Next

**Branch:** `feat/21-validation-and-notes`
**Audited Commit:** `97aa734c20cea1765a51c04924d89f9d6c282f83` (Sprint 1 Audited State on `main`)
**Date:** 2026-10-14
**Role:** Engineer A (Ticket Safety and Storage Engineer)

---

## 1. Automated Test Execution

### Command
```bash
python3 -m unittest discover -s tests -v
```

### Results
```
test_empty_queue (test_reports.ReportsTests.test_empty_queue) ... ok
test_empty_report_includes_zero_counts (test_reports.ReportsTests.test_empty_report_includes_zero_counts) ... ok
test_queue_does_not_reorder_or_modify_storage (test_reports.ReportsTests.test_queue_does_not_reorder_or_modify_storage) ... ok
test_queue_excludes_in_progress_and_resolved (test_reports.ReportsTests.test_queue_excludes_in_progress_and_resolved) ... ok
test_queue_priority_order (test_reports.ReportsTests.test_queue_priority_order) ... ok
test_queue_ties_use_numeric_ids_beyond_three_digits (test_reports.ReportsTests.test_queue_ties_use_numeric_ids_beyond_three_digits) ... ok
test_report_counts_every_ticket_without_mutation (test_reports.ReportsTests.test_report_counts_every_ticket_without_mutation) ... ok
test_load_corrupted_json_raises_storage_error_and_preserves_file (test_storage.StorageTests.test_load_corrupted_json_raises_storage_error_and_preserves_file) ... ok
test_load_list_with_non_dict_elements_raises_storage_error (test_storage.StorageTests.test_load_list_with_non_dict_elements_raises_storage_error) ... ok
test_load_non_existent_file_returns_empty_list (test_storage.StorageTests.test_load_non_existent_file_returns_empty_list) ... ok
test_load_non_list_json_raises_storage_error (test_storage.StorageTests.test_load_non_list_json_raises_storage_error) ... ok
test_save_and_load_round_trip (test_storage.StorageTests.test_save_and_load_round_trip) ... ok
test_save_creates_nested_directories_automatically (test_storage.StorageTests.test_save_creates_nested_directories_automatically) ... ok
test_save_non_list_raises_storage_error (test_storage.StorageTests.test_save_non_list_raises_storage_error) ... ok
test_create_ticket_populates_all_required_fields (test_tickets.TestTicketCreationAndLookup.test_create_ticket_populates_all_required_fields) ... ok
test_get_ticket_raises_not_found (test_tickets.TestTicketCreationAndLookup.test_get_ticket_raises_not_found) ... ok
test_get_ticket_success_and_case_insensitivity (test_tickets.TestTicketCreationAndLookup.test_get_ticket_success_and_case_insensitivity) ... ok
test_id_generation_with_existing_gaps (test_tickets.TestTicketCreationAndLookup.test_id_generation_with_existing_gaps) ... ok
test_list_tickets_returns_all (test_tickets.TestTicketCreationAndLookup.test_list_tickets_returns_all) ... ok
test_sequential_ticket_id_generation (test_tickets.TestTicketCreationAndLookup.test_sequential_ticket_id_generation) ... ok
test_rule1_high_urgency_and_10_or_more_users_critical (test_tickets.TestTicketPriorityEngine.test_rule1_high_urgency_and_10_or_more_users_critical) ... ok
test_rule2_high_urgency_or_10_or_more_users_high (test_tickets.TestTicketPriorityEngine.test_rule2_high_urgency_or_10_or_more_users_high) ... ok
test_rule3_medium_urgency_or_3_or_more_users_medium (test_tickets.TestTicketPriorityEngine.test_rule3_medium_urgency_or_3_or_more_users_medium) ... ok
test_rule4_all_remaining_valid_tickets_low (test_tickets.TestTicketPriorityEngine.test_rule4_all_remaining_valid_tickets_low) ... ok
test_normalize_valid_inputs (test_tickets.TestTicketValidation.test_normalize_valid_inputs) ... ok
test_reject_blank_or_whitespace_title (test_tickets.TestTicketValidation.test_reject_blank_or_whitespace_title) ... ok
test_reject_boolean_affected_users (test_tickets.TestTicketValidation.test_reject_boolean_affected_users) ... ok
test_reject_decimal_affected_users (test_tickets.TestTicketValidation.test_reject_decimal_affected_users) ... ok
test_reject_invalid_category (test_tickets.TestTicketValidation.test_reject_invalid_category) ... ok
test_reject_invalid_urgency (test_tickets.TestTicketValidation.test_reject_invalid_urgency) ... ok
test_reject_negative_affected_users (test_tickets.TestTicketValidation.test_reject_negative_affected_users) ... ok
test_reject_non_numeric_affected_users (test_tickets.TestTicketValidation.test_reject_non_numeric_affected_users) ... ok
test_reject_zero_affected_users (test_tickets.TestTicketValidation.test_reject_zero_affected_users) ... ok
test_assigned_ticket_completes_lifecycle (test_workflow.WorkflowTests.test_assigned_ticket_completes_lifecycle) ... ok
test_assignment_normalizes_id_and_trims_name (test_workflow.WorkflowTests.test_assignment_normalizes_id_and_trims_name) ... ok
test_errors_match_shared_cli_exception_contract (test_workflow.WorkflowTests.test_errors_match_shared_cli_exception_contract) ... ok
test_invalid_id_inputs (test_workflow.WorkflowTests.test_invalid_id_inputs) ... ok
test_invalid_staff_names_do_not_mutate (test_workflow.WorkflowTests.test_invalid_staff_names_do_not_mutate) ... ok
test_invalid_statuses_do_not_mutate (test_workflow.WorkflowTests.test_invalid_statuses_do_not_mutate) ... ok
test_only_resolved_tickets_can_reopen (test_workflow.WorkflowTests.test_only_resolved_tickets_can_reopen) ... ok
test_reassignment_of_in_progress_ticket (test_workflow.WorkflowTests.test_reassignment_of_in_progress_ticket) ... ok
test_resolved_ticket_locked_until_explicit_reopen (test_workflow.WorkflowTests.test_resolved_ticket_locked_until_explicit_reopen) ... ok
test_skipping_and_no_op_transitions_rejected (test_workflow.WorkflowTests.test_skipping_and_no_op_transitions_rejected) ... ok
test_unassigned_cannot_start (test_workflow.WorkflowTests.test_unassigned_cannot_start) ... ok
test_unknown_ids_rejected_by_all_operations (test_workflow.WorkflowTests.test_unknown_ids_rejected_by_all_operations) ... ok

----------------------------------------------------------------------
Ran 45 tests in 0.021s

OK
```
All 45 existing unit tests passed cleanly.

---

## 2. Three Inputs Tested & Observations

### Input 1: Unassigned Ticket Status Transition
* **Operation:** `update_status(tickets, "T001", "in_progress")` with `assigned_to = None`.
* **Behavior:** Successfully raises `InvalidTransitionError("Assign the ticket before moving it to in_progress.")`.
* **Observation:** The lifecycle invariant preventing unassigned tickets from moving to in_progress is working at the function level. However, we must ensure it leaves the ticket collection strictly unmutated under all conditions.

### Input 2: Type Purity for `affected_users`
* **Operation:** `validate_ticket_input("Network outage", "Network", "high", True)`.
* **Behavior:** Raises `ValidationError("affected_users must be a positive integer.")`.
* **Observation:** The boolean check `isinstance(affected_users, bool)` guards against Python's `bool` subclassing `int`. However, `validate_ticket_input` currently accepts numeric strings (e.g. `"15"`), whereas the Next specification mandates that `affected_users` must be strictly a positive integer and reject strings masquerading as integers at the domain validation level.

### Input 3: JSON File with Duplicate Ticket IDs / Missing Schema Fields
* **Operation:** `load_tickets(filepath)` where the file contains `[{"id": "T001", "title": "A"}, {"id": "T001", "title": "B"}]`.
* **Behavior:** The baseline `load_tickets` returns the list with duplicate IDs without raising an error. It also does not validate required keys (`notes`, `category`, `urgency`, `priority`, `status`, `assigned_to`) or consistency.
* **Observation:** **Confirmed audit gap.** The baseline storage layer only validated that the root JSON structure was a list of dicts. It did not validate domain schema, ticket ID uniqueness, or consistency, leaving in-memory state vulnerable to corrupted files.

---

## 3. What the Audit Said Needed Improvement

1. **Ticket Schema & Follow-up Notes:**
   - Ticket schema must be upgraded to include `notes: []`.
   - Implement structured notes (`note_id`, `author`, `message`).
   - Guard note creation: only `open` or `in_progress` tickets can accept notes.
   - Guard note IDs: simple sequential `N001`, `N002`, ...; rejected notes must not consume an ID.
   - Note messages must be 5–300 characters after trimming, with a non-blank author.
2. **Centralized Defensive Validation:**
   - Centralize validation helpers (`can_transition`, `validate_ticket`).
   - Validate before mutating; invalid operations must leave the collection completely untouched.
   - Reject strings, floats, and booleans for `affected_users` at the domain level.
3. **Safe & Reproducible JSON Persistence:**
   - Full collection validation on load: required keys, legal enums, priority consistency, unique ticket IDs, valid note shapes, and unique note IDs per ticket.
   - Atomic load failure: if any record is invalid, reject the entire load with `StorageError` and preserve in-memory state.
   - ID continuity: guarantee next ticket ID and note ID generation will not collide after restarts or reloads.
