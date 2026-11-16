import http from 'k6/http';

import { check, sleep } from 'k6';


const BASE_URL = __ENV.BASE_URL ||
    'http://localhost:8080';

const ITERATIONS = __ENV.WORK_ITERATIONS ||
    '1200000';


export const options = {

    scenarios: {

        ramp_users: {

            executor: 'ramping-vus',

            startVUs: 0,

            stages: [

                {
                    duration: '30s',
                    target: 5
                },

                {
                    duration: '60s',
                    target: 15
                },

                {
                    duration: '90s',
                    target: 30
                },

                {
                    duration: '30s',
                    target: 0
                }

            ],

            gracefulRampDown: '15s'

        }

    },

    thresholds: {

        http_req_failed: [
            'rate<0.02'
        ],

        http_req_duration: [
            'p(95)<5000'
        ]

    }

};


export default function () {

    const response = http.get(

        `${BASE_URL}/api/work?iterations=${ITERATIONS}`,

        {
            tags: {
                endpoint: 'cpu_work'
            },

            timeout: '30s'
        }

    );


    check(response, {

        'HTTP 200': (r) => r.status === 200,

        'Backend hostname returned': (r) =>
            !!r.json('hostname')

    });


    sleep(0.1);

}