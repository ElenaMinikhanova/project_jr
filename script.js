$( window ).on( "load", function() {
    let active = "tab1";

    $(`#${active}`).addClass("active")
    $(`#page_${active}`).addClass("show")

    $(".tab").click(function(e) {
        $(".page").removeClass("show")
        $(".tab").removeClass("active")
        active = e.target.id
        $(`#${active}`).addClass("active")
        $(`#page_${active}`).addClass("show")
    })
} );