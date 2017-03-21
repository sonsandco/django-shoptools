import $ from 'jquery';

function updateCart (cart) {
  $('body')[cart.count ? 'addClass' : 'removeClass']('cart-has-items');
  $('.cart-item-count').text(cart.count || '');
  // $('.cart-subtotal').text(cart.subtotal);
  // $('.cart-total').text(cart.total);
  // $('.cart-gst').text((cart.total / 11).toFixed(2));
  // $('.cart-shipping').text(cart.shipping_cost);
}

export function globalUpdate (data) {
  $('html')[data.account ? 'addClass' : 'removeClass']('state-logged-in');
  $('html')[data.account ? 'removeClass' : 'addClass']('state-anon');

  if (data.account) {
    $('.account-name').html(`${data.account.first_name} ${data.account.last_name}`);
  }

  if (data.regions && data.regions.region) {
    $('.regions-region-name').html(data.regions.region.name);
    $('.regions-region-currency').html(data.regions.region.currency);
  }

  if (data.cart) {
    updateCart(data.cart);
  }
}

export function fetchData () {
  $.get(window.URLS.get_data, function (data) {
    globalUpdate(data);
    $('html').addClass('state-data-loaded');
  });
}
