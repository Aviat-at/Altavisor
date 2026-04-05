# Backend Test Report — Altavisor

**Date:** 2026-04-04  
**Time:** 20:50:39  
**Runner:** Django Test Framework (`manage.py test`)  
**Database:** In-memory SQLite (`file:memorydb_default?mode=memory&cache=shared`)  
**Python:** 3.12  
**Django:** 4.2.13  

---

## Summary

| Metric | Value |
|---|---|
| Total Tests | **302** |
| Passed | **302** |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Duration | 74.996s |
| Result | **PASS** |

---

## Coverage by App

| App | Module | Tests |
|---|---|---|
| `accounts` | test_models | 18 |
| `accounts` | test_views | 46 |
| `people` | test_models | 26 |
| `people` | test_selectors | 40 |
| `people` | test_services | 97 |
| `people` | test_views | 75 |
| **Total** | | **302** |

---

## accounts — Test Models (`accounts.tests.test_models`)

### `UserManagerTest` — 10 tests

| Test | Status |
|---|---|
| `test_create_superuser_is_staff_and_superuser` | PASS |
| `test_create_superuser_raises_if_is_staff_false` | PASS |
| `test_create_superuser_raises_if_is_superuser_false` | PASS |
| `test_create_user_is_active_by_default` | PASS |
| `test_create_user_is_not_staff_by_default` | PASS |
| `test_create_user_is_not_superuser_by_default` | PASS |
| `test_create_user_normalizes_email_domain` | PASS |
| `test_create_user_password_is_hashed` | PASS |
| `test_create_user_sets_email` | PASS |
| `test_create_user_without_email_raises` | PASS |

### `UserModelTest` — 8 tests

| Test | Status |
|---|---|
| `test_date_joined_is_set_on_creation` | PASS |
| `test_default_role_is_viewer` | PASS |
| `test_email_is_unique` | PASS |
| `test_initials_fallback_for_single_word_name` | PASS |
| `test_initials_fallback_to_email_when_no_full_name` | PASS |
| `test_initials_from_full_name` | PASS |
| `test_initials_from_multi_word_name_uses_first_and_last` | PASS |
| `test_str_returns_email` | PASS |

---

## accounts — Test Views (`accounts.tests.test_views`)

### `LoginViewTest` — 10 tests

| Test | Status |
|---|---|
| `test_login_email_is_case_insensitive` | PASS |
| `test_login_inactive_user_returns_401` | PASS |
| `test_login_missing_fields_returns_401` | PASS |
| `test_login_response_has_detail_on_failure` | PASS |
| `test_login_returns_access_and_refresh_tokens` | PASS |
| `test_login_returns_user_data` | PASS |
| `test_login_success_returns_200` | PASS |
| `test_login_unknown_email_returns_401` | PASS |
| `test_login_updates_last_login` | PASS |
| `test_login_wrong_password_returns_401` | PASS |

### `RefreshViewTest` — 3 tests

| Test | Status |
|---|---|
| `test_refresh_returns_new_access_token` | PASS |
| `test_refresh_with_invalid_token_returns_401` | PASS |
| `test_refresh_without_token_returns_400` | PASS |

### `LogoutViewTest` — 4 tests

| Test | Status |
|---|---|
| `test_logout_requires_authentication` | PASS |
| `test_logout_returns_200` | PASS |
| `test_logout_with_invalid_refresh_token_still_returns_200` | PASS |
| `test_logout_without_refresh_token_still_returns_200` | PASS |

### `MeViewTest` — 9 tests

| Test | Status |
|---|---|
| `test_get_me_includes_expected_fields` | PASS |
| `test_get_me_requires_authentication` | PASS |
| `test_get_me_returns_200` | PASS |
| `test_get_me_returns_current_user_data` | PASS |
| `test_patch_me_full_name_too_long_returns_400` | PASS |
| `test_patch_me_ignores_disallowed_fields` | PASS |
| `test_patch_me_requires_authentication` | PASS |
| `test_patch_me_strips_whitespace_from_full_name` | PASS |
| `test_patch_me_updates_full_name` | PASS |

### `ChangePasswordViewTest` — 7 tests

| Test | Status |
|---|---|
| `test_change_password_actually_changes_password` | PASS |
| `test_change_password_mismatch_returns_400` | PASS |
| `test_change_password_missing_fields_returns_400` | PASS |
| `test_change_password_requires_authentication` | PASS |
| `test_change_password_success_returns_200` | PASS |
| `test_change_password_too_short_returns_400` | PASS |
| `test_change_password_wrong_current_returns_400` | PASS |

### `RegisterViewTest` — 10 tests

| Test | Status |
|---|---|
| `test_register_creates_user` | PASS |
| `test_register_duplicate_email_returns_400` | PASS |
| `test_register_missing_email_returns_400` | PASS |
| `test_register_password_mismatch_returns_400` | PASS |
| `test_register_password_not_in_response` | PASS |
| `test_register_requires_admin` | PASS |
| `test_register_requires_authentication` | PASS |
| `test_register_returns_user_data` | PASS |
| `test_register_short_password_returns_400` | PASS |
| `test_register_success_returns_201` | PASS |

### `SSOViewTest` — 3 tests

| Test | Status |
|---|---|
| `test_sso_accessible_without_authentication` | PASS |
| `test_sso_returns_501` | PASS |
| `test_sso_returns_not_configured_message` | PASS |

---

## people — Test Models (`people.tests.test_models`)

### `PersonPropertyTest` — 10 tests

| Test | Status |
|---|---|
| `test_default_is_active` | PASS |
| `test_display_name_falls_back_to_full_name` | PASS |
| `test_display_name_uses_preferred_when_set` | PASS |
| `test_email_null_not_unique_constrained` | PASS |
| `test_email_nullable` | PASS |
| `test_email_unique_constraint` | PASS |
| `test_full_name` | PASS |
| `test_initials` | PASS |
| `test_initials_single_letter_parts` | PASS |
| `test_str` | PASS |

### `PersonCategoryModelTest` — 5 tests

| Test | Status |
|---|---|
| `test_default_is_active` | PASS |
| `test_default_is_not_system` | PASS |
| `test_name_unique_constraint` | PASS |
| `test_slug_unique_constraint` | PASS |
| `test_str` | PASS |

### `PersonCategoryAssignmentModelTest` — 3 tests

| Test | Status |
|---|---|
| `test_default_is_active` | PASS |
| `test_str` | PASS |
| `test_unique_together_constraint` | PASS |

### `PersonAddressModelTest` — 3 tests

| Test | Status |
|---|---|
| `test_default_is_active` | PASS |
| `test_default_label_is_home` | PASS |
| `test_str` | PASS |

### `PersonNoteModelTest` — 2 tests

| Test | Status |
|---|---|
| `test_created_at_set_on_create` | PASS |
| `test_str_contains_person_name` | PASS |

### `OrgRelationModelTest` — 3 tests

| Test | Status |
|---|---|
| `test_default_is_active` | PASS |
| `test_str` | PASS |
| `test_unique_together_constraint` | PASS |

---

## people — Test Selectors (`people.tests.test_selectors`)

### `ListPersonsTest` — 10 tests

| Test | Status |
|---|---|
| `test_active_assignments_prefetched` | PASS |
| `test_can_list_inactive_persons` | PASS |
| `test_filter_by_category_id` | PASS |
| `test_inactive_assignments_not_in_active_assignments` | PASS |
| `test_last_page_has_next_false` | PASS |
| `test_pagination_count_is_total_not_page` | PASS |
| `test_returns_active_persons_by_default` | PASS |
| `test_search_by_email` | PASS |
| `test_search_by_first_name` | PASS |
| `test_search_by_last_name` | PASS |

### `SearchPersonsTest` — 5 tests

| Test | Status |
|---|---|
| `test_empty_query_returns_all_active` | PASS |
| `test_excludes_inactive_by_default` | PASS |
| `test_finds_by_email` | PASS |
| `test_finds_by_first_name` | PASS |
| `test_includes_inactive_when_flag_set` | PASS |

### `GetPersonDetailTest` — 7 tests

| Test | Status |
|---|---|
| `test_active_assignments_prefetched_as_to_attr` | PASS |
| `test_addresses_prefetched` | PASS |
| `test_finds_inactive_person` | PASS |
| `test_notes_prefetched` | PASS |
| `test_only_active_addresses_in_prefetch` | PASS |
| `test_raises_if_not_found` | PASS |
| `test_returns_person` | PASS |

### `GetPersonCategoriesTest` — 4 tests

| Test | Status |
|---|---|
| `test_filters_inactive_by_default` | PASS |
| `test_get_active_person_categories_wrapper` | PASS |
| `test_includes_inactive_when_flag_false` | PASS |
| `test_returns_active_assignments` | PASS |

### `GetPersonAddressesTest` — 3 tests

| Test | Status |
|---|---|
| `test_default_address_ordered_first` | PASS |
| `test_includes_inactive_when_flag_false` | PASS |
| `test_returns_active_addresses_by_default` | PASS |

### `GetPersonNotesTest` — 2 tests

| Test | Status |
|---|---|
| `test_returns_empty_for_person_with_no_notes` | PASS |
| `test_returns_notes_newest_first` | PASS |

### `GetPersonOrganizationsTest` — 2 tests

| Test | Status |
|---|---|
| `test_active_only_flag` | PASS |
| `test_returns_all_by_default` | PASS |

### `ListCategoriesTest` — 5 tests

| Test | Status |
|---|---|
| `test_filter_active_only` | PASS |
| `test_filter_inactive_only` | PASS |
| `test_filter_system_only` | PASS |
| `test_ordered_by_name` | PASS |
| `test_returns_all_by_default` | PASS |

### `GetCategoryTest` — 2 tests

| Test | Status |
|---|---|
| `test_raises_if_not_found` | PASS |
| `test_returns_category` | PASS |

---

## people — Test Services (`people.tests.test_services`)

### `AssignCategoryTest` — 9 tests

| Test | Status |
|---|---|
| `test_creates_assignment` | PASS |
| `test_raises_if_category_inactive` | PASS |
| `test_raises_if_category_not_found` | PASS |
| `test_raises_if_person_inactive` | PASS |
| `test_raises_if_person_not_found` | PASS |
| `test_raises_on_duplicate_active_assignment` | PASS |
| `test_reactivates_previously_removed_assignment` | PASS |
| `test_sets_assigned_by` | PASS |
| `test_reactivated_assignment_updates_assigned_by` | PASS |

### `CloseOrganizationRelationshipTest` — 4 tests

| Test | Status |
|---|---|
| `test_closes_relation` | PASS |
| `test_is_idempotent` | PASS |
| `test_raises_if_not_found` | PASS |
| `test_sets_ended_on_to_today` | PASS |

### `CreateAddressTest` — 3 tests

| Test | Status |
|---|---|
| `test_creates_address` | PASS |
| `test_new_default_demotes_existing_default` | PASS |
| `test_raises_if_person_not_found` | PASS |

### `CreateAddressEdgeCaseTest` — 3 tests

| Test | Status |
|---|---|
| `test_default_label_is_home` | PASS |
| `test_non_default_address_does_not_affect_existing_default` | PASS |
| `test_raises_if_person_inactive` | PASS |

### `CreateCategoryTest`

| Test | Status |
|---|---|
| `test_creates_with_auto_slug` | PASS |

### `UpdateAddressTest`

| Test | Status |
|---|---|
| `test_updates_city` | PASS |

### `UpdateCategoryTest` — 5 tests

| Test | Status |
|---|---|
| `test_raises_if_not_found` | PASS |
| `test_raises_on_rename_system_category` | PASS |
| `test_raises_on_slug_collision` | PASS |
| `test_updates_description_on_system_category` | PASS |
| `test_updates_name_and_regenerates_slug` | PASS |

### `UpdateOrganizationRelationshipTest` — 3 tests

| Test | Status |
|---|---|
| `test_raises_if_not_found` | PASS |
| `test_updates_is_primary` | PASS |
| `test_updates_role` | PASS |

### `UpdatePersonTest` — 6 tests

| Test | Status |
|---|---|
| `test_duplicate_check_excludes_self` | PASS |
| `test_raises_if_person_inactive` | PASS |
| `test_raises_if_person_not_found` | PASS |
| `test_raises_on_duplicate_with_other_person` | PASS |
| `test_updates_email_to_none_when_blank` | PASS |
| `test_updates_first_name` | PASS |

### `UpdatePersonEdgeCaseTest` — 3 tests

| Test | Status |
|---|---|
| `test_partial_update_preserves_untouched_fields` | PASS |
| `test_updates_gender` | PASS |
| `test_updates_phone` | PASS |

---

## people — Test Views (`people.tests.test_views`)

### `PersonListCreateViewTest` — 12 tests

| Test | Status |
|---|---|
| `test_create_duplicate_returns_409` | PASS |
| `test_create_missing_required_fields_returns_400` | PASS |
| `test_create_returns_201` | PASS |
| `test_create_returns_detail_shape` | PASS |
| `test_create_with_force_bypasses_duplicate` | PASS |
| `test_invalid_page_size_returns_400` | PASS |
| `test_list_excludes_inactive_by_default` | PASS |
| `test_list_includes_inactive_when_param` | PASS |
| `test_list_returns_200_empty` | PASS |
| `test_list_returns_paginated_persons` | PASS |
| `test_list_search_param` | PASS |
| `test_requires_authentication` | PASS |

### `PersonDetailUpdateViewTest` — 5 tests

| Test | Status |
|---|---|
| `test_get_not_found_returns_404` | PASS |
| `test_get_returns_200` | PASS |
| `test_patch_duplicate_detected_returns_409` | PASS |
| `test_patch_inactive_person_returns_409` | PASS |
| `test_patch_returns_200` | PASS |

### `PersonDeactivateViewTest` — 3 tests

| Test | Status |
|---|---|
| `test_deactivate_already_inactive_returns_409` | PASS |
| `test_deactivate_not_found_returns_404` | PASS |
| `test_deactivate_returns_200` | PASS |

### `DuplicateCheckViewTest` — 3 tests

| Test | Status |
|---|---|
| `test_missing_required_fields_returns_400` | PASS |
| `test_no_duplicates_returns_false` | PASS |
| `test_with_name_duplicate_returns_true` | PASS |

### `MergePersonViewTest` — 3 tests

| Test | Status |
|---|---|
| `test_merge_missing_target_returns_400` | PASS |
| `test_merge_requires_admin` | PASS |
| `test_merge_returns_501` | PASS |

### `PersonListCategoryFilterTest` — 2 tests

| Test | Status |
|---|---|
| `test_filter_by_category_id` | PASS |
| `test_filter_by_nonexistent_category_id_returns_empty` | PASS |

### `PersonCategoryAssignmentViewTest` — 6 tests

| Test | Status |
|---|---|
| `test_assign_category_returns_201` | PASS |
| `test_assign_inactive_category_returns_404` | PASS |
| `test_duplicate_assign_returns_409` | PASS |
| `test_list_assignments_returns_200` | PASS |
| `test_remove_category_returns_204` | PASS |
| `test_remove_non_existent_assignment_returns_404` | PASS |

### `PersonAddressViewTest` — 6 tests

| Test | Status |
|---|---|
| `test_create_address_missing_required_returns_400` | PASS |
| `test_create_address_person_not_found_returns_404` | PASS |
| `test_create_address_returns_201` | PASS |
| `test_list_addresses_returns_200` | PASS |
| `test_update_address_not_found_returns_404` | PASS |
| `test_update_address_returns_200` | PASS |

### `AddressInactivePersonTest` — 1 test

| Test | Status |
|---|---|
| `test_create_address_for_inactive_person_returns_404` | PASS |

### `PersonNoteViewTest` — 5 tests

| Test | Status |
|---|---|
| `test_create_note_empty_body_returns_400` | PASS |
| `test_create_note_person_not_found_returns_404` | PASS |
| `test_create_note_returns_201` | PASS |
| `test_create_note_sets_author_to_request_user` | PASS |
| `test_list_notes_returns_200` | PASS |

### `PersonNoteInactivePersonTest` — 1 test

| Test | Status |
|---|---|
| `test_create_note_for_inactive_person_returns_404` | PASS |

### `PersonOrgRelationViewTest` — 9 tests

| Test | Status |
|---|---|
| `test_close_org_relation_not_found_returns_404` | PASS |
| `test_close_org_relation_returns_200` | PASS |
| `test_duplicate_link_returns_409` | PASS |
| `test_link_org_returns_201` | PASS |
| `test_link_person_not_found_returns_404` | PASS |
| `test_list_active_only_param` | PASS |
| `test_list_org_relations_returns_200` | PASS |
| `test_update_org_relation_not_found_returns_404` | PASS |
| `test_update_org_relation_returns_200` | PASS |

### `PersonAttachmentsViewTest` — 1 test

| Test | Status |
|---|---|
| `test_list_attachments_returns_200` | PASS |

### `CategoryViewTest` — 10 tests

| Test | Status |
|---|---|
| `test_create_category_admin` | PASS |
| `test_create_category_non_admin_returns_403` | PASS |
| `test_create_duplicate_category_returns_409` | PASS |
| `test_deactivate_category_admin` | PASS |
| `test_deactivate_category_not_found_returns_404` | PASS |
| `test_deactivate_system_category_returns_409` | PASS |
| `test_list_categories_authenticated` | PASS |
| `test_list_categories_unauthenticated_returns_401` | PASS |
| `test_list_filter_active` | PASS |
| `test_update_category_admin` | PASS |
| `test_update_system_category_name_returns_409` | PASS |

### `SubResourceAuthTest` — 8 tests

| Test | Status |
|---|---|
| `test_addresses_create_requires_auth` | PASS |
| `test_addresses_list_requires_auth` | PASS |
| `test_categories_list_requires_auth` | PASS |
| `test_deactivate_requires_auth` | PASS |
| `test_notes_create_requires_auth` | PASS |
| `test_notes_list_requires_auth` | PASS |
| `test_organizations_list_requires_auth` | PASS |
| `test_person_detail_requires_auth` | PASS |

---

## Notes

- All 302 tests passed with zero failures or errors.
- Tests run against a fresh in-memory SQLite database — no persistent state between runs.
- The `person_merge` endpoint intentionally returns `501 Not Implemented`; its test (`test_merge_returns_501`) validates this expected behavior.
- File upload for person attachments is deferred to phase 2; the view returns an empty list and has one passing smoke test.
- No test coverage tooling (`coverage.py`) was run in this report. Run `coverage run manage.py test && coverage report` for line-level coverage metrics.
