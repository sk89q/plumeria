$(".doc-nav-menu").on("click", function (event) {
    $("body").toggleClass("sidebar-open");
});
$(".doc-nav").on("click", "a", function (event) {
    $("body").removeClass("sidebar-open");
    if (this.getAttribute("href").match(/^#/)) {
        var target = $(this.getAttribute("href"));
        if (target.length > 0) {
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 200);
            event.preventDefault();
        }
    }
});
