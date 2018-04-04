import $ from 'jquery';

const updaterRegistry = [];
const sessionKey = 'site-data';

export function registerUpdater (func) {
  /* Register an updater function which should run after fetching data. */

  updaterRegistry.push(func);
}

function updateCart (cart) {
  $('html')[cart.count ? 'addClass' : 'removeClass']('state-cart-has-items');
  $('html')[cart.count ? 'removeClass' : 'addClass']('state-cart-empty');
  $('.cart-item-count').text(cart.count || '');
  $('.cart-item-plural').text(parseInt(cart.count, 10) !== 1 ? 's' : '');
  $('.cart-snippet').html(cart.html_snippet || '');
  // $('.cart-subtotal').text(cart.subtotal);
  // $('.cart-total').text(cart.total);
  // $('.cart-gst').text((cart.total / 11).toFixed(2));
  // $('.cart-shipping').text(cart.shipping_cost);
}

export function globalUpdate (data) {
  // set site state based on data

  $('html')[data.account ? 'addClass' : 'removeClass']('state-logged-in');
  $('html')[data.account ? 'removeClass' : 'addClass']('state-anon');

  if (data.account) {
    $('.account-name').html(`${data.account.first_name} ${data.account.last_name}`);
  }

  if (data.regions && data.regions.region) {
    $('.regions-region-name').html(data.regions.region.name);
    $('.regions-region-currency').html(data.regions.region.currency_code);
  }

  if (data.cart) {
    updateCart(data.cart);
  }

  updaterRegistry.forEach((func) => {
    func(data);
  });
}

export function fetchData () {
  // TODO should just update based on the session data if it's there, but will
  // need to make sure it gets updated whenever globalUpdate is called - note
  // the data passed to globalUpdate may be incomplete, so the update needs to
  // be granular

  // for now, just run two updates - one on the session data and then another
  // once fresh data has been fetched

  const sessionData = JSON.parse(window.sessionStorage.getItem(sessionKey));

  function doUpdate (data) {
    globalUpdate(data);
    $('html').addClass('state-data-loaded');
  }

  if (sessionData) {
    doUpdate(sessionData);
  }
  $.get(window.URLS.get_data, function (data) {
    window.sessionStorage.setItem(sessionKey, JSON.stringify(data));
    doUpdate(data);
  });
}
