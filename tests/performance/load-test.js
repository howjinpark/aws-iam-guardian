import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 10 },  // 30초 동안 10명까지 증가
    { duration: '1m', target: 10 },   // 1분 동안 10명 유지
    { duration: '30s', target: 0 },   // 30초 동안 0명까지 감소
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95%의 요청이 500ms 이하
    http_req_failed: ['rate<0.1'],    // 실패율 10% 이하
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // 기본 헬스체크
  let response = http.get(`${BASE_URL}/`);
  check(response, {
    'status is 200': (r) => r.status === 200,
  });

  // API 문서 접근
  response = http.get(`${BASE_URL}/docs`);
  check(response, {
    'docs accessible': (r) => r.status === 200,
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    'performance-report.json': JSON.stringify(data, null, 2),
  };
}