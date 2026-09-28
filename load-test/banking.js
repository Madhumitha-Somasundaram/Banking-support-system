import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

const BASE_URL = 'https://api.payanams.xyz';
const EMAIL = __ENV.TEST_EMAIL;
const PASSWORD = __ENV.TEST_PASSWORD;

// Final end-to-end metric:
// message submitted -> final answer available
const endToEndResponseTime = new Trend('end_to_end_response_time', true);

const successRate = new Rate('question_success_rate');

const questionsCompleted = new Counter('questions_completed');
const questionsFailed = new Counter('questions_failed');

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '2m',

  summaryTrendStats: [
    'avg',
    'min',
    'med',
    'max',
    'p(90)',
    'p(95)',
    'p(99)',
  ],
};

export function setup() {
  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({
      email: EMAIL,
      password: PASSWORD,
    }),
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  check(loginRes, {
    'login successful': (r) => r.status === 200,
  });

  if (loginRes.status !== 200) {
    throw new Error(`Login failed: ${loginRes.status}`);
  }

  return {
    token: loginRes.json('access_token'),
  };
}

export default function (data) {
  const token = data.token;

  const authHeaders = {
    Authorization: `Bearer ${token}`,
  };

  // --------------------------------------------------
  // 1. Create conversation
  // --------------------------------------------------

  const conversationRes = http.post(
    `${BASE_URL}/api/chat/conversations`,
    null,
    {
      headers: authHeaders,
    }
  );

  const conversationOk = check(conversationRes, {
    'conversation created': (r) =>
      r.status === 200 || r.status === 201,
  });

  if (!conversationOk) {
    questionsFailed.add(1);
    successRate.add(false);
    return;
  }

  const conversationId = conversationRes.json('id');

  // --------------------------------------------------
  // 2. Submit banking question
  // --------------------------------------------------

  const startTime = Date.now();

  const messageRes = http.post(
    `${BASE_URL}/api/chat/conversations/${conversationId}/messages`,
    JSON.stringify({
      content: 'What is my account balance?',
    }),
    {
      headers: {
        ...authHeaders,
        'Content-Type': 'application/json',
      },
    }
  );

  const messageOk = check(messageRes, {
    'message accepted': (r) => r.status === 202,
    'job id returned': (r) => !!r.json('job_id'),
  });

  if (!messageOk) {
    questionsFailed.add(1);
    successRate.add(false);
    return;
  }

  const jobId = messageRes.json('job_id');

  // --------------------------------------------------
  // 3. Wait for final answer
  // --------------------------------------------------

  let finalStatus = null;

  // 90 seconds maximum observation time
  const maxAttempts = 90;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const jobRes = http.get(
      `${BASE_URL}/api/chat/jobs/${jobId}`,
      {
        headers: authHeaders,
      }
    );

    if (jobRes.status === 200) {
      finalStatus = jobRes.json('status');

      if (
        finalStatus === 'COMPLETED' ||
        finalStatus === 'APPROVAL_REQUIRED' ||
        finalStatus === 'FAILED'
      ) {
        break;
      }
    }

    sleep(1);
  }

  // --------------------------------------------------
  // 4. Record complete user-facing latency
  // --------------------------------------------------

  const endToEndTime = Date.now() - startTime;

  if (finalStatus === 'COMPLETED') {
    endToEndResponseTime.add(endToEndTime);

    questionsCompleted.add(1);
    successRate.add(true);

    check(null, {
      'question completed': () => true,
    });
  } else {
    questionsFailed.add(1);
    successRate.add(false);

    check(null, {
      'question completed': () => false,
    });
  }

  // Small pause before next user action
  sleep(1);
}