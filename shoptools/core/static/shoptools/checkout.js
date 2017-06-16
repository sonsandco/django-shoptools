import Sizzle from 'sizzle';
import Cookies from 'js-cookie';

export function checkoutForm (form) {
  const toggleFormSection = (formSection, show) => {
    formSection.classList[show ? 'add' : 'remove']('active');

    // need to remove required attr for hidden forms, or the browser won't let
    // it submit
    if (show) {
      // TODO
    } else {
      Sizzle('input, textarea, select', formSection).forEach((el) => {
        el.required = false;
      });
    }
  };

  Sizzle('.user-form', form).forEach((userForm) => {
    const userToggle = Sizzle('input[name="save_details"]', form)[0];
    const userChange = () => {
      const show = Sizzle.matchesSelector(userToggle, ':checked');
      toggleFormSection(userForm, show);
    };
    userToggle.addEventListener('change', userChange);
    userChange();
  });

  // const giftToggle = Sizzle('input[name="is_gift"]', form)[0];
  // const giftForm = Sizzle('.gift-form', form)[0];
  // const giftChange = () => {
  //   const show = Sizzle.matchesSelector(giftToggle, ':checked');
  //   toggleFormSection(giftForm, show);
  // };
  // giftToggle.addEventListener('change', giftChange);
  // giftChange();
}

export function cartInit (el) {
  el.querySelectorAll('form.quantity').forEach((form) => {
    const submit = () => {
      const url = form.getAttribute('action');
      const data = new window.FormData(form);
      const params = {
        credentials: 'include',
        method: 'post',
        body: data,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': Cookies.get('csrftoken')
          // 'Accept': 'application/json, text/plain, */*',
          // 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
      };
      window.fetch(url, params).then((response) => {
        return response.json();
      }).then((data) => {
        // el.innerHTML = data.html_snippet;
        // // TODO handle this better
        // // TODO show errors - this doesn't
        // cartInit(el);

        updateEls(el, data.html_snippet,
          ['.line-total', '.cart-shipping-cost', '.cart-total']);
      });
    };
    form.addEventListener('submit', (e) => {
      submit();
      e.preventDefault();
    });
    form.querySelector('input[type="number"]').addEventListener('change', submit);
    form.querySelector('input[type="number"]').addEventListener('keyup', submit);
  });
}

function updateEls (container, html, selectors) {
  /* Selectively update container to match new content in html, based on the
     provided selectors. selectors should be a list, i.e. ['h1', '.total']
  */

  var newContent = document.createElement('div');
  newContent.innerHTML = html;

  selectors.forEach((selector) => {
    container.querySelectorAll(selector).forEach((el, index) => {
      el.innerHTML = newContent.querySelectorAll(selector)[index].innerHTML;
    });
  });
}
