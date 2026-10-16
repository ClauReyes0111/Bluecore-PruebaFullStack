import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { CreditApplicationApiService } from './credit-application-api.service';

describe('CreditApplicationApiService', () => {
  let service: CreditApplicationApiService;
  let controller: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CreditApplicationApiService);
    controller = TestBed.inject(HttpTestingController);
  });

  afterEach(() => controller.verify());

  it('list envía status, limit y offset', () => {
    service.list('PENDING', 20, 0).subscribe();
    const req = controller.expectOne(
      '/api/v1/credit-applications?status=PENDING&limit=20&offset=0',
    );
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], total: 0, limit: 20, offset: 0 });
  });

  it('list omite status cuando es null', () => {
    service.list(null, 20, 40).subscribe();
    controller
      .expectOne('/api/v1/credit-applications?limit=20&offset=40')
      .flush({ items: [], total: 0, limit: 20, offset: 40 });
  });

  it('changeStatus usa PATCH sobre /status', () => {
    service.changeStatus('abc', { status: 'APPROVED', comment: 'Cumple requisitos' }).subscribe();
    const req = controller.expectOne('/api/v1/credit-applications/abc/status');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ status: 'APPROVED', comment: 'Cumple requisitos' });
    req.flush({});
  });
});
