import http from 'k6/http'
import {check, sleep, group} from 'k6'
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';
const BASE_URL = 'http://127.0.0.1:8000'

const test_urls = [
    "https://google.com",
    "https://youtube.com",
    "https://facebook.com",
    "https://instagram.com",
    "https://x.com",
    "https://stackoverflow.com",
    "https://github.com",
]

export function handleSummary(data) {
    // Formats aggregate metrics for easier readability
    return {
        stdout: textSummary(data, { indent: ' ', enableColors: true }),
    };
}

export const options = {
    // Load Test: 20 VUs, 10s duration
    vus: 20,
    duration: '10s',
};

export default function() {
    /**
     * Load tests the URL shortener API via three sequential operations
     * 1. POST /shorten - Shorten URL
     * 2. GET /api/urls/{code} - Retrieves URL metadata
     * 3. GET /redirect - Tests redirects
     *
     * Metrics Tracked
     * - Success Rates (200/307 status codes)
     * - Latency Distribution
     * - Error Rates
     */
    let shortenUrl, shortCode;
    group('Shorten URL', () => {
        shortenUrl = http.post(`${BASE_URL}/shorten`,
            JSON.stringify({
                url: test_urls[Math.floor(Math.random() * test_urls.length)]
            }), {
                headers: { 'Content-Type': 'application/json' }
            })

        check(shortenUrl, {
            'Status Code = 200': (r) => r.status === 200,
        })
    })

    group('Get URL Metadata', () =>
    {
        shortCode = shortenUrl.json('short_code')

        const urlMetadata = http.get(`${BASE_URL}/api/urls/${shortCode}`)

        check(urlMetadata, {
            "Status Code = 200": (r) => r.status === 200
        })
    })

    group('Redirect', () => {
        const redirectRes = http.get(`${BASE_URL}/${shortCode}`, {
            redirects: 0
        })

        check(redirectRes, {
            'Redirect Status Code = 307': (r) => r.status === 307
        })
    })
    sleep(0.05)
}