import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '1m',
};

export default function () {
  const res = http.get('https://api.payanams.xyz/api/health');

  check(res, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);
}