"use strict";

jQuery(function ($) {
  'use strict'; // 1. preloader

  $(window).ready(function () {
    $('#preloader').delay(200).fadeOut('fade');
  }); // 2. page scrolling feature - requires jQuery Easing plugin

  if ($('.scroll-to-target').length) {
    $(".scroll-to-target").on('click', function () {
      let target = $(this).attr('data-target'); // animate

      $('html, body').animate({
        scrollTop: $(target).offset().top
      }, 500);
    });
  } // 5. counter up js

}); // JQuery end

$(document).ready(function () {

  $(".form").on('submit', function (e) {
    e.preventDefault();

    const form = $(this);

    validateQuoteAttachment(form);

    // Sanitize all input fields before validation
    sanitizeForm(form);

    if (form[0].checkValidity() === false) {
      e.stopPropagation()
    } else {
      let formData = new FormData(this);
      formSubmit(form, formData);
    }

    form.addClass('was-validated');
  });

  $("form[name='formOrcamento'] input[name='anexo']").on('change', function () {
    validateQuoteAttachment($(this.form));
  });

  $('.formExam').validator({
    disable: false,
    focus: false
  }).on('submit', function (e) {
    if (!e.isDefaultPrevented()) {
      let descricao = $(this).find('input[name=descricao]').val();
      listaExames(descricao);
      return false;
    }
  });

  $('.formExam2').validator({
    disable: false,
    focus: false
  }).on('submit', function (e) {
    if (!e.isDefaultPrevented()) {
      let descricao = $(this).find('input[name=descricao]').val();
      window.location.href = "/exames/pesquisa/" + descricao;
      return false;
    }
  });

  $('.formExamExclusivos').validator({
    disable: false,
    focus: false
  }).on('submit', function (e) {
    if (!e.isDefaultPrevented()) {
      let descricao = $(this).find('input[name=descricao]').val();
      listaExamesExclusivos(descricao);
      return false;
    }
  });

  $('.btn-letra').click(function() {
    let letra = $(this).html();
    listaExames('', letra);
  });

  $('.btnHistoryBack').click(function() {
    history.back();
  });

  $('.btn-letra-exclusivos').click(function() {
    let letra = $(this).html();
    listaExamesExclusivos('', letra);
  });

  $(document).on('click', '.btn-exame',function() {
    let exame = $(this).data('exame');
    let material = $(this).data('material');
    let target = $(this).data('target');
    let id = '#' + $(this).attr('id');
    detalhesExames(exame, material, target, id);
  });

  $(document).on('click', '.btn-exame-exclusivo',function() {
    let id = '#' + $(this).attr('id');

    setTimeout(function() {
      $('html, body').animate({
        scrollTop: $(id).offset().top
      }, 300);
    }, 300);

  });

  $(document).on('click', '.btn-collapse-exame',function() {
    $(this).toggleClass('btn-exame');
    $(this).find('i').toggleClass('fa fa-chevron-down');
    $(this).find('i').toggleClass('fa fa-chevron-up');
  });

  $(document).on('click', '.btn-collapse-exame-exclusivo',function() {
    $(this).toggleClass('btn-exame-exclusivo');
    $(this).find('i').toggleClass('fa fa-chevron-down');
    $(this).find('i').toggleClass('fa fa-chevron-up');
  });

  $(document).on('click', '.btn-collapse-duvida',function() {
    $(this).find('i').toggleClass('fa fa-chevron-down');
    $(this).find('i').toggleClass('fa fa-chevron-up');
  });

  $('.owl-banner').owlCarousel({
    loop: true,
    margin: 0,
    nav: false,
    autoplay: true,
    responsive:{
      0: {
        items: 1
      }
    }
  });

  $('.owl-logo').owlCarousel({
    loop: true,
    margin: 20,
    nav: true,
    dots: true,
    autoplay: false,
    responsive:{
      0: {
        items: 2
      },
      600: {
        items: 4
      },
      1000: {
        items: 5
      }
    }
  });

  $('.owl-photo').owlCarousel({
    loop: true,
    margin: 20,
    nav: false,
    dots: false,
    autoplay: true,
    autoplayHoverPause: false,
    slideTransition: 'linear',
    smartSpeed: 6000,
    autoplaySpeed: 6000,
    responsive: {
      0: { items: 2 },
      600: { items: 4 },
      1000: { items: 5 }
    }
  });

  $('.owl-photo').trigger('play.owl.autoplay', [1]);


  $('[data-toggle="popover"]').popover({
    trigger: 'hover'
  });

  $(".btn-emoji").on('click', function () {
    $(this).parent().parent().find('.btn-emoji').removeClass('checked');
    $(this).parent().find('input[type=radio]').prop("checked", true);
    $(this).addClass('checked');
  });


  setTimeout(function() {
    $('#modalPesquisa').modal();
  }, 300);

});

function validateQuoteAttachment(form) {
  if (form.attr('name') !== 'formOrcamento') return;

  const input = form.find("input[name='anexo']")[0];
  const file = input && input.files ? input.files[0] : null;

  if (!input) return;

  input.setCustomValidity(file && file.size > 10 * 1024 * 1024
    ? 'O arquivo excede o limite permitido de 10MB.'
    : '');
}

function formSubmit(form, formData) {

  let submitButton = form.find('button[type=submit]');

  $.ajax({
    method: "POST",
    url: "/_src/components/" + form.attr('name') + ".php",
    data: formData,
    processData: false,
    contentType: false,
    dataType: "json",
    beforeSend: function () {
      submitButton.prop('disabled', true);
      submitButton.find('.submit-content').toggleClass('d-none');
      form.find('.alert-danger, .alert-success').addClass('d-none');
    },
    success: function (response) {
      if(response.status === 'sucesso') {
        let urlResponse = null;
        let url = window.location.href;
        if (url[url.length - 1] === '/') {
          urlResponse = url + "obrigado";
        } else {
          urlResponse = url + "/obrigado";
        }
        window.location.href = urlResponse;
      } else {
        submitButton.prop('disabled', false);
        submitButton.find('.submit-content').toggleClass('d-none');
        form.find(".alert-danger").removeClass("d-none").text(response.mensagem);
      }
    },
    error: function () {
      submitButton.prop('disabled', false);
      submitButton.find('.submit-content').toggleClass('d-none');
      form.find(".alert-danger").removeClass("d-none").text("Ocorreu um erro inesperado. Tente novamente.");
    }
  });

}

function sanitizeForm(form) {
  form.find('input[type="text"], input[type="email"], textarea').each(function () {
    const field = $(this);
    let sanitizedValue = field.val();

    if (field.attr("name") === "empresaCnpj") {
      sanitizedValue = sanitizedValue.replace(/[^a-zA-Z0-9\sáàâãéèêíïóôõöúçñÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ.,\-@()\/]+/g, '');
    } else if (field.attr("name") === "responsavelDataNascimento") {
      sanitizedValue = sanitizedValue.replace(/[^0-9\/]+/g, '');
    } else if (field.attr("name") === "event") {
      sanitizedValue = sanitizedValue.replace(/[^A-Za-z_]+/g, '');
    } else {
      sanitizedValue = sanitizeInput(sanitizedValue);
    }

    const escapedValue = escapeHTML(sanitizedValue);
    field.val(escapedValue);
  });
}

function sanitizeInput(value) {
  return value.replace(/[^a-zA-Z0-9\sáàâãéèêíïóôõöúçñÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ.,\-@()]+/g, '');
}

function escapeHTML(value) {
  var element = document.createElement('div');
  if (value) {
    element.innerText = value;
    element.textContent = value;
  }
  return element.innerHTML;
}

function listaExames(descricao, letra) {

  let target = $('#exams');
  $.get("/_src/components/v1/inc/ajax/exames.php", {
    descricao: descricao,
    letra: letra
  }, function(data, status){
    target.html(data);
    $('html, body').animate({
      scrollTop: target.offset().top -30
    }, 300);
  });

}

function listaExamesExclusivos(descricao, letra) {

  let target = $('#exams');
  $.get("/_src/components/v1/inc/ajax/exames_exclusivos.php", {
    descricao: descricao,
    letra: letra
  }, function(data, status){
    target.html(data);
    $('html, body').animate({
      scrollTop: target.offset().top -30
    }, 300);
  });

}

function detalhesExames(exame, material, target, id) {

  $.get("/_src/components/v1/inc/ajax/exames.php", {
    exame: exame,
    material: material
  }, function(data, status){
    $('#exams').find(target).html(data);
    setTimeout(function() {
      $('html, body').animate({
        scrollTop: $(id).offset().top
      }, 300);
    }, 300);
  });

}

function resizeVideo(plataforma, componente) {
  if (plataforma == 'youtube') {
    let container = $(componente);
    let videoDimensions = container.data('proporcao').split('x');
    let videoHeight = container.width() / videoDimensions[0] * videoDimensions[1];
    container.find('iframe').prop('height', videoHeight.toFixed());
  }
}

(function ($) {
  var resizeTimer;

  function setupMarquee() {
    var $marquee = $('#marqueeLogos');
    if (!$marquee.length) return;

    var $track = $marquee.find('.marquee-track');
    var $originalSet = $marquee.find('.marquee-set').first();

    if (!$track.length || !$originalSet.length) return;

    $track.css('animation', 'none');
    $track.find('.marquee-set.clone').remove();

    var marqueeWidth = $marquee.outerWidth();
    var setWidth = $originalSet.get(0).scrollWidth;

    if (!setWidth) return;

    var totalWidth = setWidth;

    while (totalWidth < marqueeWidth + setWidth) {
      var $clone = $originalSet.clone();
      $clone.addClass('clone');
      $track.append($clone);
      totalWidth += setWidth;
    }

    var speed = 80;
    var duration = setWidth / speed;

    var $styleTag = $('#marquee-dynamic-style');
    if (!$styleTag.length) {
      $styleTag = $('<style id="marquee-dynamic-style"></style>');
      $('head').append($styleTag);
    }

    $styleTag.html(
        '@keyframes marqueeScroll {' +
        'from { transform: translateX(0); }' +
        'to { transform: translateX(-' + setWidth + 'px); }' +
        '}'
    );

    $track.css('animation', 'marqueeScroll ' + duration + 's linear infinite');
  }

  $(window).on('load', setupMarquee);

  $(window).on('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(setupMarquee, 150);
  });
})(jQuery);
