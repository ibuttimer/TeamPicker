// place any jQuery/helper plugins in here, instead of separate, slower script files.

// https://flask-wtf.readthedocs.io/en/stable/csrf.html#setup
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        var csrf_token = $("input#csrf_token").val();
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    }
});

// datepicker related see https://www.npmjs.com/package/jquery-datetimepicker -->
jQuery.datetimepicker.setLocale('en');
jQuery('.dtpick').datetimepicker({
  format:'Y-m-d H:i'
});
jQuery('.tpick').datetimepicker({
  datepicker:false,
  format:'H:i'
});
jQuery('.dpick').datetimepicker({
  timepicker:false,
  format:'Y-m-d'
});

// book show related functions
function matchDate(queryDate) {
    var matchedDate = null;
    if (queryDate != null) {
        var match = queryDate.match(/(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})/);
        if (match) {
            matchedDate = match[1] + " " + match[2]
        }
    }
    return matchedDate;
}

function setClass(selector, className) {
    $(selector).attr("class", className)
}


// Delete match
$(function () {
    $("button[id^='delete-match-']").click(function (event) {
        // Extract info from data-bs-* attributes
        var del_href = $(this).attr('data-bs-del_href');
        var success_href = $(this).attr('data-bs-success_href');
        var start_time = $(this).attr('data-bs-start_time');
        var venue = $(this).attr('data-bs-venue');
        var opposition = $(this).attr('data-bs-opposition');

        // Set confirmation message
        $("p#confirm-delete-msg").html("Delete "+start_time+" "+venue+" match versus "+opposition+"?");

        // Add delete button click listener
        $("a#confirm-match-delete").click(function (event) {
            $.ajax({
                url: del_href,
                method: 'DELETE',
                contentType: false,
                success: function(result) {
                    window.location.replace(success_href);
                }
            });
        })
    })
});

// Toggle player selection
$(function () {
    $("button[id^='toggle-select-']").click(function (event) {
        // Extract info from data-bs-* attributes
        var href = $(this).attr('data-bs-href');
        var success_href = $(this).attr('data-bs-success_href');

        $.ajax({
            url: href,
            method: 'POST',
            contentType: false,
            success: function(result) {
                window.location.replace(success_href);
            }
        });
    })
});

// Player confirmation
$(function () {
    $("input[id^='toggle-confirm-']").click(function (event) {
        // Extract info from data-bs-* attributes
        var href = $(this).attr('data-bs-href');
        var success_href = $(this).attr('data-bs-success_href');

        // Extract end of id to send as query param to server.
        var query = $(this).attr('id').split('-')[2];

        $.ajax({
            url: href + '?select=' + query,
            method: 'POST',
            contentType: false,
            success: function(result) {
                window.location.replace(success_href);
            }
        });
    })
});

// Enable tooltips
$(function () {
    // https://getbootstrap.com/docs/5.0/components/tooltips/#example-enable-tooltips-everywhere
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
})});

