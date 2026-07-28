import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    baseline: {
      executor: "constant-arrival-rate",
      rate: 20,
      timeUnit: "1s",
      duration: "2m",
      preAllocatedVUs: 20,
      maxVUs: 80,
    },
    surge: {
      executor: "ramping-arrival-rate",
      startRate: 10,
      timeUnit: "1s",
      preAllocatedVUs: 30,
      maxVUs: 150,
      stages: [
        { target: 10, duration: "20s" },
        { target: 80, duration: "40s" },
        { target: 120, duration: "30s" },
        { target: 10, duration: "30s" },
      ],
      startTime: "2m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<750"],
    checks: ["rate>0.99"],
  },
};

const baseUrl = __ENV.ORDERS_URL || "http://localhost:8002";

export default function () {
  const payload = JSON.stringify({
    sku: "OBS-100",
    quantity: 1,
    payment_token: `demo-token-${__VU}-${__ITER}`,
  });
  const response = http.post(`${baseUrl}/orders`, payload, {
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": `k6-${__VU}-${__ITER}-${Date.now()}`,
    },
  });
  check(response, {
    "order accepted": (result) => result.status === 201 || result.status === 402,
    "request id returned": (result) => Boolean(result.headers["X-Request-Id"]),
  });
  sleep(0.1);
}
