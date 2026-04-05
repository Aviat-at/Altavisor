/**
 * api.ts — People module API layer.
 *
 * Thin wrappers around fetch() that attach the Bearer token from localStorage
 * and surface errors as thrown objects with { status, body } for callers to
 * handle (e.g. 409 duplicate detection, 400 validation, 404 not found).
 */
import type {
  ApiError,
  OrganizationPersonRelation,
  PaginatedPersons,
  PersonAddress,
  PersonCategory,
  PersonCategoryAssignment,
  PersonDetail,
  PersonNote,
} from "./types";

// ── Auth ──────────────────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api/people${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers ?? {}) },
  });

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => ({}));

  if (!res.ok) {
    const err: ApiError = { status: res.status, body };
    throw err;
  }

  return body as T;
}

// ── Persons ───────────────────────────────────────────────────────────────────

export function listPersons(params: {
  search?: string;
  category_id?: number;
  is_active?: boolean;
  page?: number;
  page_size?: number;
} = {}): Promise<PaginatedPersons> {
  const qs = new URLSearchParams();
  if (params.search)                qs.set("search",      params.search);
  if (params.category_id)           qs.set("category_id", String(params.category_id));
  if (params.is_active !== undefined) qs.set("is_active",  String(params.is_active));
  if (params.page)                  qs.set("page",        String(params.page));
  if (params.page_size)             qs.set("page_size",   String(params.page_size));
  return request<PaginatedPersons>(`/persons/?${qs}`);
}

export function getPerson(id: number): Promise<PersonDetail> {
  return request<PersonDetail>(`/persons/${id}/`);
}

export function createPerson(data: Record<string, unknown>): Promise<PersonDetail> {
  return request<PersonDetail>("/persons/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updatePerson(
  id: number,
  data: Record<string, unknown>,
): Promise<PersonDetail> {
  return request<PersonDetail>(`/persons/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deactivatePerson(id: number): Promise<{ detail: string }> {
  return request<{ detail: string }>(`/persons/${id}/deactivate/`, {
    method: "POST",
  });
}

// ── Categories ────────────────────────────────────────────────────────────────

export function listCategories(params: { is_active?: boolean } = {}): Promise<PersonCategory[]> {
  const qs = new URLSearchParams();
  if (params.is_active !== undefined) qs.set("is_active", String(params.is_active));
  return request<PersonCategory[]>(`/categories/?${qs}`);
}

export function createCategory(data: {
  name: string;
  description?: string;
}): Promise<PersonCategory> {
  return request<PersonCategory>("/categories/create/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateCategory(
  id: number,
  data: { name?: string; description?: string },
): Promise<PersonCategory> {
  return request<PersonCategory>(`/categories/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deactivateCategory(id: number): Promise<{ detail: string }> {
  return request<{ detail: string }>(`/categories/${id}/deactivate/`, {
    method: "POST",
  });
}

// ── Person → Categories ───────────────────────────────────────────────────────

export function getPersonCategories(personId: number): Promise<PersonCategoryAssignment[]> {
  return request<PersonCategoryAssignment[]>(`/persons/${personId}/categories/`);
}

export function assignCategory(
  personId: number,
  categoryId: number,
): Promise<PersonCategoryAssignment> {
  return request<PersonCategoryAssignment>(`/persons/${personId}/categories/`, {
    method: "POST",
    body: JSON.stringify({ category_id: categoryId }),
  });
}

export function removeCategory(personId: number, categoryId: number): Promise<void> {
  return request<void>(`/persons/${personId}/categories/${categoryId}/`, {
    method: "DELETE",
  });
}

// ── Person → Addresses ────────────────────────────────────────────────────────

export function getPersonAddresses(personId: number): Promise<PersonAddress[]> {
  return request<PersonAddress[]>(`/persons/${personId}/addresses/`);
}

export function createAddress(
  personId: number,
  data: Record<string, unknown>,
): Promise<PersonAddress> {
  return request<PersonAddress>(`/persons/${personId}/addresses/`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateAddress(
  personId: number,
  addressId: number,
  data: Record<string, unknown>,
): Promise<PersonAddress> {
  return request<PersonAddress>(`/persons/${personId}/addresses/${addressId}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// ── Person → Notes ────────────────────────────────────────────────────────────

export function getPersonNotes(personId: number): Promise<PersonNote[]> {
  return request<PersonNote[]>(`/persons/${personId}/notes/`);
}

export function createNote(personId: number, body: string): Promise<PersonNote> {
  return request<PersonNote>(`/persons/${personId}/notes/`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

// ── Person → Organizations ────────────────────────────────────────────────────

export function getPersonOrganizations(
  personId: number,
  active_only?: boolean,
): Promise<OrganizationPersonRelation[]> {
  const qs = active_only !== undefined ? `?active_only=${active_only}` : "";
  return request<OrganizationPersonRelation[]>(`/persons/${personId}/organizations/${qs}`);
}

export function linkOrganization(
  personId: number,
  data: Record<string, unknown>,
): Promise<OrganizationPersonRelation> {
  return request<OrganizationPersonRelation>(`/persons/${personId}/organizations/`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateOrgRelation(
  personId: number,
  relId: number,
  data: Record<string, unknown>,
): Promise<OrganizationPersonRelation> {
  return request<OrganizationPersonRelation>(
    `/persons/${personId}/organizations/${relId}/`,
    { method: "PATCH", body: JSON.stringify(data) },
  );
}

export function closeOrgRelation(
  personId: number,
  relId: number,
): Promise<{ detail: string }> {
  return request<{ detail: string }>(
    `/persons/${personId}/organizations/${relId}/close/`,
    { method: "POST" },
  );
}
