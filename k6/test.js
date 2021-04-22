import http from 'k6/http';
import { sleep,check } from 'k6';
export default function () {
  let res=http.get('http://ac703b052f4994089b2d0f64c7107fa1-555553250.us-west-2.elb.amazonaws.com/doc');
  check(res,{
      'status 200':r=>r.status==200
  })
  sleep(1);
}