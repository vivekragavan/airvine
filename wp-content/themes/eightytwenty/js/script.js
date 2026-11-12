var eightytwenty = eightytwenty || {};
jQuery(function($){
    // scroll to top-link
    $('.top-link').click(function(e){
        e.preventDefault();
        $('html,body').animate({scrollTop: 0}, 'slow');
    });
    // videos
    // see https://css-tricks.com/NetMag/FluidWidthVideo/Article-FluidWidthVideo.php
    eightytwenty.discoverVideos = function() {
        $("iframe[src*='player.vimeo.com'], iframe[src*='youtube.com/embed'], .video-iframe").not('.wrapper-added').each(function(){
            $(this).addClass('wrapper-added');
            $(this).wrap( "<div class='video-wrapper'></div>" );
        });
    }
    // createVideoWrappers()
    eightytwenty.discoverVideos();
    // popups
    // automatically create modal triggers
    eightytwenty.discoverModals = function() {
        $('.modal').each(function(){
            var popup_id = this.id;
            // anchor modals to body, when creating modals in VC, HTML tends to get deeply nested
            $(this).not('modal-anchored').addClass('modal-anchored').appendTo('body');
            // fixed missing # and adds trigger class
            $('a[href="#' + this.id + '"], a[href="' + this.id + '"]')
                .attr('href', '#' + this.id)
                .removeClass('modal-trigger')
                .addClass('modal-trigger');
        });
    }
    // autoCreateModalTriggers()
    eightytwenty.discoverModals();
    $(document).on('click', '.modal-trigger', function(e){
        e.preventDefault();
        var href = $(this).attr('href');
        $(href).modal('toggle');
    });
    // bootstrap modal, stop youtube/vimeo/iframe video playing after close
    $(document).on('hidden.bs.modal', '.modal', function(e) {
        $('iframe', this).attr('src', $('iframe', this).attr('src'));
    });
    /*
    // bootstrap modal, multi-layer support
    $(document).on('hidden.bs.modal', '.modal', function(e) {
        $('.modal:visible').length && $('body').addClass('modal-open');
    });
    $(document).on('show.bs.modal', '.modal', function(e) {
        var zIndex = $(this).css('z-index') + (10 * $('.modal:visible').length);
        $(this).css('z-index', zIndex);
        setTimeout(function() {
            $('.modal-backdrop').not('.modal-stack').addClass('modal-stack').css('z-index', zIndex - 1);
        }, 0);
    });*/
    // bootstrap modal, multi-layer support
    var open_modals = [];
    $(document).on('hidden.bs.modal', '.modal', function(e) {
        var m = open_modals.pop()
        $(m.modal).removeClass('modal-stack').css('z-index', m.z_index);
        // fixes issues with scrolling
        $('.modal:visible').length && $('body').addClass('modal-open');
    });
    $(document).on( 'shown.bs.modal', '.modal', function(e) {
        if ($(this).hasClass('modal-stack')) {
            return;
        }
        open_modals.push({
            modal: $(this).addClass('modal-stack'),
            z_index: $(this).css('z-index'),
            backdrop: $('.modal-backdrop').not('.modal-stack').addClass('modal-stack')
        });
        for(var i=0; i<open_modals.length; i++) {
            var m = open_modals[i];
            var z = $(m.modal).css('z-index');
            $(m.modal).css('z-index', z - 10);
            $(m.backdrop).css('z-index', z - 20);
        }
    });
});
jQuery(function($){
    // check if sub-menu is off-screen, add class if so
    var lastSubMenu = $('.sub-menu-container', '.menu-primary-container').last();
    if (lastSubMenu.length) {
        function flagLastSubMenuIfOffScreen() {
            var offset = lastSubMenu.closest('.menu-item').offset();
            var subMenuRightEdge = offset.left + lastSubMenu.width();
            if (subMenuRightEdge > $(window).width()) {
                lastSubMenu.addClass('off-screen');
            } else {
                lastSubMenu.removeClass('off-screen');
            }
        }
        $(window).on('resize', _.throttle(flagLastSubMenuIfOffScreen, 500));
        flagLastSubMenuIfOffScreen();
    }
});


/**
 * Slider setup. Using Cycle2 jQuery plugin.
 *
 * @see http://jquery.malsup.com/cycle2/api/
 */
(function($) {
    // disable cycle log messages
    $.fn.cycle.log = $.noop;
    $('.entry-header.page-banner > .slider').cycle();
})(jQuery);
