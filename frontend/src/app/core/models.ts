export type ApplicationStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface CreditApplication {
  id: string;
  applicant_document: string;
  amount: number;
  term_months: number;
  status: ApplicationStatus;
  decision_comment: string | null;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreditApplicationPage {
  items: CreditApplication[];
  total: number;
  limit: number;
  offset: number;
}

export interface NewCreditApplication {
  applicant_document: string;
  amount: number;
  term_months: number;
}

export interface StatusChange {
  status: 'APPROVED' | 'REJECTED';
  comment: string;
}

export interface ApiError {
  status: number;
  type: string;
  title: string;
  detail: string;
  fieldErrors: Record<string, string>;
}
