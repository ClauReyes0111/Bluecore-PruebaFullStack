import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  ApplicationStatus,
  CreditApplication,
  CreditApplicationPage,
  NewCreditApplication,
  StatusChange,
} from './models';

const BASE_URL = '/api/v1/credit-applications';

@Injectable({ providedIn: 'root' })
export class CreditApplicationApiService {
  private readonly http = inject(HttpClient);

  list(
    status: ApplicationStatus | null,
    limit: number,
    offset: number,
  ): Observable<CreditApplicationPage> {
    let params = new HttpParams();
    if (status !== null) {
      params = params.set('status', status);
    }
    params = params.set('limit', limit).set('offset', offset);
    return this.http.get<CreditApplicationPage>(BASE_URL, { params });
  }

  create(body: NewCreditApplication): Observable<CreditApplication> {
    return this.http.post<CreditApplication>(BASE_URL, body);
  }

  changeStatus(id: string, body: StatusChange): Observable<CreditApplication> {
    return this.http.patch<CreditApplication>(`${BASE_URL}/${id}/status`, body);
  }
}
