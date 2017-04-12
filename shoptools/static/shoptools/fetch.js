import Cookies from 'js-cookie';
import formurlencoded from 'form-urlencoded';

// function csrfSafeMethod (method) {
//   // these HTTP methods do not require CSRF protection
//   return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
// }

export function post (url, data) {
  if (typeof data === 'object') {
    data = formurlencoded(data);
  }

  const params = {
    credentials: 'include',
    method: 'post',
    body: data,
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': Cookies.get('csrftoken'),
      // 'Accept': 'application/json, text/plain, */*',
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
  };

  return window.fetch(url, params);
}

export function get (url) {
  const params = {
    method: 'get',
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  };

  return window.fetch(url, params);
}
