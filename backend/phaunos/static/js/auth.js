$(document).ready(function() {
    $('#login').submit(function (e) {
        $.ajax({
            type: "POST",
            contentType: "application/json",
            dataType: "json",
            url: login_url,
            data: JSON.stringify(
                {"username": $('#login input[id=username]').val(),
                    "password": $('#login input[id=password]').val()}),
            success: function (data, textStatus, jqXHR) {
                location.reload();
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $('#error').text(jqXHR.responseJSON["messages"][0]);
            },
        });
        e.preventDefault(); // block the traditional submission of the form.
    });
    $('#logout').click(function (e) {
        $.ajax({
            type: "GET",
            url: logout_url,
            success: function (data, textStatus, jqXHR) {
                location.reload();
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $('#error').text(jqXHR.responseJSON["messages"][0]);
            },
        });
        e.preventDefault(); // block the traditional submission of the form.
    });
    // Inject our CSRF token into our AJAX request.
/*    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", "{{ form.csrf_token._value() }}")
            }
        }
    })
*/
});
