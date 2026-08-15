import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const base = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const res = http.get(`${base}/health`);
  check(res, {
    'health is 200': (r) => r.status === 200,
    'health is ok': (r) => r.json('status') === 'ok',
    'security header present': (r) => r.headers['X-Content-Type-Options'] === 'nosniff',
  });
  sleep(1);
}
