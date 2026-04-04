/**
 * types.ts — TypeScript interfaces matching backend serializer response shapes.
 *
 * Field names mirror the Django serializer fields exactly so that API
 * responses can be typed without transformation.
 */

export interface PersonCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  is_system: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PersonCategoryAssignment {
  id: number;
  category: PersonCategory;
  assigned_by_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PersonAddress {
  id: number;
  label: string;
  label_display: string;
  line1: string;
  line2: string;
  city: string;
  state_province: string;
  postal_code: string;
  country: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PersonNote {
  id: number;
  body: string;
  author_name: string | null;
  created_at: string;
}

export interface PersonAttachment {
  id: number;
  label: string;
  file: string;
  uploaded_by_name: string | null;
  created_at: string;
}

export interface OrganizationPersonRelation {
  id: number;
  person_id: number;
  organization_id: number;
  organization_type: string;
  role: string;
  is_primary: boolean;
  is_active: boolean;
  started_on: string | null;
  ended_on: string | null;
  created_at: string;
  updated_at: string;
}

/** Shape returned by GET /persons/ list endpoint (PersonListSerializer) */
export interface PersonListItem {
  id: number;
  full_name: string;
  display_name: string;
  email: string | null;
  phone: string;
  is_active: boolean;
  primary_category: string | null;
  created_at: string;
}

/** Shape returned by GET /persons/:id/ detail endpoint (PersonDetailSerializer) */
export interface PersonDetail {
  id: number;
  full_name: string;
  display_name: string;
  initials: string;
  first_name: string;
  last_name: string;
  preferred_name: string;
  email: string | null;
  phone: string;
  mobile: string;
  date_of_birth: string | null;
  gender: string;
  gender_display: string;
  is_active: boolean;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
  addresses: PersonAddress[];
  category_assignments: PersonCategoryAssignment[];
  org_relations: OrganizationPersonRelation[];
  notes: PersonNote[];
  attachments: PersonAttachment[];
}

export interface PaginatedPersons {
  results: PersonListItem[];
  count: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface DuplicateCandidate {
  id: number;
  full_name: string;
  email: string | null;
  phone: string;
}

export interface ApiError {
  status: number;
  body: {
    detail?: string;
    code?: string;
    candidates?: DuplicateCandidate[];
    [key: string]: unknown;
  };
}
