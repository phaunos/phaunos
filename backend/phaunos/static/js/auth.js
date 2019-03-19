$(document).ready(function() {
    $('#login').submit(function (e) {
        $.ajax({
            type: "POST",
            contentType: "application/json",
            dataType: "json",
            url: login_url,
            data: JSON.stringify(
                {"username": $('#login input[name=username]').val(),
                    "password": $('#login input[name=password]').val()}),
            success: function (data, textStatus, jqXHR) {
                console.log(data["messages"]);  // display the returned data in the console.
                $('#error').text(data["username"]);
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
